from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Optional
import logging
import json
from datetime import datetime

from ..schemas import User as UserSchema, Track, AudioFeatures
from ..services.spotify_service import SpotifyService
from ..config import settings
from ..database import get_db, User, UserTopTrack, UserSavedTrack
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Spotify service
spotify_service = SpotifyService(
    client_id=settings.SPOTIFY_CLIENT_ID,
    client_secret=settings.SPOTIFY_CLIENT_SECRET,
    redirect_uri=settings.SPOTIFY_REDIRECT_URI
)

@router.get("/profile", response_model=UserSchema)
async def get_user_profile(request: Request, db: Session = Depends(get_db)):
    """
    Get the current user's profile information.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if token is expired
        if not user.access_token or (user.token_expires_at and user.token_expires_at <= datetime.utcnow()):
            raise HTTPException(status_code=401, detail="Access token expired")
        
        # Get fresh profile from Spotify
        try:
            spotify_profile = spotify_service.get_user_profile(user.access_token)
            
            # Update local profile if needed
            if (user.display_name != spotify_profile['display_name'] or 
                user.email != spotify_profile.get('email')):
                
                user.display_name = spotify_profile['display_name']
                user.email = spotify_profile.get('email')
                
                db.commit()
                logger.info(f"Updated profile for user: {user.display_name}")
            
        except Exception as e:
            logger.warning(f"Failed to fetch fresh profile from Spotify: {str(e)}")
            # Continue with local profile data
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

@router.get("/top-tracks", response_model=List[Track])
async def get_user_top_tracks(
    request: Request,
    limit: int = 50,
    time_range: str = "medium_term",
    db: Session = Depends(get_db)
):
    """
    Get the user's top tracks from Spotify.
    
    Args:
        limit: Number of tracks to retrieve (max 50)
        time_range: Time range for top tracks (short_term, medium_term, long_term)
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if token is expired
        if not user.access_token or (user.token_expires_at and user.token_expires_at <= datetime.utcnow()):
            raise HTTPException(status_code=401, detail="Access token expired")
        
        # Validate parameters
        if limit > 50:
            limit = 50
        elif limit < 1:
            limit = 20
        
        if time_range not in ["short_term", "medium_term", "long_term"]:
            time_range = "medium_term"
        
        # Get top tracks from Spotify
        spotify_tracks = spotify_service.get_user_top_tracks(
            access_token=user.access_token,
            limit=limit,
            time_range=time_range
        )
        
        # Store tracks in database for caching
        for spotify_track in spotify_tracks:
            # Check if track already exists
            existing_track = db.query(UserTopTrack).filter(
                UserTopTrack.user_id == user.id,
                UserTopTrack.spotify_track_id == spotify_track['id']
            ).first()
            
            if existing_track:
                # Update existing track
                existing_track.last_played = datetime.utcnow()
                existing_track.popularity = spotify_track.get('popularity', 0)
                existing_track.audio_features = json.dumps(spotify_track)
            else:
                # Create new track record
                new_track = UserTopTrack(
                    user_id=user.id,
                    track_id=spotify_track['id'],  # Use track_id as primary key
                    spotify_track_id=spotify_track['id'],
                    name=spotify_track['name'],
                    artists=", ".join(spotify_track['artists']),
                    album=spotify_track['album'],
                    album_id=spotify_track.get('album_id'),
                    duration_ms=spotify_track['duration_ms'],
                    popularity=spotify_track.get('popularity', 0),
                    external_urls=json.dumps(spotify_track.get('external_urls', {})),
                    uri=spotify_track['uri'],
                    audio_features=json.dumps(spotify_track),
                    genres=json.dumps(spotify_track.get('genres', [])),
                    time_range=time_range,
                    last_played=datetime.utcnow()
                )
                db.add(new_track)
        
        db.commit()
        logger.info(f"Retrieved and stored {len(spotify_tracks)} top tracks for user {user.display_name}")
        
        return spotify_tracks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user top tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get top tracks")

