import hmac
import json
from uuid import uuid4

import spotipy
from fastapi import UploadFile, File, APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import Playlist, PlaylistTrack, User, get_db
from ..services.audio_similarity import audio_profile, liked_keys, rank_audio, recording_keys, track_info
from ..services.catalog_similarity import feature_profiles, rank_catalog
from ..database import AudioRecording

router = APIRouter()


class SongMix(BaseModel):
    seeds: list[str] = Field(min_length=1, max_length=5)
    length: int = Field(default=20, ge=1, le=50)


def authenticated(request, db):
    user = db.get(User, request.headers.get("X-User-ID", ""))
    if not user or not user.access_token or not hmac.compare_digest(
        request.headers.get("Authorization", ""), "Bearer " + user.access_token
    ):
        raise HTTPException(401, "Reconnect Spotify to build a mix.")
    return user


@router.get("/audio-catalog")
def audio_catalog(request: Request, db: Session = Depends(get_db)):
    user = authenticated(request, db)
    rows = db.query(AudioRecording).filter_by(user_id=user.id).all()
    return {"tracks": [json.loads(r.metadata_json) for r in rows]}


@router.post("/audio-catalog/{track_id}")
def index_recording(track_id: str, request: Request, audio: UploadFile = File(...), db: Session = Depends(get_db)):
    user = authenticated(request, db)
    import re
    if not re.fullmatch(r"[A-Za-z0-9]{22}", track_id):
        raise HTTPException(400, "Enter a Spotify track link.")
    try:
        features = audio_profile(audio.file)
    except (ValueError, RuntimeError):
        raise HTTPException(422, "Use a readable MP3, FLAC or WAV containing at least four seconds of music.")
    client = spotipy.Spotify(auth=user.access_token, retries=0, requests_timeout=5)
    try:
        song = track_info(client.track(track_id))
    except (spotipy.SpotifyException, OSError):
        raise HTTPException(502, "Spotify could not verify this track. Check the link and reconnect if needed.")
    db.merge(AudioRecording(user_id=user.id, track_id=song["id"], metadata_json=json.dumps(song),
                            features_json=json.dumps(features)))
    db.commit()
    return song


def saved_songs(client):
    songs = []
    try:
        page = client.current_user_saved_tracks(limit=50)
        while True:
            for entry in page["items"]:
                t = entry.get("track")
                if t and t.get("id") and t.get("artists"):
                    songs.append(track_info(t))
            if not page.get("next"):
                return songs
            page = client.next(page)
    except (spotipy.SpotifyException, OSError) as exc:
        if getattr(exc, "http_status", None) == 401:
            raise HTTPException(401, "Reconnect your Spotify account.")
        raise HTTPException(503, "Spotify could not load your Liked Songs.")


@router.get("/liked-seeds")
def liked_seeds(request: Request, db: Session = Depends(get_db)):
    user = authenticated(request, db)
    return {"tracks": saved_songs(spotipy.Spotify(auth=user.access_token, retries=0, requests_timeout=6))}


@router.post("/song-mix")
def song_mix(data: SongMix, request: Request, db: Session = Depends(get_db)):
    user = authenticated(request, db)
    client = spotipy.Spotify(auth=user.access_token, retries=0, requests_timeout=6)
    saved = saved_songs(client)
    by_id = {s["id"]: s for s in saved}
    if any(i not in by_id for i in data.seeds):
        raise HTTPException(422, "Refresh your Liked Songs and select again.")
    seeds = [by_id[i] for i in dict.fromkeys(data.seeds)]
    excluded = set().union(*(recording_keys(s) for s in saved))
    artists = list(dict.fromkeys([a for s in seeds for a in s["artists"]] +
                                 [s["artists"][0] for s in saved]))
    candidates = {}
    try:
        for artist in artists[:14]:
            results = client.search(q=f'artist:"{artist}"', type="track", limit=10)
            for item in results["tracks"]["items"]:
                if item and item.get("id") and item.get("artists"):
                    song = track_info(item)
                    if recording_keys(song).isdisjoint(excluded):
                        candidates[song["id"]] = song
    except (spotipy.SpotifyException, OSError):
        if not candidates:
            raise HTTPException(503, "Spotify catalog search is temporarily unavailable.")
    profiles = feature_profiles([s["id"] for s in seeds] + list(candidates))
    tracks = []
    for song in rank_catalog(candidates.values(), profiles, seeds):
        keys = recording_keys(song)
        if not keys.isdisjoint(excluded):
            continue
        tracks.append(song)
        excluded.update(keys)
        if len(tracks) == data.length:
            break
    if not tracks:
        raise HTTPException(422, "No unsaved candidates with audio measurements were found. Try another starting song.")
    name = "Mix from " + ", ".join(s["name"] for s in seeds)
    mix = Playlist(id=str(uuid4()), user_id=user.id, name=name, description=name, mood="Song mix",
                   playlist_length=len(tracks), seed_track_id=seeds[0]["id"], metrics=json.dumps({"seeds": data.seeds}))
    db.add(mix)
    for i, song in enumerate(tracks, 1):
        mix.tracks.append(PlaylistTrack(track_id=song["id"], track_name=song["name"],
            artists=", ".join(song["artists"]), album=song["album"], position=i, spotify_uri=song["uri"]))
    db.commit()
    return {"id": mix.id, "tracks": tracks}
