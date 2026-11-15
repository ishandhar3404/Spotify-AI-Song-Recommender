from collections import defaultdict
from itertools import combinations


def discovery_matches(seeds, pool):
    """Find other artists connected to seed artists by observed recording credits."""
    credits = defaultdict(dict)
    for song in pool.values():
        for left, right in combinations(dict.fromkeys(song["artists"]), 2):
            credits[left].setdefault(right, song["name"])
            credits[right].setdefault(left, song["name"])

    excluded = {s["id"] for s in seeds}
    primary = {s["artists"][0] for s in seeds if s["artists"]}
    matches = []
    for song in pool.values():
        if song["id"] in excluded or not song["artists"] or song["artists"][0] in primary:
            continue
        artist = song["artists"][0]
        connections = []
        for seed in seeds:
            for source in seed["artists"]:
                if artist in credits[source]:
                    connections.append((seed["id"], f'{artist} and {source} both appear on {credits[source][artist]}'))
                else:
                    for bridge in credits[source].keys() & credits[artist].keys():
                        connections.append((seed["id"], f'{source} worked with {bridge} on {credits[source][bridge]}; {artist} worked with {bridge} on {credits[artist][bridge]}'))
        if connections:
            direct = any(artist in credits[source] for seed in seeds for source in seed["artists"])
            gap = min(abs((song.get("duration_ms") or 0) - (s.get("duration_ms") or 0)) for s in seeds)
            score = (-len({key for key, _ in connections}), not direct, gap, song["id"])
            matches.append((score, dict(song, reason=min(reason for _, reason in connections))))
    return [song for _, song in sorted(matches)]
