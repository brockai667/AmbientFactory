#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lull (AmbientFactory) PILOT -- long-form ambient video.
Generovany ambientny zvuk (vrstvene pady + brown noise + fade in/out) + pokojny hypnoticky
vizual (flow-field, Entropy styl) -> mp4 1920x1080 (landscape, long-form YouTube).
Vsetko programovo: 0 copyrightu, ziadne Suno netreba. Skaluje na 1-3h cez ffmpeg -stream_loop.

Pouzitie:  python pilot.py [sekundy]      (default 40)
"""
import os, sys, wave, shutil, subprocess
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output"); os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(ROOT, "temp"); os.makedirs(TMP, exist_ok=True)


def _ffmpeg():
    try:
        import static_ffmpeg; static_ffmpeg.add_paths()
    except Exception:
        pass
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    cand = r"C:\Users\damia\AppData\Local\Programs\Python\Python314\Lib\site-packages\static_ffmpeg\bin\win32\ffmpeg.EXE"
    return cand if os.path.exists(cand) else "ffmpeg"


FF = _ffmpeg()

# ----------------------------- AUDIO ---------------------------------------

def _brown(n, rng):
    """brown (cervene) noise: integraly bieleho sumu -> teply nizkofrekvencny sustek (more/dazd)."""
    b = np.cumsum(rng.standard_normal(n))
    b -= np.linspace(b[0], b[-1], n)            # odstran DC drift
    return b / (np.max(np.abs(b)) + 1e-9)


def _air(n, rng):
    """vzdusny sum (highpassed biely sum) -> pocutelna 'vzduch' textura aj na malych repro."""
    w = rng.standard_normal(n)
    w -= np.convolve(w, np.ones(48) / 48, mode="same")   # odober nizke -> ostane vzduch
    return w / (np.max(np.abs(w)) + 1e-9)


def _pads(t, key, phase):
    """teply, ale JASNY dron v pocutelnom strednom pasme (male repro nezahraju hlboky bas).
    root+kvinta+oktava+duodecima+2.okt+nona (add9 sus = upokojujuce)."""
    voices = [(1.0, 0.22), (1.5, 0.18), (2.0, 0.18), (3.0, 0.13), (4.0, 0.10), (2.25, 0.07)]
    sig = np.zeros_like(t)
    for i, (r, a) in enumerate(voices):
        f = key * r
        lfo = 0.55 + 0.45 * np.sin(2 * np.pi * t / (15.0 + 5 * i) + phase + i * 0.7)  # pomale dychanie
        v = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t + 0.3)  # jemny detune chorus
        sig += a * lfo * v
    return sig


def ambient_audio(seconds, sr=48000, key=196.0, seed=7, fin=3.0, fout=5.0):
    """key=196 Hz (G3) = zaklad v strednom pasme -> POCUT na notebooku aj telefone."""
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    t = np.arange(n) / sr
    shimmer = 0.05 * np.sin(2 * np.pi * key * 6 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 9.0))  # jemny vrch (~1.2kHz)
    nlfoL = 0.6 + 0.4 * np.sin(2 * np.pi * t / 13.0)
    nlfoR = 0.6 + 0.4 * np.sin(2 * np.pi * t / 13.0 + 1.7)
    L = _pads(t, key, 0.0) + shimmer + _brown(n, rng) * 0.06 * nlfoL + _air(n, rng) * 0.04
    R = _pads(t, key, 1.1) + shimmer + _brown(n, rng) * 0.06 * nlfoR + _air(n, rng) * 0.04  # nezavisly sum -> siroke stereo
    a = np.stack([L, R], 1)
    a /= (np.max(np.abs(a)) + 1e-9)
    a = np.tanh(a * 1.7) / np.tanh(1.7)                       # makeup gain: vyssie RMS (mäkke nasycenie)
    a *= 0.92
    fi, fo = int(fin * sr), int(fout * sr)                     # kosinusovy fade in/out
    env = np.ones(n)
    env[:fi] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi))
    env[n - fo:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fo))
    return a * env[:, None]


def write_wav(path, a, sr=48000):
    pcm = (np.clip(a, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())

# ----------------------------- VISUAL --------------------------------------

def _tonemap(canvas, exposure=1.0, bloom=6.0):
    """aditivny canvas -> tonemap (1-exp) + mäkky bloom (downscale blur = rychle) screen-blend."""
    img = 1.0 - np.exp(-np.clip(canvas, 0, None) * exposure)
    u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(u8, "RGB")
    small = im.resize((im.width // 2, im.height // 2), Image.BILINEAR)
    glow = small.filter(ImageFilter.GaussianBlur(radius=bloom / 2)).resize(im.size, Image.BILINEAR)
    A = np.asarray(im, np.float32); B = np.asarray(glow, np.float32)
    out = 255 - (255 - A) * (255 - B) / 255.0
    return np.clip(out, 0, 255).astype(np.uint8)


def flow_field(W, H, fps, duration, n=6500, seed=7):
    """pomaly hypnoticky drift castic v hladkom vektorovom poli (sucet sinusov) + ziarive stopy.
    Chladna upokojujuca paleta (modra/tyrkys/fialova). Castice wrapuju -> plynuly nekonecny pohyb."""
    rng = np.random.default_rng(seed)
    pos = np.stack([rng.uniform(0, W, n), rng.uniform(0, H, n)], 1).astype(np.float64)
    tc = rng.uniform(0, 1, n)
    col = np.clip(np.stack([0.12 + 0.22 * tc, 0.30 + 0.45 * tc, 0.78 - 0.25 * tc], 1), 0.05, 1.0) * 0.5
    canvas = np.zeros((H, W, 3), np.float64)
    nf = int(fps * duration)
    sc = 0.0013; speed = min(W, H) * 0.0013                   # nizka rychlost = pokoj
    for f in range(nf):
        canvas *= 0.94                                        # ziarive doznievajuce stopy
        tt = f / fps
        x = pos[:, 0]; y = pos[:, 1]
        ang = (np.sin(x * sc + 0.5 * np.sin(tt * 0.05))
               + np.cos(y * sc * 1.3 - tt * 0.06)
               + 0.6 * np.sin((x + y) * sc * 0.7 + tt * 0.04)) * np.pi
        pos[:, 0] = (x + np.cos(ang) * speed) % W
        pos[:, 1] = (y + np.sin(ang) * speed) % H
        xi = pos[:, 0].astype(np.int32); yi = pos[:, 1].astype(np.int32)
        np.add.at(canvas, (yi, xi), col * 0.55)
        yield _tonemap(canvas)


def _font(sz):
    for p in (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def thumbnail(frame_u8, brand, sub, path):
    im = Image.fromarray(frame_u8, "RGB").resize((1280, 720), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    bw, sw = _font(150), _font(52)
    tw = d.textlength(brand, font=bw)
    d.text(((1280 - tw) / 2, 250), brand, font=bw, fill=(245, 247, 255))
    tw2 = d.textlength(sub, font=sw)
    d.text(((1280 - tw2) / 2, 430), sub, font=sw, fill=(150, 180, 230))
    im.save(path, "JPEG", quality=90)

# ----------------------------- MAIN ----------------------------------------

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "40"
    audio_only = (arg == "audio")                              # rychly listen-test: reuse existujuci vizual
    secs = 40.0 if audio_only else float(arg)
    W, H, fps, seed = 1920, 1080, 30, 7
    brand, sub = "LULL", "deep focus / sleep ambient"
    silent = os.path.join(TMP, "silent.mp4")

    print(f"[1/3] generujem ambientny zvuk ({secs:.0f}s)...")
    wav = os.path.join(TMP, "ambient.wav")
    write_wav(wav, ambient_audio(secs, seed=seed))

    last = None
    if audio_only and os.path.exists(silent):
        print("[2/3] audio-only: preskakujem render, pouzivam existujuci vizual")
    else:
        print(f"[2/3] renderujem vizual {W}x{H}@{fps} ({secs:.0f}s)...")
        cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
               "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        nf = int(fps * secs)
        for i, fr in enumerate(flow_field(W, H, fps, secs, seed=seed)):
            p.stdin.write(fr.tobytes()); last = fr
            if i % 60 == 0:
                print(f"    frame {i}/{nf}")
        p.stdin.close()
        if p.wait() != 0:
            print("CHYBA: render zlyhal"); sys.exit(1)

    print("[3/3] mux zvuk (loudnorm -14 LUFS) + thumbnail...")
    out = os.path.join(OUT, "lull_pilot.mp4")
    r = subprocess.run([FF, "-y", "-i", silent, "-i", wav, "-c:v", "copy", "-map", "0:v", "-map", "1:a",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", out])
    if r.returncode != 0:
        os.replace(silent, out)
    if last is not None:
        thumbnail(last, brand, sub, os.path.join(OUT, "lull_pilot.jpg"))
    meta = ("Lull -- Deep Focus & Sleep Ambient [extend to 1-3 HOURS]\n\n"
            "Calm ambient soundscape for deep focus, studying, work and sleep. "
            "Fully generated -- no copyright.\n\n"
            "#ambient #sleepmusic #studymusic #focusmusic #relaxing #whitenoise #calm #lofi")
    open(os.path.join(OUT, "lull_pilot.txt"), "w", encoding="utf-8").write(meta)
    print("HOTOVO ->", out)


if __name__ == "__main__":
    main()
