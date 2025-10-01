from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums for validation
class Mood(str, Enum):
    ENERGETIC = "Energetic"
    CHILL = "Chill"
    FOCUSED = "Focused"
    PARTY = "Party"
    RELAXED = "Relaxed"
    WORKOUT = "Workout"
    HAPPY = "Happy"
    MELANCHOLIC = "Melancholic"

class Genre(str, Enum):
    POP = "Pop"
    ROCK = "Rock"
    JAZZ = "Jazz"
    ELECTRONIC = "Electronic"
    HIP_HOP = "Hip-Hop"
    CLASSICAL = "Classical"
    COUNTRY = "Country"
    RNB = "R&B"
    ALL_GENRES = "All Genres"

# Base schemas
class TrackBase(BaseModel):
    id: str
    title: str
    artist: str
    album: str
    album_art: Optional[str] = None
    duration_ms: Optional[int] = None

class AudioFeatures(BaseModel):
    valence: float = Field(..., ge=0.0, le=1.0)
    energy: float = Field(..., ge=0.0, le=1.0)
    danceability: float = Field(..., ge=0.0, le=1.0)
    tempo: float = Field(..., ge=0.0)
    acousticness: float = Field(..., ge=0.0, le=1.0)
    instrumentalness: float = Field(..., ge=0.0, le=1.0)
    liveness: float = Field(..., ge=0.0, le=1.0)
    speechiness: float = Field(..., ge=0.0, le=1.0)

class Track(TrackBase):
    audio_features: Optional[AudioFeatures] = None
    genres: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

class TrackWithSimilarity(Track):
    similarity_score: float = Field(..., ge=0.0, le=1.0)

# User schemas
class UserBase(BaseModel):
    id: str
    display_name: Optional[str] = None
    email: Optional[str] = None

class User(UserBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserProfile(User):
    top_tracks: List[Track] = []
    saved_tracks: List[Track] = []
    total_tracks: int = 0

# Playlist schemas
class PlaylistGenerateRequest(BaseModel):
    mood: Mood
    genre: Optional[Genre] = Genre.ALL_GENRES
    playlist_length: int = Field(..., ge=5, le=50)
    seed_track_id: Optional[str] = None
    playlist_name: Optional[str] = None

    @validator('playlist_length')
    def validate_playlist_length(cls, v):
        if v < 5 or v > 50:
            raise ValueError('Playlist length must be between 5 and 50 songs')
        return v

class PlaylistBase(BaseModel):
    id: str
    name: str
    mood: Mood
    genre: Optional[Genre]
    length: int
    seed_track_id: Optional[str]
    created_at: datetime

class Playlist(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    mood: str
    genre: Optional[str]
    playlist_length: int
    seed_track_id: Optional[str]
    generated_at: str
    metrics: Optional[Dict[str, Any]] = None
    tracks: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class PlaylistResponse(BaseModel):
    playlist: Playlist
    total_tracks_found: int
    requested_length: int
    message: Optional[str] = None

# Authentication schemas
class SpotifyAuthRequest(BaseModel):
    redirect_uri: Optional[str] = None

class SpotifyAuthResponse(BaseModel):
    auth_url: str
    state: str

class SpotifyCallbackResponse(BaseModel):
    success: bool
    message: str
    user_id: int
    display_name: str
    access_token: str
    expires_at: str

# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Analytics schemas
class ModelPerformanceMetrics(BaseModel):
    average_similarity_score: float
    genre_matching_accuracy: float
    mood_matching_accuracy: float
    total_recommendations_generated: int
    cache_hit_rate: float

class SystemMetrics(BaseModel):
    api_response_time_avg: float
    error_rate: float
    active_users: int
    total_playlists_generated: int

class RecommendationQuality(BaseModel):
    playlist_id: int
    playlist_name: str
    mood: str
    genre: Optional[str]
    playlist_length: int
    internal_similarity: float
    genre_accuracy: float
    mood_consistency: float
    average_similarity: float
    tracks_found: int
    requested_length: int
    generated_at: str

class AnalyticsMetrics(BaseModel):
    user_id: int
    display_name: str
    total_tracks: int
    top_tracks_count: int
    saved_tracks_count: int
    total_playlists: int
    average_playlist_length: float
    average_quality_score: float
    top_moods: List[tuple]
    top_genres: List[tuple]
    recent_activity: List[Dict[str, Any]]

# Cache schemas
class CacheEntry(BaseModel):
    key: str
    value: Dict[str, Any]
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
