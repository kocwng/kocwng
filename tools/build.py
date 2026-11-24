#!/usr/bin/env python3
"""Rebuild everything from tape.toml.

    python3 tools/build.py [--config PATH] [--force-chords]

1. docs/chords.json  - worked out from the song when [chords] mode = "auto"
                       (skipped when the song hasn't changed; needs numpy, scipy, ffmpeg)
2. assets/hero.svg, assets/music.svg, assets/footer.svg
3. docs/tape.json    - what the music page reads (label, song file, length, owner)
4. README.md         - the cassette link between <!-- tape:start --> and <!-- tape:end -->

The GitHub Action in .github/workflows/tape.yml runs this on every push that changes
tape.toml or the song, so normally you never have to run it yourself.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tapecfg import ROOT, load  # noqa: E402

TOOLS = os.path.join(ROOT, 'tools')


def run(*args):
    print('$', ' '.join(os.path.relpath(a, ROOT) if os.path.isabs(a) else a for a in args), flush=True)
    return subprocess.run([sys.executable, *args], cwd=ROOT).returncode


def chords_current(song, out):
    """True when out was made from this exact song file (so numpy isn't needed)."""
    try:
        with open(out) as f:
            have = json.load(f).get('source_sha1')
        with open(song, 'rb') as f:
            return have == hashlib.sha1(f.read()).hexdigest()
    except (OSError, ValueError, AttributeError):
        return False


def main():
    argv = sys.argv[1:]
    conf = argv[argv.index('--config') + 1] if '--config' in argv else None
    cfg = load(conf)
    extra = ['--config', conf] if conf else []
    t = cfg['tape']

    if not os.path.exists(t['song_abs']):
        sys.exit(f"Song not found: {t['song']}. Put your file in docs/ and set [tape] song in tape.toml.")

    # 1. chords
    mode = cfg['chords']['mode']
    if mode == 'auto' and '--force-chords' not in argv and chords_current(t['song_abs'], cfg['chords']['file']):
        print('chords: up to date with the song')
    elif mode == 'auto':
        force = ['--force'] if '--force-chords' in argv else []
        if run(os.path.join(TOOLS, 'chords.py'), t['song_abs'], cfg['chords']['file'], *force) != 0:
            print('! chord detection failed; keeping the old docs/chords.json '
                  '(install numpy, scipy and ffmpeg, or set [chords] mode = "keep")')
    else:
        print(f'chords: mode = "{mode}", leaving docs/chords.json alone')

    # 2. pictures
    failed = []
    for name, out in (('hero', 'hero.svg'), ('music', 'music.svg'), ('footer', 'footer.svg')):
        if run(os.path.join(TOOLS, f'{name}.py'), os.path.join(ROOT, 'assets', out), *extra) != 0:
            failed.append(out)

    # 3. settings for the music page
    page = {
        'label': t['label'], 'side': t['side'], 'song': t['song_url'],
        'duration': round(t['duration'], 2), 'length': t['length'],
        'owner': cfg['owner'], 'repo': cfg['repo'], 'chords': mode != 'off',
    }
    with open(os.path.join(ROOT, 'docs', 'tape.json'), 'w') as f:
        json.dump(page, f, indent=2)
        f.write('\n')
    print('wrote docs/tape.json')

    # 4. cassette link in README.md
    readme = os.path.join(ROOT, 'README.md')
    with open(readme) as f:
        text = f.read()
    new = text
    block = re.compile(r'(<!-- tape:start[^>]*-->.*?<a href=")[^"]*(")', re.S)
    if block.search(new):
        new = block.sub(lambda m: m.group(1) + t['link'] + m.group(2), new, count=1)
    else:
        print('README.md: no <!-- tape:start --> block, link left as is')
    # image descriptions for screen readers, kept in step with the pictures
    def sentence(s):
        s = s.strip()
        return s[:1].upper() + s[1:]
    alts = {
        'hero.svg': sentence(' '.join(cfg['hero']['greeting'])),
        'music.svg': sentence(' '.join(t['caption'])) + ' Play the recording.',
        'footer.svg': sentence(cfg['footer']['text']),
    }
    for svg, alt in alts.items():
        alt = alt.replace('"', '&quot;')
        new = re.sub(r'(<img src="\./assets/' + re.escape(svg) + r'"[^>]*?alt=")[^"]*(")',
                     lambda m: m.group(1) + alt + m.group(2), new)
    if new != text:
        with open(readme, 'w') as f:
            f.write(new)
        print(f"README.md: updated (cassette links to {t['link']})")

    if failed:
        sys.exit('failed to draw: ' + ', '.join(failed))


if __name__ == '__main__':
    main()
