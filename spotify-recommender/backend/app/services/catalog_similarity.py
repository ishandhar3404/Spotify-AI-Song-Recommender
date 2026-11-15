import math
import requests
from fastapi import HTTPException

FEATURES = ("valence", "energy", "danceability", "acousticness", "instrumentalness", "speechiness")


def feature_profiles(ids):
    profiles = {}
    ids = list(dict.fromkeys(ids))
    try:
        for start in range(0, len(ids), 40):
            response = requests.get("https://api.reccobeats.com/v1/audio-features",
                                    params={"ids": ",".join(ids[start:start + 40])}, timeout=8)
            response.raise_for_status()
            for record in response.json()["content"]:
                values = [record.get(name) for name in FEATURES]
                if all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
                    profiles[record["href"].rsplit("/", 1)[-1]] = values
    except (requests.RequestException, KeyError, ValueError):
        raise HTTPException(503, "Audio measurements are temporarily unavailable. Try again shortly.")
    return profiles


def rank_catalog(songs, profiles, seeds):
    missing = [s["name"] for s in seeds if s["id"] not in profiles]
    if missing:
        raise HTTPException(422, "No audio measurements available for " + ", ".join(missing) + ". Choose another liked song.")
    ranked = []
    for song in songs:
        values = profiles.get(song["id"])
        if values is None:
            continue
        differences = [sum((v - profiles[s["id"]][i]) ** 2 for s in seeds) / len(seeds)
                       for i, v in enumerate(values)]
        closest = sorted(range(len(FEATURES)), key=differences.__getitem__)[:2]
        reason = "Closest audio traits: " + " and ".join(FEATURES[i] for i in closest)
        ranked.append((sum(differences), song["id"], dict(song, reason=reason)))
    return [song for _, _, song in sorted(ranked)]
