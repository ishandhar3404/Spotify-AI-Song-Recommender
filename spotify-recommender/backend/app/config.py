from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Spotify Playlist Recommender"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI dev server
        "https://your-domain.com"  # Production domain
    ]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./spotify_recommender.db"
    DATABASE_ECHO: bool = False
    
    # Spotify API settings
    SPOTIFY_CLIENT_ID: str = "f1319edcc9204b05aaf7465c1884aad7"
    SPOTIFY_CLIENT_SECRET: str = "8103e017f16b43fabe562fd51d2749ea"
    SPOTIFY_REDIRECT_URI: str = "http://127.0.0.1:8888/callback"
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis settings (for caching)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_ENABLED: bool = False
    
    # ML model settings
    KNN_K: int = 20
    MIN_TRACKS_REQUIRED: int = 20
    MAX_PLAYLIST_LENGTH: int = 50
    MIN_PLAYLIST_LENGTH: int = 5
    
    # Supported moods and genres
    SUPPORTED_MOODS: List[str] = [
        "Energetic", "Chill", "Focused", "Party", 
        "Relaxed", "Workout", "Happy", "Melancholic"
    ]
    
    SUPPORTED_GENRES: List[str] = [
        "Pop", "Rock", "Jazz", "Electronic", 
        "Hip-Hop", "Classical", "Country", "R&B"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

# Load environment variables on import
load_env()
