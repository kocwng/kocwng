#!/usr/bin/env python3
"""Render docs/tape.mp4: the song as a 1280x720 video in the README sticker style.

    python3 tools/video.py [docs/tape.mp4] [--config tape.toml]

Needs Pillow and numpy (pip install pillow numpy) and ffmpeg/ffprobe on PATH.

What is in it: the [tape] label in big bobbing letters, the cassette with spinning reels
(the tape winds from left to right as the song plays), 16 equalizer bars driven by the
song's spectrum, the banana from assets/banana.png bobbing on the beat (re-render it with
tools/banana.py after changing the banana in tools/hero.py), a chord card that follows
docs/chords.json (left out when [chords] mode = "off" or there are no chords), and a
progress bar with the time.

The song is copied into the video untouched when it is AAC (m4a), otherwise encoded as
AAC 160k. The video is H.264 and kept under 8 MB, so it fits GitHub's 10 MB upload limit.

GitHub only plays a video inline in a README when it was uploaded through GitHub itself:
open README.md in the web editor (pencil icon), drag docs/tape.mp4 into the text, and
commit. GitHub turns it into a https://github.com/user-attachments/... link that shows
as a player. A relative link to docs/tape.mp4 only shows as a plain link.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tapecfg import ROOT, load  # noqa: E402
from textfit import args  # noqa: E402

W, H, FPS = 1280, 720, 24
K = 4                                    # supersampling for the shapes drawn once
MAX_BYTES = 8_000_000                    # GitHub takes 10 MB; stay well under it
TARGET_BYTES = 7_400_000

KREM, TINTA, BG = (255, 246, 229), (43, 35, 64), (29, 23, 48)
JERUK, PINK, KUNING = (255, 138, 61), (255, 95, 162), (255, 210, 63)
MINT, LANGIT, ANGGUR = (61, 220, 151), (76, 201, 240), (123, 92, 255)
PALETTE = [JERUK, PINK, KUNING, MINT, LANGIT, ANGGUR]
DOTS = [KUNING, MINT, LANGIT, PINK, JERUK]          # finger dots, as on the music page
SHADOW = TINTA + (215,)                              # sticker shadow: ink, offset down-right
ROUND_FONTS = [
    '/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf',
    '/Library/Fonts/Arial Rounded Bold.ttf',
    '~/Library/Fonts/Nunito-Black.ttf', '~/Library/Fonts/Nunito-ExtraBold.ttf',
    '/usr/share/fonts/truetype/nunito/Nunito-Black.ttf',
    '/usr/share/fonts/truetype/nunito/Nunito-ExtraBold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    'C:/Windows/Fonts/arialbd.ttf',
]
SANS_FONTS = [
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/System/Library/Fonts/Supplemental/Verdana Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    'C:/Windows/Fonts/arialbd.ttf',
]
_fonts = {}


def _font_file(cands):
    for c in cands:
        p = os.path.expanduser(c)
        if os.path.exists(p):
            return p
    try:                                  # Linux without the usual paths: ask fontconfig
        p = subprocess.run(['fc-match', '-f', '%{file}', 'sans:bold'],
                           capture_output=True, text=True, timeout=10).stdout.strip()
        if p and os.path.exists(p):
            return p
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def font(kind, size):
    key = (kind, round(size))
    if key not in _fonts:
        if kind not in _fonts:
            _fonts[kind] = _font_file(ROUND_FONTS if kind == 'round' else SANS_FONTS)
        path = _fonts[kind]
        _fonts[key] = (ImageFont.truetype(path, max(1, round(size))) if path
                       else ImageFont.load_default(max(1, round(size))))
    return _fonts[key]


def mix(c, over, a):
    """Colour c at opacity a over the opaque colour `over`."""
    return tuple(round(c[i] * a + over[i] * (1 - a)) for i in range(3))


def bezier(x1, y1, x2, y2):
    """CSS cubic-bezier() as a lookup function on [0, 1]."""
    s = np.linspace(0, 1, 4096)
    bx = 3 * x1 * s * (1 - s) ** 2 + 3 * x2 * s ** 2 * (1 - s) + s ** 3
    by = 3 * y1 * s * (1 - s) ** 2 + 3 * y2 * s ** 2 * (1 - s) + s ** 3
    return lambda p: float(np.interp(min(max(p, 0.0), 1.0), bx, by))


BOUNCE = bezier(.5, -.4, .5, 1.4)
POP = bezier(.5, -.4, .5, 1.6)
EASE_OUT = bezier(0, 0, .58, 1)


def keyframes(p, frames, ease):
    """Value at phase p in [0,1) of [(at, value), ...] keyframes (values are tuples)."""
    for (a, va), (b, vb) in zip(frames, frames[1:]):
        if a <= p <= b:
            e = ease((p - a) / (b - a)) if b > a else 1
            return tuple(x + (y - x) * e for x, y in zip(va, vb))
    return frames[-1][1]


# ---------------------------------------------------------------- drawing helpers

class Pen:
    """RGBA canvas in 'units' (scale px per unit), drawn K times larger, then reduced.
    ImageDraw has no anti-aliasing; the reduction gives smooth edges."""

    def __init__(self, w, h, scale=1.0, ox=0.0, oy=0.0):
        self.s, self.ox, self.oy, self.w, self.h = scale * K, ox, oy, w, h
        self.im = Image.new('RGBA', (round(w * K), round(h * K)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def p(self, x, y):
        return (x + self.ox) * self.s, (y + self.oy) * self.s

    def rrect(self, x0, y0, x1, y1, r, fill, stroke=None, sw=0.0):
        """Rounded rect; stroke is centred on the edge like SVG."""
        if stroke and sw:
            h = sw / 2
            self._rr(x0 - h, y0 - h, x1 + h, y1 + h, r + h, stroke)
            self._rr(x0 + h, y0 + h, x1 - h, y1 - h, max(0.0, r - h), fill)
        else:
            self._rr(x0, y0, x1, y1, r, fill)

    def _rr(self, x0, y0, x1, y1, r, fill):
        a, b = self.p(x0, y0), self.p(x1, y1)
        r = min(r * self.s, (b[0] - a[0]) / 2, (b[1] - a[1]) / 2)
        self.d.rounded_rectangle([a, b], radius=max(0, r), fill=fill)

    def circle(self, cx, cy, r, fill=None, stroke=None, sw=0.0):
        if stroke and sw:
            if fill:
                self._c(cx, cy, r + sw / 2, stroke)
                self._c(cx, cy, r - sw / 2, fill)
            else:                            # ring only: keep what is underneath
                h = r + sw / 2
                self.d.ellipse([self.p(cx - h, cy - h), self.p(cx + h, cy + h)], outline=stroke,
                               width=max(1, round(sw * self.s)))
        else:
            self._c(cx, cy, r, fill)

    def _c(self, cx, cy, r, fill):
        self.d.ellipse([self.p(cx - r, cy - r), self.p(cx + r, cy + r)], fill=fill)

    def line(self, pts, color, sw, round_caps=True):
        P = [self.p(*q) for q in pts]
        self.d.line(P, fill=color, width=max(1, round(sw * self.s)), joint='curve')
        if round_caps:
            for q in pts:
                self._c(q[0], q[1], sw / 2, color)

    def poly(self, pts, fill):
        self.d.polygon([self.p(*q) for q in pts], fill=fill)

    def text(self, x, y, s, kind, size, fill, anchor='ls'):
        self.d.text(self.p(x, y), s, font=font(kind, size * self.s), fill=fill, anchor=anchor)

    def done(self, angle=0.0):
        """angle in degrees, counter-clockwise (PIL); the canvas keeps its size."""
        im = self.im
        if angle:
            im = im.rotate(angle, resample=Image.BICUBIC)
        return im.resize((round(self.w), round(self.h)), Image.LANCZOS)


def text_sprite(s, kind, size, fill, stroke=KREM, sw=0, shadow=None, pad=None):
    """Anti-aliased text with an outline and an offset shadow, built from masks
    so the edges composite correctly. Returns (RGBA image, baseline-left offset)."""
    f = font(kind, size)
    pad = pad if pad is not None else sw + 14
    l, t, r, b = f.getbbox(s, anchor='ls', stroke_width=sw)
    w, h = r - l + 2 * pad, b - t + 2 * pad
    org = (pad - l, pad - t)

    def mask(stroke_w):
        m = Image.new('L', (w, h), 0)
        ImageDraw.Draw(m).text(org, s, font=f, fill=255, anchor='ls', stroke_width=stroke_w, stroke_fill=255)
        return m

    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    outer = mask(sw) if sw else None
    if shadow:
        dx, dy, col = shadow
        m = Image.new('L', (w, h), 0)
        m.paste(outer or mask(0), (dx, dy))
        m = m.point(lambda v: v * col[3] // 255)
        sh = Image.new('RGBA', (w, h), col[:3] + (0,))
        sh.putalpha(m)
        out = Image.alpha_composite(out, sh)
    if sw:
        lay = Image.new('RGBA', (w, h), stroke + (0,))
        lay.putalpha(outer)
        out = Image.alpha_composite(out, lay)
    lay = Image.new('RGBA', (w, h), fill + (0,))
    lay.putalpha(mask(0))
    out = Image.alpha_composite(out, lay)
    return out, org


def paste(frame, im, x, y):
    frame.paste(im, (round(x), round(y)), im)


# ---------------------------------------------------------------- audio analysis

def decode(song, sr=22050):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', song, '-map', '0:a:0', '-ac', '1', '-ar', str(sr),
                          '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32), sr


def spectrum_levels(x, sr, n_frames, n_bars=16, nfft=2048):
    """Bar levels 0..1 per video frame: log bands 60 Hz - 6 kHz, like the music page."""
    win = np.hanning(nfft).astype(np.float32)
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    edges = 60 * 100 ** (np.arange(n_bars + 1) / n_bars)
    bins = [(int(np.searchsorted(freqs, a)), max(int(np.searchsorted(freqs, a)) + 1, int(np.searchsorted(freqs, b))))
            for a, b in zip(edges, edges[1:])]
    pad = np.concatenate([np.zeros(nfft // 2, np.float32), x, np.zeros(nfft, np.float32)])
    db = np.empty((n_frames, n_bars), np.float32)
    for n in range(n_frames):
        c = int(n / FPS * sr)
        mag = np.abs(np.fft.rfft(pad[c:c + nfft] * win))
        db[n] = [20 * np.log10(mag[a:b].max() + 1e-6) for a, b in bins]
    # flatten the spectral tilt a little so the treble bars move too, then map ~42 dB to 0..1
    med = np.median(db, axis=0)
    db = db - 0.7 * (med - np.median(med))
    hi = np.percentile(db, 99.3)
    lv = np.clip((db - (hi - 42)) / 42, 0, 1) ** 1.35
    # half of each bar follows its own range, so quiet bands still move
    p5, p99 = np.percentile(lv, 5, axis=0), np.percentile(lv, 99, axis=0)
    lv = 0.5 * lv + 0.5 * np.clip((lv - p5) / np.maximum(p99 - p5, 1e-3), 0, 1)
    # smoothing: quick rise, slow fall (no flicker)
    out = np.empty_like(lv)
    y = np.zeros(n_bars, np.float32)
    for n in range(n_frames):
        y = np.where(lv[n] > y, y + 0.65 * (lv[n] - y), y + 0.22 * (lv[n] - y))
        out[n] = y
    # gentle neighbour blur so the row reads as one shape
    out[:, 1:-1] = 0.2 * out[:, :-2] + 0.6 * out[:, 1:-1] + 0.2 * out[:, 2:]
    return out


def estimate_beat(levels):
    """Beat period in seconds from the bar levels (spectral flux autocorrelation)."""
    flux = np.maximum(np.diff(levels, axis=0), 0).sum(axis=1)
    flux = flux - flux.mean()
    if len(flux) < FPS * 4 or not flux.any():
        return 0.6
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
    lo, hi = int(0.45 * FPS), int(1.3 * FPS)
    return (lo + int(np.argmax(ac[lo:hi]))) / FPS


# ---------------------------------------------------------------- static layers

def background():
    k = 2
    im = Image.new('RGB', (W * k, H * k), BG)
    d = ImageDraw.Draw(im)
    dot = mix(KREM, BG, 0.07)
    for y in range(14, H, 28):
        for x in range(14, W, 28):
            d.ellipse([(x - 2.25) * k, (y - 2.25) * k, (x + 2.25) * k, (y + 2.25) * k], fill=dot)
    return im.resize((W, H), Image.LANCZOS)


class Title:
    """Big colourful letters, each with a cream outline and ink shadow, bobbing in a wave."""

    def __init__(self, text, cx, base, max_w, size=104):
        def measure(z):
            f = font('round', z)
            return f, sum(f.getlength(c) for c in text) + z * .04 * (len(text) - 1), max(5, round(z * .075))

        f, total, sw = measure(size)
        while total + 2 * sw > max_w and size > 36:
            size -= 2
            f, total, sw = measure(size)
        self.letters, self.cache = [], {}
        track = size * .04
        x = cx - total / 2
        j = 0
        for ch in text:
            adv = f.getlength(ch)
            if ch.strip():
                im, org = text_sprite(ch, 'round', size, PALETTE[j % len(PALETTE)], KREM, sw,
                                      shadow=(round(size * .05), round(size * .065), SHADOW))
                self.letters.append((im, x - org[0], base - org[1], len(self.letters)))
                j += 1
            x += adv + track

    def draw(self, frame, t):
        for im, x, y, i in self.letters:
            p = ((t - i * 0.09) / 2.4) % 1
            e = BOUNCE(p * 2) if p < .5 else 1 - BOUNCE((p - .5) * 2)
            ang = round((-3 + 6 * e) * 4) / 4              # CSS deg, clockwise
            key = (i, ang)
            if key not in self.cache:
                self.cache[key] = im.rotate(-ang, resample=Image.BICUBIC)
            paste(frame, self.cache[key], x, y - 9 * e)


class Cassette:
    """The cassette from assets/music.svg (same units), tilted -3 deg, reels spinning."""
    S = 1.8                                   # px per music.svg unit
    TILT = 3.0                                # degrees counter-clockwise

    def __init__(self, cfg, cx, cy):
        S, t = self.S, cfg['tape']
        self.cx, self.cy = cx, cy             # screen position of unit point (145, 60)
        self.box = (-45, -50, 335, 170)       # canvas in units
        bw, bh = self.box[2] - self.box[0], self.box[3] - self.box[1]
        pen = Pen(bw * S, bh * S, S, -self.box[0], -self.box[1])
        pen.rrect(4, 5, 294, 127, 18, SHADOW)
        pen.rrect(0, 0, 290, 122, 18, ANGGUR, KREM, 5)
        for x, y in ((12, 12), (278, 12), (12, 110), (278, 110)):
            pen.circle(x, y, 4, KREM, TINTA, 1.4)
        pen.rrect(22, 10, 268, 94, 10, KREM)
        pen.rrect(22, 58, 268, 65, 0, PINK)
        pen.rrect(22, 69, 268, 76, 0, KUNING)
        # label text: from x=36 to just before the side badge
        label, size = t['label'], 20.0
        fw = lambda s, z: font('round', z * 8).getlength(s) / 8
        while fw(label, size) > 188 and size > 10:
            size -= .5
        while fw(label, size) > 188 and len(label) > 1:
            label = label[:-2].rstrip() + '…'
        pen.text(36, 27.8 + .36 * size, label, 'round', size, TINTA)
        side = f"side {t['side']} · {t['length']}" if t['length'] else f"side {t['side']}"
        pen.text(37, 51, side, 'sans', 11.5, mix(TINTA, KREM, .8))
        pen.circle(246, 30, 12, PINK)
        bs = 15.0
        while fw(t['side'], bs) > 19 and bs > 9:
            bs -= .5
        pen.text(246, 30, t['side'], 'round', bs, KREM, anchor='mm')
        pen.rrect(72, 54, 218, 88, 17, TINTA)
        pen.rrect(98, 80, 192, 84, 0, mix(LANGIT, TINTA, .55))
        pen.poly([(78, 122), (90, 100), (200, 100), (212, 122)], JERUK)
        pen.line([(78, 122), (90, 100), (200, 100), (212, 122)], KREM, 4)
        for x in (112, 178):
            pen.circle(x, 112, 4.5, KREM, TINTA, 1.4)
        pen.rrect(139, 106, 151, 116, 2, TINTA)
        pen.rrect(139.7, 106.7, 150.3, 115.3, 1.4, KREM)
        self.body = pen.done(self.TILT)
        self.x0 = cx - (145 - self.box[0]) * S
        self.y0 = cy - (60 - self.box[1]) * S

        # reel: cream wheel, ink hub, four teeth (four-fold symmetric)
        rp = Pen(26 * S, 26 * S, S, 13, 13)
        rp.circle(0, 0, 11, KREM)
        rp.circle(0, 0, 4, TINTA)
        for x0, y0, x1, y1 in ((-1.5, -9.5, 1.5, -4.5), (-1.5, 4.5, 1.5, 9.5), (-9.5, -1.5, -4.5, 1.5), (4.5, -1.5, 9.5, 1.5)):
            rp.rrect(x0, y0, x1, y1, 1, TINTA)
        self.reel_big = rp.im
        self.reel_size = rp.w
        self.reels, self.blobs = {}, {}
        self.tape = mix(LANGIT, TINTA, .55)

    def pos(self, ux, uy, bob):
        a = math.radians(self.TILT)
        dx, dy = (ux - 145) * self.S, (uy - 60) * self.S
        return (self.cx + dx * math.cos(a) + dy * math.sin(a),
                self.cy - dx * math.sin(a) + dy * math.cos(a) + bob)

    def reel(self, ang):
        q = int(round(ang / 2)) * 2 % 90
        if q not in self.reels:
            im = self.reel_big.rotate(q + self.TILT, resample=Image.BICUBIC)
            self.reels[q] = im.resize((round(self.reel_size),) * 2, Image.LANCZOS)
        return self.reels[q]

    def blob(self, r):
        q = round(r * 4) / 4
        if q not in self.blobs:
            p = Pen((2 * q + 2) * self.S, (2 * q + 2) * self.S, self.S, q + 1, q + 1)
            p.circle(0, 0, q, self.tape)
            self.blobs[q] = p.done()
        return self.blobs[q]

    def draw(self, frame, t, prog):
        p = (t / 2.6) % 1
        bob = -8 * (BOUNCE(p * 2) if p < .5 else 1 - BOUNCE((p - .5) * 2))
        paste(frame, self.body, self.x0, self.y0 + bob)
        for ux, r, period in ((98, 15 - 3.5 * prog, 2.2), (192, 11.5 + 3.5 * prog, 1.6)):
            b = self.blob(r)
            x, y = self.pos(ux, 71, bob)
            paste(frame, b, x - b.width / 2, y - b.height / 2)
            im = self.reel(t / period * 360)
            paste(frame, im, x - im.width / 2, y - im.height / 2)


class Equalizer:
    def __init__(self, cx, floor, n=16, bw=26, gap=9, hmin=26, hmax=168):
        self.n, self.bw, self.floor, self.hmin, self.hmax = n, bw, floor, hmin, hmax
        self.x0 = cx - (n * bw + (n - 1) * gap) / 2
        self.step = bw + gap
        self.cache = {}

    def bar(self, i, h):
        c = i % len(PALETTE)
        key = (c, h)
        if key not in self.cache:
            sw, o = 4, 6                         # cream outline, room for the shadow
            pen = Pen(self.bw + 2 * sw + o + 2, h + 2 * sw + o + 2, 1, sw + 1, sw + 1)
            r = self.bw / 2
            pen.rrect(3, 4, self.bw + 3, h + 4, r, SHADOW)
            pen.rrect(0, 0, self.bw, h, r, PALETTE[c], KREM, sw)
            self.cache[key] = pen.done()
        return self.cache[key]

    def draw(self, frame, levels):
        for i, v in enumerate(levels):
            h = int(round(self.hmin + (self.hmax - self.hmin) * float(v)))
            im = self.bar(i, h)
            paste(frame, im, self.x0 + i * self.step - 5, self.floor - h - 5)


class Banana:
    """assets/banana.png, squashing and bobbing on every beat (like .sq in hero.svg)."""
    FRAMES = [(0, (0, 1, 1)), (.15, (6, 1.035, .96)), (.36, (-9, .985, 1.025)),
              (.57, (3, 1.015, .98)), (.78, (0, 1, 1)), (1, (0, 1, 1))]

    def __init__(self, path, cx, bottom, height):
        im = Image.open(path).convert('RGBA')
        f = height / im.height
        self.big = im
        self.w, self.h = im.width * f, im.height * f
        self.cx, self.bottom = cx, bottom
        self.cache = {}

    def draw(self, frame, t, beat):
        q = int((t / beat) % 1 * 24)
        if q not in self.cache:
            dy, sx, sy = keyframes(q / 24, self.FRAMES, EASE_OUT)
            im = self.big.resize((round(self.w * sx), round(self.h * sy)), Image.LANCZOS)
            self.cache[q] = (im, dy)
        im, dy = self.cache[q]
        paste(frame, im, self.cx - im.width / 2, self.bottom - im.height + dy)


class ChordCard:
    """Cream card, ink border, tilted 5 deg: chord name, ukulele diagram (G C E A), next chord."""
    CW, CH = 214, 292

    def __init__(self, chords, cx, cy):
        self.tl = chords['timeline']
        self.shapes = chords.get('shapes', {})
        self.cx, self.cy = cx, cy
        self.cache = {}

    def index(self, t):
        for i, (_, _, end) in enumerate(self.tl):
            if t < end:
                return i
        return len(self.tl) - 1

    def render(self, i):
        name = self.tl[i][0]
        nxt = self.tl[i + 1][0] if i + 1 < len(self.tl) else ''
        shape = str(self.shapes.get(name, '0000'))[:4].ljust(4, '0')
        CW, CH = self.CW, self.CH
        m = 30                                    # room for the shadow and the tilt
        pen = Pen(CW + 2 * m, CH + 2 * m, 1, m, m)
        pen.rrect(8, 10, CW + 8, CH + 10, 36, SHADOW)
        pen.rrect(0, 0, CW, CH, 36, KREM, TINTA, 7)
        # chord name
        size = 64
        while font('round', size * K).getlength(name) / K > CW - 40 and size > 24:
            size -= 2
        pen.text(CW / 2, 74, name, 'round', size, TINTA, anchor='ms')
        # diagram: index.html geometry (72x80 box) at g px per unit
        g, ox, oy = 2.0, CW / 2 - 36 * 2.0, 84
        P = lambda x, y: (ox + x * g, oy + y * g)
        xs, top, fh = [12, 28, 44, 60], 14, 15
        frets = [int(c) for c in shape if c.isdigit()]
        base = 1 if not frets or max(frets) <= 4 else min(f for f in frets if f > 0)
        nut = base == 1
        x0, y0 = P(10, top - 3)
        x1, y1 = P(62, top + 1)
        if nut:
            pen.rrect(x0, y0, x1, y1, 2 * g, TINTA)
        else:
            pen.text(P(4, top + .5 * fh)[0], P(4, top + .5 * fh)[1], f'{base}', 'sans', 18, TINTA, anchor='rm')
        line = mix(TINTA, KREM, .5)
        for f in range(1, 5):
            pen.line([P(12, top + f * fh), P(60, top + f * fh)], line, 1.5 * g)
        if not nut:
            pen.line([P(12, top), P(60, top)], line, 1.5 * g)
        for x in xs:
            pen.line([P(x, top), P(x, top + 4 * fh)], TINTA, 2 * g, round_caps=False)
        for s, c in enumerate(shape):
            x = xs[s]
            if c.lower() == 'x':
                cx, cy = P(x, top - 8)
                pen.line([(cx - 5, cy - 5), (cx + 5, cy + 5)], TINTA, 3)
                pen.line([(cx - 5, cy + 5), (cx + 5, cy - 5)], TINTA, 3)
            elif c == '0' or not c.isdigit():
                cx, cy = P(x, top - 8)
                pen.circle(cx, cy, 3.5 * g, None, TINTA, 1.8 * g)
            else:
                f = int(c) - base + 1
                cx, cy = P(x, top + (f - .5) * fh)
                pen.circle(cx, cy, 6 * g, DOTS[s % len(DOTS)], TINTA, 2 * g)
        if nxt:
            pen.text(CW / 2, CH - 22, f'next: {nxt}', 'sans', 22, mix(TINTA, KREM, .7), anchor='ms')
        return pen.done(-5)                       # CSS rotate(5deg) = clockwise

    def draw(self, frame, t):
        i = self.index(t)
        if i not in self.cache:
            self.cache[i] = self.render(i)
        im = self.cache[i]
        since = t - self.tl[i][1]
        if t > 0 and since < .35 and self.tl[i][1] > 0:
            s = .7 + .3 * POP(since / .35)
            im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.BILINEAR)
        paste(frame, im, self.cx - im.width / 2, self.cy - im.height / 2)


class Progress:
    def __init__(self, x0, x1, cy, dur):
        self.x0, self.x1, self.cy, self.dur = x0, x1, cy, dur
        hh = 7
        self.track = Pen(x1 - x0 + 2 * hh + 8, 2 * hh + 8, 1, 4 + hh, 4 + hh)
        self.track.rrect(-hh, -hh, x1 - x0 + hh, hh, hh, mix(KREM, BG, .16))
        self.track = self.track.done()
        fill = Pen(x1 - x0 + 2 * hh + 8, 2 * hh + 8, 1, 4 + hh, 4 + hh)
        fill.rrect(-hh, -hh, x1 - x0 + hh, hh, hh, KUNING)
        self.fill = fill.done()
        knob = Pen(40, 40, 1, 20, 20)
        knob.circle(2, 3, 13, SHADOW)
        knob.circle(0, 0, 13, PINK, KREM, 5)
        self.knob = knob.done()
        self.texts = {}
        self.total = self.fmt(dur)

    @staticmethod
    def fmt(s):
        s = int(s)
        return f'{s // 60}:{s % 60:02d}'

    def static(self, bg):
        paste(bg, self.track, self.x0 - 11, self.cy - 11)

    def draw(self, frame, t):
        p = min(1.0, max(0.0, t / self.dur)) if self.dur else 0
        x = self.x0 + p * (self.x1 - self.x0)
        w = round(x - self.x0 + 11)
        if w > 0:
            part = self.fill.crop((0, 0, w + 7, self.fill.height))
            paste(frame, part, self.x0 - 11, self.cy - 11)
        paste(frame, self.knob, x - 20, self.cy - 20)
        s = f'{self.fmt(t)} / {self.total}'
        if s not in self.texts:
            self.texts[s] = text_sprite(s, 'round', 30, KREM, pad=4)
        im, org = self.texts[s]
        paste(frame, im, self.x1 + 34 - org[0], self.cy + 11 - org[1])


# ---------------------------------------------------------------- main

def load_chords(cfg):
    if cfg['chords']['mode'] == 'off':
        return None
    try:
        with open(cfg['chords']['file'], encoding='utf-8') as f:
            j = json.load(f)
        tl = [(str(n), float(a), float(b)) for n, a, b in j.get('timeline', [])]
    except (OSError, ValueError, TypeError):
        return None
    if not tl:
        return None
    return {'timeline': tl, 'shapes': j.get('shapes') or {}, 'beat': j.get('beat')}


def audio_info(song):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries',
                          'stream=codec_name,bit_rate:format=bit_rate', '-of', 'json', song],
                         capture_output=True, text=True).stdout
    j = json.loads(out or '{}')
    st = (j.get('streams') or [{}])[0]
    br = st.get('bit_rate') or j.get('format', {}).get('bit_rate') or 192000
    return st.get('codec_name', ''), int(br)


def encode(frames_fn, n, song, out, seconds, codec, abr, crf, maxrate):
    acopy = codec == 'aac'
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-i', song, '-map', '0:v:0', '-map', '1:a:0',
           '-c:v', 'libx264', '-preset', 'medium', '-tune', 'animation', '-crf', str(crf),
           '-maxrate', f'{maxrate}k', '-bufsize', f'{2 * maxrate}k', '-pix_fmt', 'yuv420p',
           '-threads', '2', '-c:a', 'copy' if acopy else 'aac']
    if not acopy:
        cmd += ['-b:a', '160k']
    cmd += ['-t', f'{seconds:.3f}', '-movflags', '+faststart', out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for fr in frames_fn(n):
            proc.stdin.write(fr.tobytes())
        proc.stdin.close()
    except BrokenPipeError:
        pass
    if proc.wait() != 0:
        sys.exit('video.py: ffmpeg failed')


def scene(cfg, seconds=None):
    """Everything that is drawn. Returns (frame(k) -> RGB image, frame count, length, info)."""
    song = cfg['tape']['song_abs']
    x, sr = decode(song)
    dur = len(x) / sr or cfg['tape']['duration']    # decoded length = what the player plays
    length = min(dur, seconds) if seconds else dur
    n = int(math.ceil(length * FPS))
    levels = spectrum_levels(x, sr, n)
    # first frames (the poster): show a lively row that fades into the real levels
    peek = levels[min(n - 1, int(1.2 * FPS))]
    for k in range(min(n, FPS)):
        levels[k] = np.maximum(levels[k], peek * math.exp(-k / FPS / .3))
    chords = load_chords(cfg)
    beat = float(chords['beat']) if chords and chords.get('beat') else 0
    if not 0.25 < beat < 3:
        beat = estimate_beat(levels)

    # layout (1280x720): left = title, cassette, equalizer; right = chord card, banana
    bg = background()
    title = Title(cfg['tape']['label'], 352, 128, 640)
    cassette = Cassette(cfg, 352, 300)
    eq = Equalizer(352, 622)
    if chords:
        card = ChordCard(chords, 1104, 236)
        banana = Banana(os.path.join(ROOT, 'assets', 'banana.png'), 822, 648, 448)
    else:
        card = None
        banana = Banana(os.path.join(ROOT, 'assets', 'banana.png'), 960, 648, 480)
    prog = Progress(72, 1040, 680, dur)
    prog.static(bg)

    def frame(k):
        t = k / FPS
        fr = bg.copy()
        title.draw(fr, t)
        cassette.draw(fr, t, t / dur)
        eq.draw(fr, levels[k])
        banana.draw(fr, t, beat)
        if card:
            card.draw(fr, t)
        prog.draw(fr, t)
        return fr

    return frame, n, length, f'beat {beat:.2f} s, chords {"on" if card else "off"}'


def main():
    argv = sys.argv
    seconds = None
    if '--seconds' in argv:                   # hidden: render only the first N seconds (tests)
        i = argv.index('--seconds')
        seconds = float(argv[i + 1])
        del argv[i:i + 2]
    out, conf = args(os.path.join(ROOT, 'docs', 'tape.mp4'))
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            sys.exit(f'video.py: {tool} not found')
    cfg = load(conf)
    song = cfg['tape']['song_abs']
    if not os.path.exists(song):
        sys.exit(f'video.py: song not found: {song}')
    t0 = time.time()

    frame, n, length, info = scene(cfg, seconds)
    frames = lambda count: (frame(k) for k in range(count))
    codec, abr = audio_info(song)
    audio_bits = (abr if codec == 'aac' else 160000) * length
    crf, maxrate = 20, int(max(250, min(3000, (TARGET_BYTES * 8 - audio_bits) / length / 1000 * .93)))
    for _ in range(3):
        encode(frames, n, song, out, length, codec, abr, crf, maxrate)
        size = os.path.getsize(out)
        if size <= MAX_BYTES:
            break
        print(f'{size} bytes is too big, trying again smaller')
        crf, maxrate = crf + 3, int(maxrate * .75)
    print(f'{out} {os.path.getsize(out)} bytes, {length:.2f} s, {n} frames, '
          f'{info}, {time.time() - t0:.1f} s')


if __name__ == '__main__':
    main()
