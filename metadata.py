#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generuj titulok/popis/tagy pre ambient long-form (sablony + rotacia -> variabilita).
Ziadne AI, zadarmo. YouTube algoritmus ma rad konzistentny format + kluc. slova v titulku."""
import random

DUR = {30: "30 Minutes", 45: "45 Minutes", 60: "1 Hour", 90: "90 Minutes", 120: "2 Hours", 180: "3 Hours"}

TITLES = {
    "focus": [
        "Deep Focus Music — {dur} of Ambient for Studying, Concentration & Work",
        "{dur} of Deep Focus — Ambient Study Music to Concentrate & Get Things Done",
        "Ambient Focus Music — {dur} to Study, Work & Code Without Distraction",
        "Deep Work Music — {dur} of Calm Ambient for Flow State & Productivity",
    ],
    "study": [
        "Study Music — {dur} of Calm Ambient Tones to Focus & Memorize",
        "{dur} Study With Me — Gentle Ambient Tones for Deep Learning",
        "Calm Study Music — {dur} of Soft Ambient for Reading & Revision",
        "Ambient Study Tones — {dur} to Concentrate, Read & Remember",
    ],
    "sleep": [
        "Deep Sleep Music — {dur} of Calm Ambient to Fall Asleep Fast",
        "{dur} of Deep Sleep — Dark Ambient to Calm Your Mind & Drift Off",
        "Fall Asleep Fast — {dur} of Soothing Ambient for Insomnia & Relaxation",
        "Sleep Music — {dur} of Gentle Dark Ambient for Deep, Restful Sleep",
    ],
}
DESC = {
    "focus": "Ambient focus music to help you concentrate, study and work in deep flow. "
             "Fully original, no copyright. Press play, keep it in the background, and get into the zone.",
    "study": "Soft ambient study tones to help you read, memorize and learn without distraction. "
             "Fully original, no copyright. Perfect background for study-with-me sessions and revision.",
    "sleep": "Calm, dark ambient music to help you fall asleep fast and sleep deeply through the night. "
             "Fully original, no copyright. Dim the lights, press play and drift off.",
}
TAGS = {
    "focus": ["focusmusic", "studymusic", "ambient", "deepfocus", "concentration", "studywithme", "deepwork"],
    "study": ["studymusic", "ambient", "studywithme", "focus", "calm", "studytones", "revision"],
    "sleep": ["sleepmusic", "deepsleep", "ambient", "relaxing", "calm", "insomnia", "sleep"],
}


def make(niche, minutes, seed=None):
    r = random.Random(seed)
    dur = DUR.get(int(minutes), f"{int(minutes)} Minutes")
    title = r.choice(TITLES[niche]).format(dur=dur)
    tags = TAGS[niche]
    desc = DESC[niche] + "\n\n" + " ".join("#" + t for t in tags)
    return {"title": title[:100], "description": desc[:4900], "tags": tags}


if __name__ == "__main__":
    import sys, json
    n = sys.argv[1] if len(sys.argv) > 1 else "focus"
    mins = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    print(json.dumps(make(n, mins), indent=2, ensure_ascii=False))
