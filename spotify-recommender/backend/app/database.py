from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import json

from .config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)  # Spotify user ID
    display_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    access_token = Column(Text, nullable=True)  # Can be null initially
    refresh_token = Column(Text, nullable=True)  # Can be null initially
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    top_tracks = relationship("Track", secondary="user_top_tracks", back_populates="users")
    saved_tracks = relationship("Track", secondary="user_saved_tracks", back_populates="saved_by_users")
    playlists = relationship("Playlist", back_populates="user")

# Track model
class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(String, primary_key=True, index=True)  # Spotify track ID
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album = Column(String, nullable=False)
    album_art = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    audio_features = Column(Text, nullable=True)  # JSON string
    genres = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    users = relationship("User", secondary="user_top_tracks", back_populates="top_tracks")
    saved_by_users = relationship("User", secondary="user_saved_tracks", back_populates="saved_tracks")
    playlist_tracks = relationship("PlaylistTrack", back_populates="track")
    
    def get_audio_features(self):
        """Get audio features as dictionary"""
        if self.audio_features:
            return json.loads(self.audio_features)
        return {}
    
    def get_genres(self):
        """Get genres as list"""
        if self.genres:
            return json.loads(self.genres)
        return []

# Playlist model
class Playlist(Base):
    __tablename__ = "playlists"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    mood = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    playlist_length = Column(Integer, nullable=False)
    seed_track_id = Column(String, nullable=True)
    generated_at = Column(DateTime, default=func.now())
    metrics = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=func.now())
    
    # Spotify integration fields
    spotify_playlist_id = Column(String, nullable=True)
    spotify_playlist_url = Column(String, nullable=True)
    saved_to_spotify = Column(Boolean, default=False)
    saved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="playlists")
    tracks = relationship("PlaylistTrack", back_populates="playlist")
    
    def get_metrics(self):
        """Get metrics as dictionary"""
        if self.metrics:
            return json.loads(self.metrics)
        return {}

# PlaylistTrack junction table
class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(String, ForeignKey("playlists.id"), nullable=False)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False)
    track_name = Column(String, nullable=False)
    artists = Column(String, nullable=False)
    album = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    spotify_uri = Column(String, nullable=True)
    similarity_score = Column(Integer, nullable=True)  # Store as integer (multiply by 1000)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="tracks")
    track = relationship("Track", back_populates="playlist_tracks")

# User-Track junction tables
class UserTopTrack(Base):
    __tablename__ = "user_top_tracks"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    track_id = Column(String, ForeignKey("tracks.id"), primary_key=True)
    spotify_track_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    artists = Column(String, nullable=False)
    album = Column(String, nullable=False)
    album_id = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    popularity = Column(Integer, nullable=True)
    external_urls = Column(Text, nullable=True)  # JSON string
    uri = Column(String, nullable=True)
    audio_features = Column(Text, nullable=True)  # JSON string
    genres = Column(Text, nullable=True)  # JSON string
    time_range = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    last_played = Column(DateTime, nullable=True)
    added_at = Column(DateTime, default=func.now())

class UserSavedTrack(Base):
    __tablename__ = "user_saved_tracks"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    track_id = Column(String, ForeignKey("tracks.id"), primary_key=True)
    spotify_track_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    artists = Column(String, nullable=False)
    album = Column(String, nullable=False)
    album_id = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    popularity = Column(Integer, nullable=True)
    external_urls = Column(Text, nullable=True)  # JSON string
    uri = Column(String, nullable=True)
    audio_features = Column(Text, nullable=True)  # JSON string
    genres = Column(Text, nullable=True)  # JSON string
    added_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, nullable=True)

# Cache model for storing Spotify data
class Cache(Base):
    __tablename__ = "cache"
    
    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=False)  # JSON string
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    def get_value(self):
        """Get cached value as dictionary"""
        if self.value:
            return json.loads(self.value)
        return {}
    
    def is_expired(self):
        """Check if cache entry is expired"""
        return datetime.utcnow() > self.expires_at
