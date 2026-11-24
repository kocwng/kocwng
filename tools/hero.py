#!/usr/bin/env python3
"""Generator assets/hero.svg (lihat STYLE.md).

    python3 tools/hero.py [assets/hero.svg] [--config tape.toml]

Kiri: judul stiker bergelombang dari [hero] greeting di tape.toml (1-2 baris, mengecil
otomatis supaya tidak menabrak pisang).
Kanan: maskot pisang orisinal memetik ukulele; kartu kord mengikuti [chords] file
(sekitar 40 detik pertama, durasi asli), not balok melayang tiap genjrengan.
Tanpa kord (mode "off", file hilang/rusak, timeline kosong): pisang genjreng saja, tanpa kartu.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tapecfg import ROOT, load  # noqa: E402
from textfit import ADV, DEFAULT_ADV, args, esc, fit  # noqa: E402

OUT, CONF = args(os.path.join(ROOT, 'assets', 'hero.svg'))
cfg = load(CONF)

KREM, TINTA = '#FFF6E5', '#2B2340'
JERUK, PINK, KUNING = '#FF8A3D', '#FF5FA2', '#FFD23F'
MINT, LANGIT, ANGGUR = '#3DDC97', '#4CC9F0', '#7B5CFF'
BOUNCE = 'cubic-bezier(.5,-0.4,.5,1.4)'
W, H = 900, 300

css, defs, out = [], [], []
add = out.append


def num(v):
    """angka ringkas: 128.0 -> '128', 117.25 -> '117.2'"""
    return f'{v:.1f}'.rstrip('0').rstrip('.')


def shadow(inner):
    """Bayangan stiker: salinan digeser (+4,+5), tinta 0.35."""
    return f'<g transform="translate(4 5)" fill="{TINTA}" stroke="{TINTA}" opacity=".35">{inner}</g>'


# ---------------------------------------------------------------- judul
GREETING = cfg['hero']['greeting']
TRACK = .05
FS_MAX = 90                  # ukuran penuh (judul "hello there!" asli)
X0, INDENT = 40, 52          # baris 1 mulai di x=40, baris 2 menjorok 52 px (pada ukuran penuh)
RIGHT = 540                  # batas kanan judul: kepala ukulele ~x 555, kartu kord ~x 600
MID = 139.6                  # tengah vertikal blok huruf (tinggi kapital) di samping pisang
PALETTES = ([JERUK, PINK, ANGGUR, LANGIT, MINT], [MINT, JERUK, PINK, ANGGUR, LANGIT, PINK])
WAVE = 3.0


def em(text):
    return sum(ADV.get(c, DEFAULT_ADV) + TRACK for c in text)


TITLE_FS = FS_MAX
for i, text in enumerate(GREETING):
    ind = INDENT / FS_MAX if i else 0          # indent ikut mengecil bersama huruf
    TITLE_FS = min(TITLE_FS, int((RIGHT - X0) / (em(text) + ind)))
TITLE_FS = max(TITLE_FS, 24)
K = TITLE_FS / FS_MAX
if len(GREETING) == 1:
    bases = [round(MID + .36 * TITLE_FS)]
else:
    gap = 88 * K
    b1 = round(MID - (gap - .72 * TITLE_FS) / 2)
    bases = [b1, b1 + round(gap)]
lines = [(text, X0 + (round(INDENT * K) if i else 0), bases[i], PALETTES[i]) for i, text in enumerate(GREETING)]


def cap_i(cx, base):
    """Huruf I berpalang: di font sans 'I' dan 'l' kembar, nama dengan 'I' bisa terbaca 'l'."""
    ch, bw, sw, bh = .72 * TITLE_FS, 13.5 * K, 6.5 * K, 10.5 * K
    t = base - ch
    return (f'M{num(cx - bw)} {num(t)}H{num(cx + bw)}V{num(t + bh)}H{num(cx + sw)}V{num(base - bh)}H{num(cx + bw)}V{base}'
            f'H{num(cx - bw)}V{num(base - bh)}H{num(cx - sw)}V{num(t + bh)}H{num(cx - bw)}Z')


n = 0
boxes = []                   # kotak judul (x0, y0, x1, y1), konfeti yang menabrak dibuang
add('<g class="ttl">')
for text, x0, base, cols in lines:
    x = x0
    for k, ch in enumerate(text):
        col = cols[k % len(cols)]
        w = (ADV.get(ch, DEFAULT_ADV) + TRACK) * TITLE_FS
        cx = x + w / 2
        x += w
        if ch == ' ':
            continue
        tilt = (-4, 3, -2, 4, -3)[n % 5]
        rot = f'transform="rotate({tilt} {cx:.0f} {base})"'
        if ch == 'I':
            d = cap_i(cx, base)
            sh = f'<path d="{d}" {rot} stroke-width="11" stroke-linejoin="round"/>'
            fg = (f'<path d="{d}" {rot} fill="{KREM}" stroke="{KREM}" stroke-width="11" stroke-linejoin="round"/>'
                  f'<path d="{d}" {rot} fill="{col}" stroke="{col}" stroke-width="5" stroke-linejoin="round"/>')
            add(f'<g class="wv" style="animation-delay:{n * .11:.2f}s">{shadow(sh)}{fg}</g>')
        else:
            glyph = f'<text x="{cx:.0f}" y="{base}" {rot}>{esc(ch)}</text>'
            add(f'<g class="wv" style="animation-delay:{n * .11:.2f}s">'
                f'{shadow(glyph)}<g fill="{col}" stroke="{KREM}">{glyph}</g></g>')
        n += 1
    # tinggi huruf + lompatan gelombang (13 px) di atas, ekor huruf (g, y, p) di bawah
    boxes.append((x0, base - .74 * TITLE_FS - 14, x, base + .22 * TITLE_FS))
add('</g>')
css.append(
    ".ttl text{font-family:'Arial Rounded MT Bold','Nunito','Varela Round','Trebuchet MS','Segoe UI',sans-serif;"
    f"font-weight:800;font-size:{TITLE_FS}px;text-anchor:middle;stroke-width:6;stroke-linejoin:round;paint-order:stroke}}"
    f".wv{{animation:wave {WAVE}s {BOUNCE} infinite both;transform-box:fill-box;transform-origin:50% 85%}}"
    "@keyframes wave{0%,40%,100%{transform:translateY(0) rotate(0)}"
    "12%{transform:translateY(-13px) rotate(-6deg)}24%{transform:translateY(2px) rotate(4deg)}32%{transform:translateY(0) rotate(-1deg)}}")

# ---------------------------------------------------------------- konfeti
defs.append('<path id="spk" d="M0-11Q2-2 11 0Q2 2 0 11Q-2 2-11 0Q-2-2 0-11Z"/>')
defs.append('<path id="sqg" d="M-14 0q3.5-7 7 0t7 0t7 0t7 0" fill="none"/>')
confetti = [  # (jenis, x, y, warna, skala, durasi, delay)
    ('spk', 22, 40, KUNING, 1.0, 2.6, 0), ('dot', 22, 160, LANGIT, 4.5, 2.6, -1.6),
    ('sqg', 338, 34, PINK, .9, 3.6, -1.4), ('dot', 440, 64, PINK, 6, 3.4, -1),
    ('sqg', 478, 128, LANGIT, 1, 3.0, -.5), ('spk', 520, 238, MINT, .8, 2.2, -1.2),
    ('dot', 574, 66, MINT, 5, 3.0, -2), ('spk', 876, 34, ANGGUR, .85, 2.8, -.6),
    ('dot', 882, 200, KUNING, 6, 3.2, -.3),
]
REACH = {'dot': lambda s: s + 8, 'spk': lambda s: 13 * s + 4, 'sqg': lambda s: 16 * s + 4}  # jangkauan + gerak


def hits_title(kind, x, y, s):
    r = REACH[kind](s)
    return any(x + r > x0 and x - r < x1 and y + r > y0 and y - r < y1 for x0, y0, x1, y1 in boxes)


# judul panjang: konfeti yang akan menimpa huruf dibuang
confetti = [c for c in confetti if not hits_title(c[0], c[1], c[2], c[4])]
add('<g class="cf">')
for kind, x, y, col, s, dur, dl in confetti:
    anim = f'animation-duration:{dur}s;animation-delay:{dl}s'
    if kind == 'dot':
        add(f'<g transform="translate({x} {y})"><g class="dr" style="{anim}">'
            f'<circle r="{s}" fill="{col}" stroke="{KREM}" stroke-width="7" paint-order="stroke"/></g></g>')
    elif kind == 'spk':
        add(f'<g transform="translate({x} {y}) scale({s})"><g class="tw" style="{anim}">'
            f'<use href="#spk" fill="{KREM}" stroke="{KREM}" stroke-width="8" stroke-linejoin="round"/>'
            f'<use href="#spk" fill="{col}"/></g></g>')
    else:
        add(f'<g transform="translate({x} {y}) scale({s})"><g class="wg" style="{anim}">'
            f'<use href="#sqg" stroke="{KREM}" stroke-width="10" stroke-linecap="round"/>'
            f'<use href="#sqg" stroke="{col}" stroke-width="4.5" stroke-linecap="round"/></g></g>')
add('</g>')
css.append(
    ".dr{animation:dr 3s ease-in-out infinite alternate}@keyframes dr{0%{transform:translate(0,0)}100%{transform:translate(4px,-9px)}}"
    ".tw{animation:tw 2.6s ease-in-out infinite alternate}@keyframes tw{0%{transform:scale(.75) rotate(0)}100%{transform:scale(1.15) rotate(45deg)}}"
    ".wg{animation:wg 3s ease-in-out infinite alternate}@keyframes wg{0%{transform:rotate(-12deg) translateY(0)}100%{transform:rotate(10deg) translateY(-6px)}}")


# ---------------------------------------------------------------- data kord ([chords] file)
MAX_LOOP = 40.0              # kartu kord mengulang kira-kira 40 detik pertama lagu
DEFAULT_BEAT = 1.0


def load_chords():
    """-> (beat, shapes, seq) ; seq kosong = tanpa kartu kord (mode off, file hilang/rusak/kosong)."""
    if cfg['chords']['mode'] == 'off':
        return DEFAULT_BEAT, {}, []
    try:
        with open(cfg['chords']['file']) as f:
            cj = json.load(f)
        if not isinstance(cj, dict):
            raise ValueError('not an object')
    except (OSError, ValueError) as e:
        why = 'not found' if isinstance(e, FileNotFoundError) else str(e).splitlines()[0][:60]
        print(f"hero: no chord card ({os.path.basename(cfg['chords']['file'])}: {why}), the banana just strums")
        return DEFAULT_BEAT, {}, []
    try:
        beat = float(cj.get('beat') or DEFAULT_BEAT)
        beat = round(beat, 3) if .3 <= beat <= 3 else DEFAULT_BEAT
    except (TypeError, ValueError):
        beat = DEFAULT_BEAT
    shapes = cj.get('shapes') if isinstance(cj.get('shapes'), dict) else {}
    shapes = {str(k): str(v) for k, v in shapes.items() if len(str(v)) == 4}   # GCEA, 4 senar
    tl = []
    for row in cj.get('timeline') or []:
        try:
            c, s, e = row[:3]
            c, s, e = str(c).strip(), float(s), float(e)
        except (TypeError, ValueError):
            continue
        if c and e > s:
            tl.append((c, s, e))
    if not tl:
        return beat, shapes, []
    t0 = tl[0][1]
    seq = [r for r in tl if r[2] <= t0 + MAX_LOOP] or tl[:1]
    return beat, shapes, seq


BEAT, SHAPES, seq = load_chords()
HAS_CHORDS = bool(seq)
if HAS_CHORDS:
    T0, LOOP = seq[0][1], seq[-1][2] - seq[0][1]


def pct(t):
    return f'{(t - T0) / LOOP * 100:.3f}'.rstrip('0').rstrip('.') + '%'


# ---------------------------------------------------------------- maskot pisang + ukulele
BX, BY, SC = 724, 246, 1.06  # titik kaki pisang (tertutup badan ukulele) + skala
UX, UY, UR = 33, -27, 20     # pinggang ukulele dalam koordinat pisang, sudut (leher ke kiri-atas)
body = 'M0 0C58-26 66-128 14-176Q2-186-10-176C-17-128-26-50-14-8Q-8 2 0 0Z'
defs.append(f'<path id="bd" d="{body}"/>')
defs.append('<clipPath id="bdc"><use href="#bd"/></clipPath>')
stem = 'M3-178Q2-196-10-206'
add(f'<g transform="translate({BX} {BY}) scale({SC})"><g class="sq">')
add(shadow(f'<use href="#bd" stroke-width="10"/><path d="{stem}" fill="none" stroke-width="20" stroke-linecap="round"/>'))
add(f'<path d="{stem}" fill="none" stroke="{KREM}" stroke-width="20" stroke-linecap="round"/>')
add(f'<use href="#bd" fill="{KUNING}" stroke="{KREM}" stroke-width="10" paint-order="stroke"/>')
# tangkai hijau mint + kilau krem (bukan cokelat gelap: di tema gelap tangkai+pangkal tinta terbaca
# sebagai not balok gelap)
add(f'<path d="{stem}" fill="none" stroke="{MINT}" stroke-width="10" stroke-linecap="round"/>'
    f'<path d="M1-184Q0-194-7-201" fill="none" stroke="{KREM}" stroke-opacity=".6" stroke-width="2.6" stroke-linecap="round"/>')
add(f'<g clip-path="url(#bdc)">'
    f'<path d="M14-6C56-36 58-128 20-170" fill="none" stroke="{JERUK}" stroke-opacity=".35" stroke-width="12"/>'
    f'<ellipse cx="-4" cy="-2" rx="12" ry="9" fill="{TINTA}" fill-opacity=".7"/>'
    f'<ellipse cx="6" cy="-180" rx="12" ry="7" fill="{MINT}" fill-opacity=".75"/></g>')
add(f'<path d="M-8-150C-13-118-15-82-11-52" fill="none" stroke="{KREM}" stroke-opacity=".8" stroke-width="5" stroke-linecap="round"/>')
add(f'<g class="eye"><circle cx="4" cy="-118" r="4.6" fill="{TINTA}"/><circle cx="30" cy="-118" r="4.6" fill="{TINTA}"/>'
    f'<circle cx="5.6" cy="-119.6" r="1.6" fill="{KREM}"/><circle cx="31.6" cy="-119.6" r="1.6" fill="{KREM}"/></g>'
    f'<ellipse cx="-5" cy="-106" rx="6.5" ry="4" fill="{PINK}" opacity=".85"/>'
    f'<ellipse cx="39" cy="-106" rx="6.5" ry="4" fill="{PINK}" opacity=".85"/>'
    f'<path d="M11-109Q17-101 23-109" fill="none" stroke="{TINTA}" stroke-width="2.8" stroke-linecap="round"/>')

# ukulele: koordinat lokal sepanjang sumbu x, pinggang di (0,0), leher ke -x
NUT, HEAD = -160, -194
uke_body = ('M-10-24C-2-24 6-40 22-40A40 40 0 0 1 22 40C6 40-2 24-10 24'
            'C-18 24-22 31-30 31A31 31 0 0 1-30-31C-22-31-18-24-10-24Z')
pegs = ''.join(f'<circle cx="{x}" cy="{y}" r="4.6"/>' for x in (-170, -185) for y in (-14, 14))
uke_parts = (f'<path d="{uke_body}"/><rect x="{NUT - 2}" y="-8" width="{-50 - (NUT - 2)}" height="16" rx="4"/>'
             f'<rect x="{HEAD}" y="-11" width="{NUT - HEAD + 4}" height="22" rx="8"/>{pegs}')
add(f'<g transform="translate({UX} {UY}) rotate({UR})">')
add(shadow(f'<g stroke-width="10" stroke-linejoin="round">{uke_parts}</g>'))
add(f'<g fill="{KREM}" stroke="{KREM}" stroke-width="10" stroke-linejoin="round">{uke_parts}</g>')
add(f'<g fill="{JERUK}">{uke_parts}</g><g fill="{KUNING}">{pegs}</g>')
# kilau badan, papan fret, fret, lubang suara, bridge
FRETS = [-145, -131, -118, -106, -95, -85, -76, -68, -61]
add(f'<path d="M30-33A33 33 0 0 1 52 2" fill="none" stroke="{KREM}" stroke-opacity=".7" stroke-width="4" stroke-linecap="round"/>'
    f'<path d="M-50-14A22 22 0 0 1-36-25" fill="none" stroke="{KREM}" stroke-opacity=".7" stroke-width="3.5" stroke-linecap="round"/>'
    f'<rect x="{NUT}" y="-6.5" width="{NUT * -1 - 44}" height="13" rx="2" fill="{TINTA}" fill-opacity=".8"/>'
    f'<path d="{"".join(f"M{x} -6.5v13" for x in FRETS)}" stroke="{KREM}" stroke-opacity=".55" stroke-width="1.3"/>'
    f'<circle cx="-100" cy="0" r="1.8" fill="{KREM}" fill-opacity=".8"/>'
    f'<rect x="{NUT - 2}" y="-7" width="4" height="14" rx="1.5" fill="{KREM}"/>'
    f'<circle cx="-30" cy="0" r="13.5" fill="{KUNING}"/><circle cx="-30" cy="0" r="10.5" fill="{TINTA}" fill-opacity=".85"/>'
    f'<rect x="24" y="-15" width="10" height="30" rx="4" fill="{TINTA}" fill-opacity=".75"/>'
    f'<path d="M29-11v22" stroke="{KREM}" stroke-width="2" stroke-linecap="round"/>'
    f'<path d="M{HEAD + 8} 0h{NUT - HEAD - 12}" stroke="{TINTA}" stroke-opacity=".35" stroke-width="4" stroke-linecap="round"/>')
strings = ''.join(f'M{NUT} {y}H29' for y in (-4.5, -1.5, 1.5, 4.5))
add(f'<path class="str" d="{strings}" stroke="{KREM}" stroke-width="1.3"/>')
add('</g>')

UC, US = math.cos(math.radians(UR)), math.sin(math.radians(UR))


def u2b(x, y):
    """titik lokal ukulele -> koordinat pisang"""
    return UX + x * UC - y * US, UY + x * US + y * UC


def arm(sx, sy, d, hx, hy, cls, extra=''):
    """lengan pisang lunak: path d (relatif bahu) berujung di tangan (hx,hy) relatif bahu.
    Kuning tebal + outline krem 5px seperti badan, ujung bulat, tangan bulat."""
    return (f'<g transform="translate({sx} {sy})"><g class="{cls}">'
            f'<path d="{d}" fill="none" stroke="{KREM}" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/>{extra}'
            f'<path d="{d}" fill="none" stroke="{KUNING}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="7.5" fill="{KUNING}" stroke="{KREM}" stroke-width="10" paint-order="stroke"/>'
            f'</g></g>')


# tangan kiri (pegang kord) bergeser sepanjang leher sesuai bentuk kord
FRET_X = [NUT] + FRETS


def fret_pos(shape):
    fr = [int(c) for c in shape if c.isdigit() and c != '0']
    p = sum(fr) / len(fr) if fr else 1
    i = min(int(p), 8)
    return FRET_X[i - 1] + (FRET_X[i] - FRET_X[i - 1]) * (p - i + .5)


def string_pos(shape):
    """rata-rata indeks senar yang ditekan (0=G .. 3=A), untuk geser kecil melintang leher."""
    ix = [k for k, c in enumerate(shape) if c.isdigit() and c != '0']
    return sum(ix) / len(ix) if ix else 1.5


REST = '0003'                # posisi tangan kalau tidak ada kord (atau bentuk kord tidak dikenal)
SHAPE0 = SHAPES.get(seq[0][0], REST) if HAS_CHORDS else REST
base = fret_pos(SHAPE0)
sbase = string_pos(SHAPE0)
lsx, lsy, rsx, rsy = -19, -86, 49, -86
# lengan kiri: melengkung lembut, sedikit melendut ke bawah
fx, fy = u2b(base, -5)
fx, fy = fx - lsx, fy - lsy
add(arm(lsx, lsy, f'M0 0C{fx * .3:.1f} 15 {fx * .72:.1f} {fy + 15:.1f} {fx:.1f} {fy:.1f}', fx, fy, 'fh'))
# tangan kanan genjreng di ujung papan fret + pick
pick = (f'<path d="M{u2b(-40, 6)[0] - rsx:.1f} {u2b(-40, 6)[1] - rsy:.1f}l-4-8h9z" fill="{PINK}" stroke="{KREM}" '
        'stroke-width="5" stroke-linejoin="round" paint-order="stroke"/>')
# lengan kanan: lengan atas turun di sisi badan, siku tertekuk, lengan bawah ke arah lubang suara
hx, hy = u2b(-40, -1)
hx, hy = hx - rsx, hy - rsy
ex, ey = 9, hy * .9                                  # siku
add(arm(rsx, rsy, f'M0 0C14 8 {ex + 12:.1f} {ey - 14:.1f} {ex:.1f} {ey:.1f}'
                  f'S{hx * .55:.1f} {hy + 4:.1f} {hx:.1f} {hy:.1f}', hx, hy, 'st', pick))
add('</g></g>')

if HAS_CHORDS:
    kf = []
    for c, s, e in seq:
        shape = SHAPES.get(c, SHAPE0)
        off = (fret_pos(shape) - base) * .75
        cross = (string_pos(shape) - sbase) * 2.5
        v = f'translate({off * UC - cross * US:.1f}px,{off * US + cross * UC:.1f}px)'
        kf.append(f'{pct(s)}{{transform:{v}}}')
        kf.append(f'{pct(max(s, e - .25))}{{transform:{v}}}')
    kf.append(f'100%{{transform:none}}')
    css.append(f".fh{{animation:fh {LOOP:.2f}s ease-in-out infinite}}@keyframes fh{{{''.join(kf)}}}")
css.append(
    f".sq{{animation:sq {BEAT}s ease-out infinite}}"
    "@keyframes sq{0%,100%{transform:none}15%{transform:translateY(2px) scale(1.035,.96)}"
    "36%{transform:translateY(-2px) scale(.985,1.025)}57%{transform:translateY(1px) scale(1.015,.98)}78%{transform:none}}"
    ".eye{animation:blink 3.2s infinite;transform-box:fill-box;transform-origin:50% 50%}"
    "@keyframes blink{0%,46%,50%,100%{transform:scaleY(1)}48%{transform:scaleY(.1)}}"
    f".st{{animation:st {BEAT}s infinite}}"
    "@keyframes st{0%,6%{transform:rotate(11deg);animation-timing-function:ease-in}24%,48%{transform:rotate(-12deg);"
    "animation-timing-function:ease-in}66%,100%{transform:rotate(11deg)}}"
    f".str{{animation:vb {BEAT}s linear infinite}}"
    "@keyframes vb{0%,14%,56%{stroke-width:1.3;stroke-opacity:1}17%,59%{stroke-width:2.6;stroke-opacity:.7}"
    "21%,63%{stroke-width:1.1;stroke-opacity:1}25%,67%{stroke-width:2;stroke-opacity:.8}32%,74%,100%{stroke-width:1.3;stroke-opacity:1}}")

# ---------------------------------------------------------------- kartu kord (gelembung bicara)
if HAS_CHORDS:
    CX, CY, CW, CHT = 646, 14, 92, 106
    SX = [-19.5, -6.5, 6.5, 19.5]     # senar G C E A
    NY, FS = 56, 11                    # garis nut + jarak fret
    card = (f'<rect x="{-CW / 2}" y="0" width="{CW}" height="{CHT}" rx="16"/>'
            f'<path d="M{CW / 2 - 6} 58L{CW / 2 + 20} 80L{CW / 2 - 6} 78Z"/>')
    add(f'<g transform="translate({CX} {CY}) rotate(-4 0 {CHT / 2})"><g class="cd">')
    add(shadow(f'<g stroke-width="12" stroke-linejoin="round">{card}</g>'))
    add(f'<g fill="{KREM}" stroke="{KREM}" stroke-width="16" stroke-linejoin="round">{card}</g>'
        f'<g fill="{KREM}" stroke="{ANGGUR}" stroke-width="5" stroke-linejoin="round">{card}</g><g fill="{KREM}">{card}</g>')
    grid = ''.join(f'M{x} {NY}v{4 * FS}' for x in SX) + ''.join(f'M{SX[0]} {NY + k * FS}H{SX[-1]}' for k in range(1, 5))
    add(f'<path d="{grid}" stroke="{TINTA}" stroke-opacity=".55" stroke-width="1.5" stroke-linecap="round"/>'
        f'<path d="M{SX[0] - 1} {NY}H{SX[-1] + 1}" stroke="{TINTA}" stroke-width="4" stroke-linecap="round"/>')
    names = list(dict.fromkeys(c for c, _, _ in seq))
    for gi, c in enumerate(names):
        # bentuk tidak dikenal atau di atas fret 4 (di luar diagram): nama kord saja
        shape = SHAPES.get(c, '')
        if not all(f_ in '01234x' for f_ in shape):
            shape = ''
        dots = ''.join(f'<circle cx="{SX[k]}" cy="{NY + (int(f_) - .5) * FS}" r="4.6"/>'
                       for k, f_ in enumerate(shape) if f_.isdigit() and f_ != '0')
        opens = ''.join(f'<circle cx="{SX[k]}" cy="{NY - 7}" r="2.8"/>' for k, f_ in enumerate(shape) if f_ == '0')
        muted = ''.join(f'<path d="M{SX[k] - 3} {NY - 10}l6 6m0-6l-6 6"/>' for k, f_ in enumerate(shape) if f_ == 'x')
        cfs = fit(c, CW - 12, 31, 12)               # nama panjang (mis. "F#m7b5") mengecil
        size = f' font-size="{num(cfs)}"' if cfs < 31 else ''
        add(f'<g class="ch c{gi}"><text x="0" y="40"{size}>{esc(c)}</text>'
            f'<g fill="{ANGGUR}">{dots}</g><g fill="none" stroke="{TINTA}" stroke-width="1.6">{opens}{muted}</g></g>')
        kf, vis = [], None
        for c2, s, e in seq:
            v = 1 if c2 == c else 0
            if v != vis:
                kf.append(f'{pct(s)}{{opacity:{v}}}')
                vis = v
        kf.append(f'100%{{opacity:{vis}}}')
        css.append(f".c{gi}{{animation:c{gi} {LOOP:.2f}s step-end infinite}}@keyframes c{gi}{{{''.join(kf)}}}")
    add('</g></g>')
    css.append(
        ".ch{opacity:0}.c0{opacity:1}"
        ".ch text{font-family:'Arial Rounded MT Bold','Nunito','Varela Round','Trebuchet MS','Segoe UI',sans-serif;"
        f"font-weight:800;font-size:31px;text-anchor:middle;fill:{TINTA}}}"
        f".cd{{animation:cd {BEAT * 2:.2f}s ease-in-out infinite alternate}}"
        "@keyframes cd{0%{transform:translateY(0) rotate(0)}100%{transform:translateY(-4px) rotate(1.5deg)}}")

# ---------------------------------------------------------------- not balok melayang (tiap genjrengan)
defs.append('<g id="n1"><ellipse cx="0" cy="0" rx="7.5" ry="5.8" transform="rotate(-22)"/>'
            '<rect x="4.2" y="-27" width="3.6" height="27" rx="1.5"/>'
            '<path d="M4.2-27q12 3 11 16q-3-8-11-9z"/></g>')
defs.append('<g id="n2"><ellipse cx="0" cy="0" rx="7" ry="5.4" transform="rotate(-22)"/>'
            '<ellipse cx="20" cy="-5" rx="7" ry="5.4" transform="rotate(-22 20 -5)"/>'
            '<rect x="3.8" y="-25" width="3.4" height="25" rx="1.5"/><rect x="23.8" y="-30" width="3.4" height="25" rx="1.5"/>'
            '<path d="M3.8-25L27.2-30v6L3.8-19z"/></g>')
notes = [  # (bentuk, x, y, warna, dx) -- satu not per genjrengan (setengah ketukan)
    ('n1', 810, 192, ANGGUR, -2), ('n2', 836, 214, PINK, 22),
    ('n1', 822, 178, LANGIT, 46), ('n1', 846, 200, MINT, 2),
]
NDUR = BEAT * 2
for i, (nid, x, y, col, dx) in enumerate(notes):
    add(f'<g transform="translate({x} {y})"><g class="nt nt{i}" style="animation-delay:{BEAT * (.15 + .5 * i):.3f}s">'
        f'<use href="#{nid}" fill="{KREM}" stroke="{KREM}" stroke-width="7" stroke-linejoin="round"/>'
        f'<use href="#{nid}" fill="{col}"/></g></g>')
    # hilang dengan mengecil, bukan memudar: not setengah transparan di tema gelap jadi kusam/gelap
    css.append(f"@keyframes nt{i}{{0%{{transform:translate(0,0) scale(0) rotate(0);opacity:1}}"
               f"12%{{transform:translate({dx * .1:.1f}px,-14px) scale(.85) rotate(1deg)}}"
               f"72%{{transform:translate({dx * .78:.1f}px,-92px) scale(1.1) rotate({6 + 2 * i}deg);opacity:1}}"
               f"100%{{transform:translate({dx}px,-118px) scale(0) rotate({8 + 3 * i}deg);opacity:1}}}}"
               f".nt{i}{{animation:nt{i} {NDUR:.2f}s ease-out infinite both}}")
css.append(".nt{opacity:0}")

css.append("@media (prefers-reduced-motion:reduce){*{animation:none!important}.nt{opacity:0!important}}")

TITLE = ' '.join(GREETING)
DESC = (f'Colourful sticker title "{TITLE}" ; on the right a banana mascot strums a ukulele'
        + (', a chord card shows the current chord' if HAS_CHORDS else '') + ' while music notes float up.')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
       f'<title id="t">{esc(TITLE)}</title><desc id="d">{esc(DESC)}</desc>'
       f'<style>{"".join(css)}</style><defs>{"".join(defs)}</defs>{"".join(out)}</svg>\n')
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(svg)
print(OUT, len(svg.encode()), 'bytes')
