#!/usr/bin/env python3
"""Generator assets/music.svg (lihat STYLE.md).

    python3 tools/music.py [assets/music.svg] [--config tape.toml]

Kaset stiker berlabel [tape] label (side + lama lagu), not melayang, equalizer kecil,
tombol play berdenyut, dan [tape] caption di kanan. Teks panjang mengecil sendiri.
Animasi dan gaya stiker sama persis dengan versi tulisan tangan sebelumnya.
"""
import os
import sys
from string import Template

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tapecfg import ROOT, load  # noqa: E402
from textfit import SLACK, args, esc, fit, width  # noqa: E402

TEMPLATE = Template('''\
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="170" viewBox="0 0 900 170" role="img" aria-labelledby="mu-title mu-desc">
  <title id="mu-title">$title</title>
  <desc id="mu-desc">$desc</desc>
  <defs>
    <!-- not: tanpa atribut fill/stroke supaya diwarisi dari <use> -->
    <g id="n1">
      <ellipse cx="0" cy="0" rx="8.5" ry="6.5" transform="rotate(-22)"/>
      <rect x="4.6" y="-27" width="4.2" height="27" rx="2"/>
      <path d="M6.5 -27 C10 -20 19 -19 17 -8 C15 -13 11 -15 6.5 -16 Z"/>
    </g>
    <g id="n2">
      <ellipse cx="0" cy="0" rx="8" ry="6.2" transform="rotate(-22)"/>
      <ellipse cx="22" cy="-5" rx="8" ry="6.2" transform="rotate(-22 22 -5)"/>
      <rect x="4.4" y="-27" width="4" height="27" rx="2"/>
      <rect x="26.4" y="-32" width="4" height="27" rx="2"/>
      <path d="M4.4 -28 L30.4 -33 L30.4 -26 L4.4 -21 Z"/>
    </g>
    <path id="star" d="M0 -13 C1.6 -4 4 -1.6 13 0 C4 1.6 1.6 4 0 13 C-1.6 4 -4 1.6 -13 0 C-4 -1.6 -1.6 -4 0 -13 Z"/>
    <style>
      .t { font-family: 'Arial Rounded MT Bold', 'Nunito', 'Varela Round', 'Trebuchet MS', 'Segoe UI', sans-serif; font-weight: 800; }
      .s { font-family: 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; }

      .bob { animation: bob 2.6s cubic-bezier(.5,-0.4,.5,1.4) infinite; }
      @keyframes bob {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
      }

      .reel { transform-box: fill-box; transform-origin: center; animation: spin 2.2s linear infinite; }
      .reel.r2 { animation-duration: 1.6s; }
      @keyframes spin { to { transform: rotate(-360deg); } }

      .nt { opacity: 0; animation: rise 3.6s ease-out infinite; }
      .d1 { animation-delay: 0s; }
      .d2 { animation-delay: -0.9s; }
      .d3 { animation-delay: -1.8s; }
      .d4 { animation-delay: -2.7s; }
      /* tanpa opacity setengah: not yang memudar jadi gelap/keruh di tema gelap → muncul dan hilang lewat skala */
      @keyframes rise {
        0% { opacity: 1; transform: translate(0, 18px) rotate(-8deg) scale(0); }
        15% { opacity: 1; transform: translate(4px, 0) rotate(6deg) scale(1); }
        55% { opacity: 1; transform: translate(-4px, -14px) rotate(-6deg) scale(1); }
        80% { opacity: 1; transform: translate(6px, -30px) rotate(8deg) scale(0); }
        80.01%, 100% { opacity: 0; transform: translate(6px, -30px) rotate(8deg) scale(0); }
      }

      .eq { transform-box: fill-box; transform-origin: 50% 100%; animation: eq 1.6s cubic-bezier(.5,-0.4,.5,1.4) infinite; }
      .e2 { animation-duration: 1.9s; animation-delay: -0.5s; }
      .e3 { animation-duration: 1.5s; animation-delay: -1.1s; }
      .e4 { animation-duration: 2.1s; animation-delay: -0.3s; }
      .e5 { animation-duration: 1.7s; animation-delay: -0.8s; }
      @keyframes eq {
        0%, 100% { transform: scaleY(.55); }
        30% { transform: scaleY(1); }
        60% { transform: scaleY(.7); }
        80% { transform: scaleY(.85); }
      }

      .pulse { transform-box: fill-box; transform-origin: center; animation: pulse 2s cubic-bezier(.5,-0.4,.5,1.4) infinite; }
      @keyframes pulse {
        0%, 100% { transform: scale(1); }
        40% { transform: scale(1.08); }
        70% { transform: scale(.97); }
      }
      .halo { transform-box: fill-box; transform-origin: center; animation: halo 2s ease-out infinite; }
      @keyframes halo {
        0% { opacity: 1; transform: scale(1); }
        45% { opacity: .7; }
        80%, 100% { opacity: 0; transform: scale(1.3); }
      }

      .wig { transform-box: fill-box; transform-origin: center; animation: wig 3.4s cubic-bezier(.5,-0.4,.5,1.4) infinite; }
      @keyframes wig {
        0%, 100% { transform: rotate(0deg); }
        50% { transform: rotate(2.5deg) translateY(-2px); }
      }

      .tw { transform-box: fill-box; transform-origin: center; animation: tw 2.4s cubic-bezier(.5,-0.4,.5,1.4) infinite; }
      .tw2 { animation-duration: 3.1s; animation-delay: -1.2s; }
      @keyframes tw {
        0%, 100% { transform: scale(.7) rotate(0deg); }
        50% { transform: scale(1.1) rotate(20deg); }
      }

      @media (prefers-reduced-motion: reduce) {
        .bob, .reel, .eq, .pulse, .halo, .wig, .tw { animation: none; }
        .nt { animation: none; opacity: 1; }
        .halo { opacity: 0; }
      }
    </style>
  </defs>

  <!-- ============ KASET ============ -->
  <g transform="translate(34 26) rotate(-3 145 60)">
    <g class="bob">
      <!-- bayangan -->
      <rect x="4" y="5" width="290" height="122" rx="18" fill="#2B2340" opacity=".35"/>
      <!-- badan -->
      <rect x="0" y="0" width="290" height="122" rx="18" fill="#7B5CFF" stroke="#FFF6E5" stroke-width="5"/>

      <!-- sekrup -->
      <g fill="#FFF6E5" stroke="#2B2340" stroke-width="1.4">
        <circle cx="12" cy="12" r="4"/>
        <circle cx="278" cy="12" r="4"/>
        <circle cx="12" cy="110" r="4"/>
        <circle cx="278" cy="110" r="4"/>
      </g>

      <!-- label krem -->
      <rect x="22" y="10" width="246" height="84" rx="10" fill="#FFF6E5"/>
      <rect x="22" y="58" width="246" height="7" fill="#FF5FA2"/>
      <rect x="22" y="69" width="246" height="7" fill="#FFD23F"/>
      <text x="36" y="$label_y" class="t" font-size="$label_fs" fill="#2B2340">$label</text>
      <text x="37" y="51" class="s" font-size="11.5" font-weight="600" fill="#2B2340" opacity=".8">$sideline</text>
      <!-- sisi $side_comment -->
      <circle cx="246" cy="30" r="12" fill="#FF5FA2"/>
      <text x="246" y="$badge_y" class="t" font-size="$badge_fs" fill="#FFF6E5" text-anchor="middle">$side</text>

      <!-- jendela pita -->
      <rect x="72" y="54" width="146" height="34" rx="17" fill="#2B2340"/>
      <!-- pita tergulung -->
      <circle cx="98" cy="71" r="14" fill="#4CC9F0" opacity=".55"/>
      <rect x="98" y="80" width="94" height="4" fill="#4CC9F0" opacity=".55"/>
      <!-- gulungan kiri -->
      <g class="reel">
        <circle cx="98" cy="71" r="11" fill="#FFF6E5"/>
        <circle cx="98" cy="71" r="4" fill="#2B2340"/>
        <g fill="#2B2340">
          <rect x="96.5" y="61.5" width="3" height="5" rx="1"/>
          <rect x="96.5" y="75.5" width="3" height="5" rx="1"/>
          <rect x="88.5" y="69.5" width="5" height="3" rx="1"/>
          <rect x="102.5" y="69.5" width="5" height="3" rx="1"/>
        </g>
      </g>
      <!-- gulungan kanan -->
      <g class="reel r2">
        <circle cx="192" cy="71" r="11" fill="#FFF6E5"/>
        <circle cx="192" cy="71" r="4" fill="#2B2340"/>
        <g fill="#2B2340">
          <rect x="190.5" y="61.5" width="3" height="5" rx="1"/>
          <rect x="190.5" y="75.5" width="3" height="5" rx="1"/>
          <rect x="182.5" y="69.5" width="5" height="3" rx="1"/>
          <rect x="196.5" y="69.5" width="5" height="3" rx="1"/>
        </g>
      </g>

      <!-- kepala kaset -->
      <path d="M78 122 L90 100 L200 100 L212 122" fill="#FF8A3D" stroke="#FFF6E5" stroke-width="4" stroke-linejoin="round"/>
      <g fill="#FFF6E5" stroke="#2B2340" stroke-width="1.4">
        <circle cx="112" cy="112" r="4.5"/>
        <circle cx="178" cy="112" r="4.5"/>
        <rect x="139" y="106" width="12" height="10" rx="2"/>
      </g>
    </g>
  </g>

  <g transform="translate(398 118) scale(1.15) translate(-398 -118)">
  <!-- ============ NOT MELAYANG ============ -->
  <g transform="translate(350 76)">
    <g class="nt d1">
      <use href="#n1" transform="translate(3 4)" fill="#2B2340" opacity=".35"/>
      <use href="#n1" fill="#FFF6E5" stroke="#FFF6E5" stroke-width="7" stroke-linejoin="round"/>
      <use href="#n1" fill="#FFD23F"/>
    </g>
  </g>
  <g transform="translate(404 76)">
    <g class="nt d2">
      <use href="#n2" transform="translate(3 4)" fill="#2B2340" opacity=".35"/>
      <use href="#n2" fill="#FFF6E5" stroke="#FFF6E5" stroke-width="7" stroke-linejoin="round"/>
      <use href="#n2" fill="#3DDC97"/>
    </g>
  </g>
  <g transform="translate(376 70)">
    <g class="nt d3">
      <use href="#n1" transform="translate(3 4)" fill="#2B2340" opacity=".35"/>
      <use href="#n1" fill="#FFF6E5" stroke="#FFF6E5" stroke-width="7" stroke-linejoin="round"/>
      <use href="#n1" fill="#FF5FA2"/>
    </g>
  </g>
  <g transform="translate(448 76)">
    <g class="nt d4">
      <use href="#n1" transform="translate(3 4)" fill="#2B2340" opacity=".35"/>
      <use href="#n1" fill="#FFF6E5" stroke="#FFF6E5" stroke-width="7" stroke-linejoin="round"/>
      <use href="#n1" fill="#4CC9F0"/>
    </g>
  </g>

  <!-- ============ EQUALIZER ============ -->
  <g class="eq"><rect x="363" y="94" width="12" height="52" rx="6" fill="#2B2340" opacity=".35"/><rect x="360" y="90" width="12" height="52" rx="6" fill="#FF5FA2" stroke="#FFF6E5" stroke-width="4" vector-effect="non-scaling-stroke"/></g>
  <g class="eq e2"><rect x="381" y="94" width="12" height="52" rx="6" fill="#2B2340" opacity=".35"/><rect x="378" y="90" width="12" height="52" rx="6" fill="#FF8A3D" stroke="#FFF6E5" stroke-width="4" vector-effect="non-scaling-stroke"/></g>
  <g class="eq e3"><rect x="399" y="94" width="12" height="52" rx="6" fill="#2B2340" opacity=".35"/><rect x="396" y="90" width="12" height="52" rx="6" fill="#FFD23F" stroke="#FFF6E5" stroke-width="4" vector-effect="non-scaling-stroke"/></g>
  <g class="eq e4"><rect x="417" y="94" width="12" height="52" rx="6" fill="#2B2340" opacity=".35"/><rect x="414" y="90" width="12" height="52" rx="6" fill="#3DDC97" stroke="#FFF6E5" stroke-width="4" vector-effect="non-scaling-stroke"/></g>
  <g class="eq e5"><rect x="435" y="94" width="12" height="52" rx="6" fill="#2B2340" opacity=".35"/><rect x="432" y="90" width="12" height="52" rx="6" fill="#4CC9F0" stroke="#FFF6E5" stroke-width="4" vector-effect="non-scaling-stroke"/></g>
  <!-- lantai equalizer -->
  <rect x="356" y="146" width="94" height="6" rx="3.5" fill="#2B2340" opacity=".35"/>

  </g>

  <g transform="translate(8 0)">
  <!-- ============ TOMBOL PLAY ============ -->
  <g transform="translate(528 84)">
    <circle class="halo" cx="0" cy="0" r="47" fill="none" stroke="#FF5FA2" stroke-width="6"/>
    <g class="pulse">
      <circle cx="4" cy="5" r="46" fill="#2B2340" opacity=".35"/>
      <circle cx="0" cy="0" r="46" fill="#FF5FA2" stroke="#FFF6E5" stroke-width="6"/>
      <path d="M-11 -17 L-11 17 L19 0 Z" fill="#2B2340" stroke="#2B2340" stroke-width="7" stroke-linejoin="round"/>
      <ellipse cx="-20" cy="-24" rx="9" ry="5" transform="rotate(-35 -20 -24)" fill="#FFF6E5" opacity=".55"/>
    </g>
  </g>

  <!-- ============ TULISAN ============ -->
  <g class="wig">
    <g transform="rotate(-4 730 92)">
      <g class="t">
$caption      </g>
    </g>
  </g>

  <!-- bintang kecil -->
  <g transform="translate($star1)">
    <g class="tw">
      <use href="#star" transform="translate(2 3)" fill="#2B2340" opacity=".35"/>
      <use href="#star" fill="#FFD23F" stroke="#FFF6E5" stroke-width="4" stroke-linejoin="round" paint-order="stroke"/>
    </g>
  </g>
  <g transform="translate($star2)">
    <g class="tw tw2">
      <circle cx="1.5" cy="2" r="6" fill="#2B2340" opacity=".35"/>
      <circle r="6" fill="#3DDC97" stroke="#FFF6E5" stroke-width="3.5" paint-order="stroke"/>
    </g>
  </g>
  </g>
</svg>
''')


