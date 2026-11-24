#!/usr/bin/env python3
"""Master a phone recording for the web.

    python master.py input.wav output.wav

Needs: numpy scipy soundfile noisereduce pyloudnorm
Chain: trim silence -> balance L/R -> denoise (profile from the silent intro)
       -> EQ -> gentle compression -> small room reverb -> -16 LUFS -> peak limit -> fades
"""
import sys

import noisereduce as nr
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal
from scipy.ndimage import minimum_filter1d

src, dst = sys.argv[1], sys.argv[2]
x, sr = sf.read(src, always_2d=True)
x = x[:, :2] if x.shape[1] >= 2 else np.repeat(x, 2, axis=1)

# 1. noise profile from the silent intro, then trim it (keep 0.25 s of lead-in)
mono = x.mean(axis=1)
env = np.convolve(np.abs(mono), np.ones(int(0.05 * sr)) / int(0.05 * sr), "same")
start = int(np.argmax(env > 10 ** (-40 / 20)))
noise_clip = x[: max(start - int(0.2 * sr), int(0.5 * sr))]
x = x[max(0, start - int(0.25 * sr)):]

# 2. balance channels to equal RMS
rms = np.sqrt((x ** 2).mean(axis=0))
x = x * (rms.mean() / rms)

# 3. light stationary denoise using the intro as profile
x = np.stack([nr.reduce_noise(y=x[:, c], sr=sr, y_noise=noise_clip[:, c], stationary=True,
                              prop_decrease=0.6, n_fft=2048) for c in range(2)], axis=1)


# 4. EQ (RBJ biquads)
def biquad(kind, f0, gain_db=0.0, q=0.707):
    a = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / sr
    cw, sw = np.cos(w), np.sin(w)
    al = sw / (2 * q)
    if kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        aa = [1 + al, -2 * cw, 1 - al]
    elif kind == "peak":
        b = [1 + al * a, -2 * cw, 1 - al * a]
        aa = [1 + al / a, -2 * cw, 1 - al / a]
    elif kind == "hs":
        s = 2 * np.sqrt(a) * al
        b = [a * ((a + 1) + (a - 1) * cw + s), -2 * a * ((a - 1) + (a + 1) * cw), a * ((a + 1) + (a - 1) * cw - s)]
        aa = [(a + 1) - (a - 1) * cw + s, 2 * ((a - 1) - (a + 1) * cw), (a + 1) - (a - 1) * cw - s]
    return np.array(b) / aa[0], np.array(aa) / aa[0]


for kind, f0, g, q in [
    ("hp", 40, 0, 0.707),      # rumble
    ("peak", 320, -3.0, 0.8),  # boxy/muddy build-up
    ("peak", 2500, 3.0, 0.9),  # clarity
    ("hs", 6000, 4.0, 0.707),  # air the phone lost
]:
    b, a = biquad(kind, f0, g, q)
    x = signal.lfilter(b, a, x, axis=0)
b, a = signal.butter(2, 14000 / (sr / 2))  # stop the shelf from lifting codec hiss
x = signal.lfilter(b, a, x, axis=0)

# 5. gentle compression (feed-forward, RMS detector, 2:1 above -26 dBFS)
det = np.sqrt(signal.lfilter([1 - np.exp(-1 / (0.03 * sr))], [1, -np.exp(-1 / (0.03 * sr))], (x ** 2).mean(axis=1)))
lvl = 20 * np.log10(det + 1e-9)
gr = np.minimum(0, (-26 - lvl) * (1 - 1 / 2))
gr = signal.lfilter([1 - np.exp(-1 / (0.15 * sr))], [1, -np.exp(-1 / (0.15 * sr))], gr)  # smooth release
x = x * (10 ** (gr / 20))[:, None]

# 6. small room reverb: decaying noise impulse, decorrelated per channel, 12% wet
rng = np.random.default_rng(1)
n = int(0.9 * sr)
t = np.arange(n) / sr
ir = rng.standard_normal((n, 2)) * np.exp(-t / 0.28)[:, None]
b, a = signal.butter(2, 5000 / (sr / 2))
ir = signal.lfilter(b, a, ir, axis=0)
ir[: int(0.012 * sr)] = 0  # predelay
ir /= np.sqrt((ir ** 2).sum(axis=0))
wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
x = 0.88 * x + 0.12 * wet * (np.sqrt((x ** 2).mean()) / (np.sqrt((wet ** 2).mean()) + 1e-12))

# 7. loudness to -16 LUFS, then lookahead peak limiter at -1 dBFS
meter = pyln.Meter(sr)
x = pyln.normalize.loudness(x, meter.integrated_loudness(x), -16.0)
ceil = 10 ** (-1 / 20)
peak = np.abs(x).max(axis=1)
need = np.minimum(1, ceil / (peak + 1e-12))
look = int(0.005 * sr)
# sliding-window minimum over the lookahead, then smooth release
gain = minimum_filter1d(need, size=2 * look + 1)
rel = np.exp(-1 / (0.08 * sr))
g = np.empty_like(gain)
cur = 1.0
for i, v in enumerate(gain):
    cur = v if v < cur else rel * cur + (1 - rel) * v
    g[i] = cur
x = x * g[:, None]
x = np.clip(x, -ceil, ceil)

# 8. fades: 30 ms in, 2.5 s out (the recording stops mid-phrase)
fi, fo = int(0.03 * sr), int(2.5 * sr)
x[:fi] *= np.linspace(0, 1, fi)[:, None]
x[-fo:] *= (np.cos(np.linspace(0, np.pi, fo)) * 0.5 + 0.5)[:, None]

sf.write(dst, x, sr, subtype="PCM_24")
print(f"{dst}: {len(x) / sr:.1f}s, {meter.integrated_loudness(x):.1f} LUFS, peak {20 * np.log10(np.abs(x).max()):.2f} dBFS, "
      f"gain reduction max {-gr.min():.1f} dB, limiter max {-20 * np.log10(g.min()):.1f} dB")