@router.get("/saved-tracks", response_model=List[Track])
async def get_user_saved_tracks(
    request: Request,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get the user's saved tracks from Spotify.
    
    Args:
        limit: Number of tracks to retrieve (max 50)
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if token is expired
        if not user.access_token or (user.token_expires_at and user.token_expires_at <= datetime.utcnow()):
            raise HTTPException(status_code=401, detail="Access token expired")
        
        # Validate parameters
        if limit > 50:
            limit = 50
        elif limit < 1:
            limit = 20
        
        # Get saved tracks from Spotify
        spotify_tracks = spotify_service.get_user_saved_tracks(
            access_token=user.access_token,
            limit=limit
        )
        
        # Store tracks in database for caching
        for spotify_track in spotify_tracks:
            # Check if track already exists
            existing_track = db.query(UserSavedTrack).filter(
                UserSavedTrack.user_id == user.id,
                UserSavedTrack.spotify_track_id == spotify_track['id']
            ).first()
            
            if existing_track:
                # Update existing track
                existing_track.last_accessed = datetime.utcnow()
                existing_track.popularity = spotify_track.get('popularity', 0)
                existing_track.audio_features = json.dumps(spotify_track)
            else:
                # Create new track record
                new_track = UserSavedTrack(
                    user_id=user.id,
                    track_id=spotify_track['id'],  # Use track_id as primary key
                    spotify_track_id=spotify_track['id'],
                    name=spotify_track['name'],
                    artists=", ".join(spotify_track['artists']),
                    album=spotify_track['album'],
                    album_id=spotify_track.get('album_id'),
                    duration_ms=spotify_track['duration_ms'],
                    popularity=spotify_track.get('popularity', 0),
                    external_urls=json.dumps(spotify_track.get('external_urls', {})),
                    uri=spotify_track['uri'],
                    audio_features=json.dumps(spotify_track),
                    genres=json.dumps(spotify_track.get('genres', [])),
                    added_at=datetime.fromisoformat(spotify_track['added_at'].replace('Z', '+00:00')) if spotify_track.get('added_at') else None,
                    last_accessed=datetime.utcnow()
                )
                db.add(new_track)
        
        db.commit()
        logger.info(f"Retrieved and stored {len(spotify_tracks)} saved tracks for user {user.display_name}")
        
        return spotify_tracks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user saved tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get saved tracks")

@router.get("/tracks")
async def get_user_tracks(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get combined user tracks (top tracks + saved tracks) for dashboard display.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if token is expired
        if not user.access_token or (user.token_expires_at and user.token_expires_at <= datetime.utcnow()):
            raise HTTPException(status_code=401, detail="Access token expired")
        
        # Try to get tracks from database first
        all_tracks = []
        top_tracks_count = 0
        saved_tracks_count = 0
        
        try:
            # Get tracks from database
            db_top_tracks = db.query(UserTopTrack).filter(UserTopTrack.user_id == user.id).all()
            db_saved_tracks = db.query(UserSavedTrack).filter(UserSavedTrack.user_id == user.id).all()
            
            # Convert database tracks to track format
            for track in db_top_tracks:
                all_tracks.append({
                    'id': track.spotify_track_id,
                    'name': track.name,
                    'artists': track.artists.split(", ") if track.artists else [],
                    'album': track.album,
                    'album_images': [],  # We don't store images in DB currently
                    'duration_ms': track.duration_ms,
                    'popularity': track.popularity,
                    'external_urls': json.loads(track.external_urls) if track.external_urls else {},
                    'uri': track.uri,
                    'type': 'top_track'
                })
                top_tracks_count += 1
            
            for track in db_saved_tracks:
                all_tracks.append({
                    'id': track.spotify_track_id,
                    'name': track.name,
                    'artists': track.artists.split(", ") if track.artists else [],
                    'album': track.album,
                    'album_images': [],  # We don't store images in DB currently
                    'duration_ms': track.duration_ms,
                    'popularity': track.popularity,
                    'external_urls': json.loads(track.external_urls) if track.external_urls else {},
                    'uri': track.uri,
                    'added_at': track.added_at.isoformat() if track.added_at else None,
                    'type': 'saved_track'
                })
                saved_tracks_count += 1
            
            logger.info(f"Retrieved {len(all_tracks)} tracks from database for user {user.display_name}")
            
        except Exception as e:
            logger.warning(f"Failed to get tracks from database: {str(e)}")
            
            # Fallback: try to fetch fresh from Spotify
            try:
                top_tracks_response = await get_user_top_tracks(request, limit=50, db=db)
                if isinstance(top_tracks_response, list):
                    all_tracks.extend(top_tracks_response)
                    top_tracks_count = len(top_tracks_response)
                
                saved_tracks_response = await get_user_saved_tracks(request, limit=50, db=db)
                if isinstance(saved_tracks_response, list):
                    all_tracks.extend(saved_tracks_response)
                    saved_tracks_count = len(saved_tracks_response)
                    
                logger.info(f"Retrieved {len(all_tracks)} tracks from Spotify for user {user.display_name}")
                
            except Exception as spotify_error:
                logger.error(f"Failed to fetch tracks from Spotify: {str(spotify_error)}")
                # Return empty result instead of failing completely
                all_tracks = []
        
        # Remove duplicates based on track ID
        seen_ids = set()
        unique_tracks = []
        for track in all_tracks:
            if track.get('id') and track['id'] not in seen_ids:
                seen_ids.add(track['id'])
                unique_tracks.append(track)
        
        # Separate tracks by type for frontend compatibility
        top_tracks = [track for track in unique_tracks if track.get('type') == 'top_track']
        saved_tracks = [track for track in unique_tracks if track.get('type') == 'saved_track']
        
        return {
            "tracks": unique_tracks,
            "top_tracks": top_tracks,
            "saved_tracks": saved_tracks,
            "total_count": len(unique_tracks),
            "top_tracks_count": len(top_tracks),
            "saved_tracks_count": len(saved_tracks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user tracks")


@router.get("/tracks/count")
async def get_user_tracks_count(request: Request, db: Session = Depends(get_db)):
    """
    Get the count of user's top tracks and saved tracks.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get counts from database
        top_tracks_count = db.query(UserTopTrack).filter(UserTopTrack.user_id == user_id).count()
        saved_tracks_count = db.query(UserSavedTrack).filter(UserSavedTrack.user_id == user_id).count()
        
        return {
            "top_tracks_count": top_tracks_count,
            "saved_tracks_count": saved_tracks_count,
            "total_tracks": top_tracks_count + saved_tracks_count
        }
        
    except Exception as e:
        logger.error(f"Error getting tracks count: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get tracks count")

@router.get("/tracks/recent")
async def get_recent_tracks(
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get the user's recently played/accessed tracks.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get recent top tracks
        recent_top_tracks = db.query(UserTopTrack).filter(
            UserTopTrack.user_id == user_id
        ).order_by(UserTopTrack.last_played.desc()).limit(limit).all()
        
        # Get recent saved tracks
        recent_saved_tracks = db.query(UserSavedTrack).filter(
            UserSavedTrack.user_id == user_id
        ).order_by(UserSavedTrack.last_accessed.desc()).limit(limit).all()
        
        # Combine and sort by recency
        all_recent = []
        
        for track in recent_top_tracks:
            all_recent.append({
                "id": track.spotify_track_id,
                "name": track.name,
                "artists": track.artists.split(", ") if track.artists else [],
                "album": track.album,
                "duration_ms": track.duration_ms,
                "popularity": track.popularity,
                "external_urls": track.external_urls,
                "uri": track.uri,
                "genres": track.genres,
                "audio_features": track.audio_features,
                "type": "top_track",
                "last_accessed": track.last_played.isoformat() if track.last_played else None
            })
        
        for track in recent_saved_tracks:
            all_recent.append({
                "id": track.spotify_track_id,
                "name": track.name,
                "artists": track.artists.split(", ") if track.artists else [],
                "album": track.album,
                "duration_ms": track.duration_ms,
                "popularity": track.popularity,
                "external_urls": track.external_urls,
                "uri": track.uri,
                "genres": track.genres,
                "audio_features": track.audio_features,
                "type": "saved_track",
                "last_accessed": track.last_accessed.isoformat() if track.last_accessed else None
            })
        
        # Sort by last accessed time
        all_recent.sort(key=lambda x: x['last_accessed'] or '', reverse=True)
        
        # Return limited results
        return all_recent[:limit]
        
    except Exception as e:
        logger.error(f"Error getting recent tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recent tracks")

@router.get("/tracks/search")
async def search_user_tracks(
    request: Request,
    query: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Search through user's tracks by name, artist, or album.
    """
    try:
        if not query or len(query.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
        
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        query = query.strip().lower()
        
        # Search in top tracks
        top_tracks = db.query(UserTopTrack).filter(
            UserTopTrack.user_id == user_id,
            (UserTopTrack.name.ilike(f"%{query}%") |
             UserTopTrack.artists.ilike(f"%{query}%") |
             UserTopTrack.album.ilike(f"%{query}%"))
        ).limit(limit).all()
        
        # Search in saved tracks
        saved_tracks = db.query(UserSavedTrack).filter(
            UserSavedTrack.user_id == user_id,
            (UserSavedTrack.name.ilike(f"%{query}%") |
             UserSavedTrack.artists.ilike(f"%{query}%") |
             UserSavedTrack.album.ilike(f"%{query}%"))
        ).limit(limit).all()
        
        # Combine results
        results = []
        
        for track in top_tracks:
            results.append({
                "id": track.spotify_track_id,
                "name": track.name,
                "artists": track.artists.split(", ") if track.artists else [],
                "album": track.album,
                "duration_ms": track.duration_ms,
                "popularity": track.popularity,
                "external_urls": track.external_urls,
                "uri": track.uri,
                "genres": track.genres,
                "audio_features": track.audio_features,
                "type": "top_track"
            })
        
        for track in saved_tracks:
            results.append({
                "id": track.spotify_track_id,
                "name": track.name,
                "artists": track.artists.split(", ") if track.artists else [],
                "album": track.album,
                "duration_ms": track.duration_ms,
                "popularity": track.popularity,
                "external_urls": track.external_urls,
                "uri": track.uri,
                "genres": track.genres,
                "audio_features": track.audio_features,
                "type": "saved_track"
            })
        
        # Remove duplicates and limit results
        seen_ids = set()
        unique_results = []
        for track in results:
            if track['id'] not in seen_ids:
                seen_ids.add(track['id'])
                unique_results.append(track)
                if len(unique_results) >= limit:
                    break
        
        return unique_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching user tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search tracks")

@router.post("/refresh-data")
async def refresh_user_data(request: Request, db: Session = Depends(get_db)):
    """
    Refresh user's Spotify data (top tracks and saved tracks).
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if token is expired
        if not user.access_token or (user.token_expires_at and user.token_expires_at <= datetime.utcnow()):
            raise HTTPException(status_code=401, detail="Access token expired")
        
        # Refresh top tracks
        top_tracks = spotify_service.get_user_top_tracks(user.access_token, limit=50)
        saved_tracks = spotify_service.get_user_saved_tracks(user.access_token, limit=50)
        
        # Clear existing data
        db.query(UserTopTrack).filter(UserTopTrack.user_id == user.id).delete()
        db.query(UserSavedTrack).filter(UserSavedTrack.user_id == user.id).delete()
        
        # Store new data
        for track in top_tracks:
            new_track = UserTopTrack(
                user_id=user.id,
                track_id=track['id'],
                spotify_track_id=track['id'],
                name=track['name'],
                artists=", ".join(track['artists']),
                album=track['album'],
                album_id=track.get('album_id'),
                duration_ms=track['duration_ms'],
                popularity=track.get('popularity', 0),
                external_urls=json.dumps(track.get('external_urls', {})),
                uri=track['uri'],
                audio_features=json.dumps(track),
                genres=json.dumps(track.get('genres', [])),
                time_range="medium_term",
                last_played=datetime.utcnow()
            )
            db.add(new_track)
        
        for track in saved_tracks:
            new_track = UserSavedTrack(
                user_id=user.id,
                track_id=track['id'],
                spotify_track_id=track['id'],
                name=track['name'],
                artists=", ".join(track['artists']),
                album=track['album'],
                album_id=track.get('album_id'),
                duration_ms=track['duration_ms'],
                popularity=track.get('popularity', 0),
                external_urls=json.dumps(track.get('external_urls', {})),
                uri=track['uri'],
                audio_features=json.dumps(track),
                genres=json.dumps(track.get('genres', [])),
                added_at=datetime.fromisoformat(track['added_at'].replace('Z', '+00:00')) if track.get('added_at') else None,
                last_accessed=datetime.utcnow()
            )
            db.add(new_track)
        
        db.commit()
        
        logger.info(f"Refreshed data for user {user.display_name}: {len(top_tracks)} top tracks, {len(saved_tracks)} saved tracks")
        
        return {
            "message": "Data refreshed successfully",
            "top_tracks_count": len(top_tracks),
            "saved_tracks_count": len(saved_tracks),
            "total_tracks": len(top_tracks) + len(saved_tracks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing user data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh user data")
