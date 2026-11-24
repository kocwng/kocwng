#!/usr/bin/env python3
"""Re-render assets/banana.png, the banana mascot used by tools/video.py.

    python3 tools/banana.py [assets/banana.png]

Takes the banana-with-ukulele group out of assets/hero.svg (the <g> around class="sq"),
renders it with headless Google Chrome / Chromium at 2x, animations off, on a transparent
background, and crops the result to the banana. Needs Chrome and Pillow.

You only need this after changing how the banana looks in tools/hero.py: the PNG is
committed, so making the video does not need Chrome.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tapecfg import ROOT  # noqa: E402

SCALE = 2
CHROMES = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome',
]


def find_chrome():
    for c in CHROMES:
        p = c if os.path.isabs(c) else shutil.which(c)
        if p and os.path.exists(p):
            return p
    sys.exit('banana.py: Google Chrome or Chromium not found')


def banana_svg(hero):
    """Standalone SVG: hero's <style> + <defs> + the banana group, same 900x300 viewBox."""
    head = re.match(r'<svg[^>]*>', hero).group(0)
    style = re.search(r'<style>.*?</style>', hero, re.S).group(0)
    defs = re.search(r'<defs>.*?</defs>', hero, re.S).group(0)
    sq = hero.find('<g class="sq">')
    if sq < 0:
        sys.exit('banana.py: no <g class="sq"> (the banana) in hero.svg')
    start = hero.rfind('<g', 0, sq)          # the positioning <g transform=...> around it
    depth, i = 0, start
    for m in re.finditer(r'<g[\s>]|</g>', hero[start:]):
        depth += -1 if m.group(0) == '</g>' else 1
        if depth == 0:
            i = start + m.end()
            break
    group = hero[start:i]
    off = '<style>*{animation:none!important}</style>'
    return f'{head}{style}{off}{defs}{group}</svg>'


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'assets', 'banana.png')
    with open(os.path.join(ROOT, 'assets', 'hero.svg'), encoding='utf-8') as f:
        svg = banana_svg(f.read())
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, 'banana.html')
        shot = os.path.join(tmp, 'shot.png')
        with open(page, 'w', encoding='utf-8') as f:
            f.write('<!doctype html><html><body style="margin:0;background:transparent">'
                    f'<div style="width:900px;height:300px">{svg}</div></body></html>')
        subprocess.run([find_chrome(), '--headless=new', '--disable-gpu', '--hide-scrollbars',
                        f'--user-data-dir={os.path.join(tmp, "profile")}',
                        '--default-background-color=00000000', f'--force-device-scale-factor={SCALE}',
                        '--window-size=900,300', f'--screenshot={shot}', 'file://' + page],
                       check=True, capture_output=True, timeout=120)
        im = Image.open(shot).convert('RGBA')
    box = im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
    if not box:
        sys.exit('banana.py: the render came out empty')
    pad = 4 * SCALE
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad))
    im = im.crop(box)
    im.save(out, optimize=True)
    print(out, im.size, os.path.getsize(out), 'bytes')


if __name__ == '__main__':
    main()