def num(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


def sentence(s):
    s = s.strip()
    s = s[:1].upper() + s[1:]
    return s if s[-1:] in '.!?…' else s + '.'


def caption_svg(lines):
    """Baris caption: bayangan tinta (+3,+4) lalu teks warna berlapis outline krem.
    Ukuran asli 40/42 px; mengecil bersama kalau ada baris yang terlalu panjang."""
    X, MAXW = 608, 264               # x=608 (di dalam translate(8 0)) .. tepi kanan ~872
    STARS = 27 + 36 + 8              # bintang + titik di ujung baris terpendek
    if len(lines) == 1:
        spec = [(lines[0], 42, 81.9, '#FF8A3D')]                  # tengah tinggi huruf (cap) di y ~82
    else:
        spec = [(lines[0], 40, 57.6, '#4CC9F0'), (lines[1], 42, 105.9, '#FF8A3D')]
    star = min(range(len(spec)), key=lambda i: width(spec[i][0], spec[i][1]))
    s = 1.0
    for i, (text, fs, _, _) in enumerate(spec):
        room = MAXW - (STARS if i == star else 0)
        s = min(s, fit(text, room, fs, 1) / fs)
    out = []
    ends = []
    for text, fs, mid, col in spec:
        size = max(14, int(fs * s * 2) / 2)
        base = round(mid + .36 * size, 1)
        t = esc(text)
        out.append(f'        <text x="611" y="{num(base + 4)}" font-size="{num(size)}" fill="#2B2340" opacity=".35" stroke="#2B2340" '
                   f'stroke-width="6" stroke-linejoin="round" paint-order="stroke">{t}</text>\n'
                   f'        <text x="608" y="{num(base)}" font-size="{num(size)}" fill="{col}" stroke="#FFF6E5" '
                   f'stroke-width="6" stroke-linejoin="round" paint-order="stroke">{t}</text>\n')
        ends.append((X + width(text, size), mid))
    end, mid = ends[star]
    sx = round(min(end + 27, 900 - 8 - 36 - 10))
    return ''.join(out), f'{sx} {round(mid - 13.6)}', f'{sx + 36} {round(mid + 2.4)}'


def main():
    out_path, conf = args(os.path.join(ROOT, 'assets', 'music.svg'))
    cfg = load(conf)
    t = cfg['tape']
    side, length = t['side'], t['length']

    # label kaset: ruang dari x=36 sampai sebelum lencana sisi (x~228)
    label, lfs = t['label'], fit(t['label'], 192, 20, 10)
    while width(label, lfs) * SLACK > 192 and len(label) > 1:
        label = label[:-2].rstrip() + '…'
    bfs = fit(side, 19, 15, 9)                       # huruf sisi di lencana bulat r=12

    caption, star1, star2 = caption_svg(t['caption'])
    title = sentence(' '.join(t['caption']))
    d = int(round(t['duration']))
    if d:
        title += f' A {d}-second recording.' if d < 120 else f' A {round(d / 60)}-minute recording.'
    desc = (f'Retro cassette sticker labelled "{t['label']}" with spinning reels, floating colourful music notes, '
            f'a small bouncing equalizer and a pulsing pink play button that says "{" ".join(t["caption"])}".')

    svg = TEMPLATE.substitute(
        title=esc(title), desc=esc(desc),
        label=esc(label), label_fs=num(lfs), label_y=num(round(27.8 + .36 * lfs, 1)),
        sideline=esc(f'side {side} · {length}' if length else f'side {side}'),
        side=esc(side), side_comment=esc(side.replace('-', '_')),
        badge_fs=num(bfs), badge_y=num(round(30 + .37 * bfs, 1)),
        caption=caption, star1=star1, star2=star2)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(out_path, len(svg.encode()), 'bytes')


if __name__ == '__main__':
    main()
