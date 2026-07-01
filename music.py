#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lumora music engine v3 -- ambient/lo-fi HUDBA v style Minecraft (C418) + jemny beat:
  - PIANO melodia (teply, jemne rozladeny -> nostalgicky Minecraft pocit)
  - akordova PROGRESIA (swell pady) + mäkky BAS
  - jemny LO-FI BEAT (kick/snare/hi-hat) + vinyl crackle  (sleep = bez beatu)
  - REVERB (priestor); kazdy track ina tonina/progresia/tempo
"""
import numpy as np

SR = 48000
MINOR = [0, 2, 3, 5, 7, 8, 10]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
CHORD = {"min": [0, 3, 7], "maj": [0, 4, 7]}
PROGS = [
    [(0, "min"), (8, "maj"), (3, "maj"), (10, "maj")],
    [(0, "min"), (5, "min"), (10, "maj"), (3, "maj")],
    [(0, "min"), (10, "maj"), (8, "maj"), (10, "maj")],
    [(0, "maj"), (9, "min"), (5, "maj"), (7, "maj")],
    [(0, "min"), (3, "maj"), (8, "maj"), (7, "min")],
    [(0, "maj"), (5, "maj"), (9, "min"), (7, "maj")],
]


def _note(root, semis):
    return root * 2.0 ** (semis / 12.0)


def _place(buf, start, sig, pan):
    n = len(buf); i0 = int(start * SR); i1 = min(n, i0 + len(sig))
    if i1 <= i0:
        return
    m = i1 - i0
    buf[i0:i1, 0] += sig[:m] * (1 - pan)
    buf[i0:i1, 1] += sig[:m] * pan


def add_pad(buf, start, dur, freq, amp, pan):
    m = int(dur * SR); tt = np.arange(m) / SR
    env = np.ones(m); ai = min(m, int(1.4 * SR)); ri = min(m, int(2.6 * SR))
    env[:ai] = np.linspace(0, 1, ai) ** 1.5
    if ri < m:
        env[m - ri:] = np.linspace(1, 0, ri) ** 1.5
    w = np.sin(2*np.pi*freq*tt) + 0.4*np.sin(2*np.pi*freq*1.004*tt) + 0.16*np.sin(2*np.pi*2*freq*tt)
    _place(buf, start, w * env * amp, pan)


def add_bass(buf, start, dur, freq, amp):
    m = int(dur * SR); tt = np.arange(m) / SR
    env = np.ones(m); ai = min(m, int(0.02 * SR)); ri = min(m, int(0.45 * SR))
    env[:ai] = np.linspace(0, 1, ai)
    if ri < m:
        env[m - ri:] = np.linspace(1, 0, ri)
    w = np.sin(2*np.pi*freq*tt) + 0.12*np.sin(2*np.pi*2*freq*tt)
    _place(buf, start, w * env * amp, 0.5)


def _piano(freq, tt):                                    # teply piano (mierna inharmonicita)
    w = np.zeros_like(tt)
    for k, a in [(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.17), (5, 0.1), (6, 0.05)]:
        w += a * np.sin(2 * np.pi * freq * k * (1 + 0.0007 * k * k) * tt)
    return w


def add_lead(buf, start, dur, freq, amp, pan):
    m = int(dur * SR); tt = np.arange(m) / SR
    env = np.exp(-tt / (dur * 0.45)) * (1 - np.exp(-tt / 0.003))
    w = _piano(freq, tt) * 0.6 + _piano(freq * 1.003, tt) * 0.4   # detune layer = Minecraft teplo
    _place(buf, start, w * env * amp, pan)


def add_kick(buf, start, amp=0.26):
    m = int(0.28 * SR); tt = np.arange(m) / SR
    f = 45 + 55 * np.exp(-tt / 0.03)                     # pitch drop
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-tt / 0.15) * (1 - np.exp(-tt / 0.001))
    _place(buf, start, np.sin(ph) * env * amp, 0.5)


def add_snare(buf, start, rng, amp=0.11):
    m = int(0.16 * SR); tt = np.arange(m) / SR
    sig = (rng.standard_normal(m) * 0.7 + np.sin(2*np.pi*185*tt) * 0.3) * np.exp(-tt / 0.08) * amp
    _place(buf, start, sig, 0.5)


def add_hat(buf, start, rng, amp=0.05):
    m = int(0.05 * SR); tt = np.arange(m) / SR
    nz = rng.standard_normal(m); nz -= np.convolve(nz, np.ones(8)/8, mode="same")   # brighten
    _place(buf, start, nz * np.exp(-tt / 0.018) * amp, rng.uniform(0.4, 0.6))


def _reverb(buf, mix=0.3):
    taps = [0.043, 0.071, 0.097, 0.131, 0.167, 0.211, 0.27, 0.34, 0.41]
    n = len(buf); wetL = np.zeros(n); wetR = np.zeros(n); g = 0.7
    for d in taps:
        sL = int(d*SR); sR = int(d*1.03*SR)
        if sL < n:
            wetL[sL:] += buf[:n-sL, 0] * g
        if sR < n:
            wetR[sR:] += buf[:n-sR, 1] * g
        g *= 0.72
    out = buf.copy()
    out[:, 0] = buf[:, 0]*(1-mix) + wetL*mix
    out[:, 1] = buf[:, 1]*(1-mix) + wetR*mix
    return out


def compose(seconds, seed=0, niche="focus", beat=None, fin=2.5, fout=5.0):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR); buf = np.zeros((n, 2))
    root_hz = _note(440.0, int(rng.integers(-21, -9)))
    if niche == "sleep":
        prog = PROGS[rng.choice([0, 1, 2, 4])]; bpm = rng.uniform(60, 70); mel_p = 0.4; lead_amp = 0.12; hb = False
    elif niche == "study":
        prog = PROGS[rng.integers(len(PROGS))]; bpm = rng.uniform(72, 82); mel_p = 0.58; lead_amp = 0.15; hb = True
    else:
        prog = PROGS[rng.integers(len(PROGS))]; bpm = rng.uniform(74, 86); mel_p = 0.6; lead_amp = 0.16; hb = True
    if beat is not None:
        hb = beat
    elif niche != "sleep":
        hb = rng.random() < 0.75
    scale = MAJOR if prog[0][1] == "maj" else MINOR
    bt = 60.0 / bpm; bar = 4 * bt; clen = 2 * bar
    crackle = hb and rng.random() < 0.7
    t = 0.0; ci = 0
    while t < seconds:
        croot, qual = prog[ci % len(prog)]
        for s in CHORD[qual]:
            add_pad(buf, t, clen + 2.6, _note(root_hz, croot + s + 12), 0.12, rng.uniform(0.4, 0.6))
        for b in range(2):
            add_bass(buf, t + b * bar, bar * 0.92, _note(root_hz, croot), 0.15)
        nb = int(round(clen / bt))
        if hb:
            for k in range(nb):
                if k % 4 == 0:
                    add_kick(buf, t + k * bt)
                if k % 4 == 2:
                    add_snare(buf, t + k * bt, rng)
            for h in range(int(round(clen / (bt / 2)))):
                if rng.random() < 0.9:
                    add_hat(buf, t + h * (bt / 2), rng, 0.05 * rng.uniform(0.6, 1.0))
        deg = int(rng.integers(0, len(scale)))
        for k in range(nb):
            if rng.random() < mel_p:
                semi = croot + int(rng.choice(CHORD[qual])) if rng.random() < 0.55 else int(scale[deg % len(scale)])
                octv = 24 + (12 if rng.random() < 0.18 else 0)
                add_lead(buf, t + k * bt, bt * rng.uniform(1.4, 2.6), _note(root_hz, semi + octv), lead_amp, rng.uniform(0.3, 0.7))
            deg += int(rng.choice([-2, -1, -1, 1, 1, 2]))
        t += clen; ci += 1
    air = rng.standard_normal(n); air -= np.convolve(air, np.ones(64)/64, mode="same"); air /= (np.max(np.abs(air)) + 1e-9)
    buf[:, 0] += air * 0.01; buf[:, 1] += np.roll(air, 211) * 0.01
    if crackle:                                          # jemny vinyl crackle (lo-fi)
        cr = (rng.random(n) < 0.0006) * rng.standard_normal(n) * 0.05
        buf[:, 0] += cr; buf[:, 1] += np.roll(cr, 97)
    buf = _reverb(buf)
    buf /= (np.max(np.abs(buf)) + 1e-9); buf *= 0.92
    fi, fo = int(fin * SR), int(fout * SR); env = np.ones(n)
    env[:fi] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi))
    env[n - fo:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fo))
    return buf * env[:, None]


def write_wav(path, a, sr=SR):
    import wave
    pcm = (np.clip(a, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
