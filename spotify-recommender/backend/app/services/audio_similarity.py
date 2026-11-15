import re
import unicodedata

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from math import gcd

LABELS = ["bass balance", "midrange balance", "brightness", "dynamic range", "rhythmic activity"]


def audio_profile(file):
    profiles = []
    with sf.SoundFile(file) as audio:
        rate = audio.samplerate
        if not 8000 <= rate <= 192000 or not 1 <= audio.channels <= 8 or len(audio) < rate * 4:
            raise ValueError("Use a recording at least four seconds long.")
        size = min(len(audio), rate * 12)
        for start in np.linspace(0, len(audio) - size, 5, dtype=int):
            audio.seek(int(start))
            samples = audio.read(size, dtype="float32", always_2d=True).mean(axis=1)
            factor = gcd(rate, 16000)
            mono = resample_poly(samples, 16000 // factor, rate // factor)
            frames = np.lib.stride_tricks.sliding_window_view(mono, 1024)[::256]
            power = abs(np.fft.rfft(frames * np.hanning(1024))) ** 2
            rms = np.sqrt(np.mean(frames ** 2, axis=1))
            if np.max(rms) < 0.0001:
                continue
            spectrum = np.sqrt(power.mean(axis=0))
            bands = np.split(spectrum, [16, 128])
            balance = [band.sum() / spectrum.sum() for band in bands]
            normalized = np.sqrt(power)
            normalized /= normalized.sum(axis=1, keepdims=True) + 1e-9
            flux = np.maximum(np.diff(normalized, axis=0), 0).sum(axis=1)
            dynamics = 1 - np.percentile(rms, 10) / max(np.percentile(rms, 90), 1e-8)
            profiles.append([*balance, dynamics, np.mean(flux)])
    if not profiles:
        raise ValueError("The file contains no measurable audio.")
    return np.median(profiles, axis=0).tolist()


def recording_keys(song):
    def normalize(value):
        return "".join(c for c in unicodedata.normalize("NFKC", value).casefold() if c.isalnum())
    title = re.sub(r"\s*(?:[-–—(\[]\s*)(?:(?:\d{4}\s+)?remaster(?:ed)?|feat\.?|ft\.|explicit|clean|radio edit|album version|single version)\b.*$", "", song["name"], flags=re.I)
    keys = {("id", song["id"]), ("title", normalize(song["artists"][0]), normalize(title))}
    if song.get("isrc"):
        keys.add(("isrc", song["isrc"].upper()))
    if song.get("linked_id"):
        keys.add(("id", song["linked_id"]))
    return keys


def track_info(t):
    return dict(id=t["id"], name=t["name"], artists=[a["name"] for a in t["artists"]],
                album=t["album"]["name"], uri=t["uri"], isrc=(t.get("external_ids") or {}).get("isrc"),
                linked_id=(t.get("linked_from") or {}).get("id"))


def liked_keys(client):
    keys = set()
    page = client.current_user_saved_tracks(limit=50)
    while True:
        for item in page["items"]:
            t = item.get("track")
            if t and t.get("artists") and t.get("name"):
                keys.update(recording_keys(track_info(t)))
        if not page.get("next"):
            return keys
        page = client.next(page)


def rank_audio(catalog, seeds):
    ranked = []
    for song, features in catalog:
        delta = np.mean([np.abs(np.asarray(features) - seed) for seed in seeds], axis=0)
        closest = np.argsort(delta)[:2]
        reason = "Closest measured traits: " + " and ".join(LABELS[i] for i in closest)
        ranked.append((np.linalg.norm(delta), song["id"], dict(song, reason=reason)))
    return [song for _, _, song in sorted(ranked)]
