from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Optional
import logging
import json
from datetime import datetime

from ..schemas import PlaylistGenerateRequest, Playlist, Track
from ..services.spotify_service import SpotifyService
from ml.knn_algorithm import KNNRecommender
from ml.smart_playlist_generator import SmartPlaylistGenerator
from ..config import settings
from ..database import get_db, User, UserTopTrack, UserSavedTrack, Playlist as PlaylistModel, PlaylistTrack
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
spotify_service = SpotifyService(
    client_id=settings.SPOTIFY_CLIENT_ID,
    client_secret=settings.SPOTIFY_CLIENT_SECRET,
    redirect_uri=settings.SPOTIFY_REDIRECT_URI
)

knn_recommender = KNNRecommender(k=settings.KNN_K)
smart_playlist_generator = SmartPlaylistGenerator(k=settings.KNN_K)

@router.post("/generate", response_model=Playlist)
async def generate_playlist(
    request_data: PlaylistGenerateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate a personalized playlist using KNN algorithm.
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
        
        # Validate request parameters
        if request_data.playlist_length < settings.MIN_PLAYLIST_LENGTH or request_data.playlist_length > settings.MAX_PLAYLIST_LENGTH:
            raise HTTPException(
                status_code=400, 
                detail=f"Playlist length must be between {settings.MIN_PLAYLIST_LENGTH} and {settings.MAX_PLAYLIST_LENGTH} songs"
            )
        
        if request_data.mood not in settings.SUPPORTED_MOODS:
            raise HTTPException(
                status_code=400, 
                detail=f"Mood must be one of: {', '.join(settings.SUPPORTED_MOODS)}"
            )
        
        if request_data.genre and request_data.genre not in settings.SUPPORTED_GENRES + ["All Genres"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Genre must be one of: All Genres, {', '.join(settings.SUPPORTED_GENRES)}"
            )
        
        # Get user's listening history from Spotify API (real-time)
        user_tracks = []  # Initialize the list
        available_tracks = []  # Pool of tracks for recommendations
        
        try:
            # Get user's top tracks from Spotify
            top_tracks = spotify_service.get_user_top_tracks(
                access_token=user.access_token,
                limit=50,
                time_range='medium_term'
            )
            user_tracks.extend(top_tracks)
            
            # Get user's saved tracks from Spotify
            saved_tracks = spotify_service.get_user_saved_tracks(
                access_token=user.access_token,
                limit=50
            )
            user_tracks.extend(saved_tracks)
            
            # Get additional tracks for recommendation pool
            # Map enum values to search queries
            genre_search_map = {
                "Pop": "pop",
                "Rock": "rock", 
                "Electronic": "electronic",
                "Jazz": "jazz",
                "Hip-Hop": "hip hop",
                "Classical": "classical",
                "Country": "country",
                "R&B": "r&b",
                "All Genres": None  # Will search all
            }
            
            search_queries = ["pop", "rock", "electronic", "jazz", "hip hop", "country", "folk", "blues", "reggae", "classical"]
            for query in search_queries:
                try:
                    search_results = spotify_service.search_tracks(
                        access_token=user.access_token,
                        query=query,
                        limit=10
                    )
                    available_tracks.extend(search_results)
                except Exception as e:
                    logger.warning(f"Failed to search for {query}: {e}")
            
            logger.info(f"Retrieved {len(user_tracks)} user tracks and {len(available_tracks)} available tracks for user {user.display_name}")
            
        except Exception as e:
            logger.error(f"Failed to fetch tracks from Spotify: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch user listening history from Spotify")
        
        # Check if user has enough tracks
        if len(user_tracks) < settings.MIN_TRACKS_REQUIRED:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough tracks in your library. You need at least {settings.MIN_TRACKS_REQUIRED} tracks, but you have {len(user_tracks)}."
            )
        
        # Get seed track if specified
        seed_track = None
        if request_data.seed_track_id:
            seed_track = next((t for t in user_tracks if t['id'] == request_data.seed_track_id), None)
            if not seed_track:
                raise HTTPException(status_code=400, detail="Seed track not found in your library")
        
        # Generate recommendations using Smart Playlist Generator
        recommended_tracks, metrics = smart_playlist_generator.generate_smart_playlist(
            user_tracks=user_tracks,
            available_tracks=available_tracks,
            mood=request_data.mood,
            genre=request_data.genre if request_data.genre != "All Genres" else None,
            playlist_length=request_data.playlist_length,
            seed_track=seed_track
        )
        
        if not recommended_tracks:
            raise HTTPException(
                status_code=400,
                detail=metrics.get('error', 'Failed to generate recommendations')
            )
        
        # Create playlist in database
        import json
        import uuid
        
        playlist_id = str(uuid.uuid4())
        playlist_name = request_data.playlist_name or f"{request_data.mood} {request_data.genre or 'Mix'} Playlist"
        playlist = PlaylistModel(
            id=playlist_id,
            user_id=user.id,
            name=playlist_name,
            description=f"Generated playlist with {request_data.mood} mood and {request_data.genre or 'all genres'}",
            mood=request_data.mood,
            genre=request_data.genre,
            playlist_length=len(recommended_tracks),
            seed_track_id=request_data.seed_track_id,
            generated_at=datetime.utcnow(),
            metrics=json.dumps(metrics)
        )
        db.add(playlist)
        db.flush()  # Get the playlist ID
        
        # Add tracks to playlist
        for i, track in enumerate(recommended_tracks):
            playlist_track = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track['id'],
                track_name=track['name'],
                artists=", ".join(track['artists']) if isinstance(track['artists'], list) else track['artists'],
                album=track['album'],
                position=i + 1,
                spotify_uri=track['uri']
            )
            db.add(playlist_track)
        
        db.commit()
        
        logger.info(f"Generated playlist with {len(recommended_tracks)} tracks for user {user.display_name}")
        
        # Format tracks for response
        formatted_tracks = []
        for track in recommended_tracks:
            formatted_track = {
                'id': track['id'],
                'name': track['name'],
                'artists': track['artists'] if isinstance(track['artists'], list) else [track['artists']],
                'album': track['album'],
                'album_art': track.get('album_images', [{}])[0].get('url', '') if track.get('album_images') else '',
                'uri': track['uri']
            }
            formatted_tracks.append(formatted_track)
        
        # Return playlist with tracks
        return Playlist(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            mood=playlist.mood,
            genre=playlist.genre,
            playlist_length=playlist.playlist_length,
            seed_track_id=playlist.seed_track_id,
            generated_at=playlist.generated_at.isoformat(),
            metrics=playlist.get_metrics(),
            tracks=formatted_tracks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating playlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate playlist")

@router.get("", response_model=List[Playlist])
@router.get("/list", response_model=List[Playlist])
async def get_user_playlists(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get list of user's generated playlists.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get playlists from database
        playlists = db.query(PlaylistModel).filter(
            PlaylistModel.user_id == user_id
        ).order_by(PlaylistModel.generated_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to response models
        playlist_responses = []
        for playlist in playlists:
            # Get tracks for this playlist
            playlist_tracks = db.query(PlaylistTrack).filter(
                PlaylistTrack.playlist_id == playlist.id
            ).order_by(PlaylistTrack.position).all()
            
            tracks = []
            for pt in playlist_tracks:
                track = {
                    'id': pt.track_id,
                    'name': pt.track_name,
                    'artists': pt.artists.split(", ") if pt.artists else [],
                    'album': pt.album,
                    'album_art': '',  # We don't store album art in the database
                    'uri': pt.spotify_uri
                }
                tracks.append(track)
            
            playlist_response = Playlist(
                id=playlist.id,
                name=playlist.name,
                description=playlist.description,
                mood=playlist.mood,
                genre=playlist.genre,
                playlist_length=playlist.playlist_length,
                seed_track_id=playlist.seed_track_id,
                generated_at=playlist.generated_at.isoformat(),
                metrics=playlist.get_metrics(),
                tracks=tracks
            )
            playlist_responses.append(playlist_response)
        
        return playlist_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user playlists: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get playlists")

@router.get("/{playlist_id}", response_model=Playlist)
async def get_playlist(
    playlist_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get a specific playlist by ID.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get playlist from database
        playlist = db.query(PlaylistModel).filter(
            PlaylistModel.id == playlist_id,
            PlaylistModel.user_id == user_id
        ).first()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Get tracks for this playlist
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist.id
        ).order_by(PlaylistTrack.position).all()
        
        tracks = []
        for pt in playlist_tracks:
            track = {
                'id': pt.track_id,
                'name': pt.track_name,
                'artists': pt.artists.split(", ") if pt.artists else [],
                'album': pt.album,
                'album_art': '',  # We don't store album art in the database
                'uri': pt.spotify_uri
            }
            tracks.append(track)
        
        return Playlist(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            mood=playlist.mood,
            genre=playlist.genre,
            playlist_length=playlist.playlist_length,
            seed_track_id=playlist.seed_track_id,
            generated_at=playlist.generated_at.isoformat(),
            metrics=playlist.metrics,
            tracks=tracks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting playlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get playlist")

@router.post("/{playlist_id}/regenerate", response_model=Playlist)
async def regenerate_playlist(
    playlist_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Regenerate a playlist with the same parameters.
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
        
        # Get existing playlist from database
        playlist = db.query(PlaylistModel).filter(
            PlaylistModel.id == playlist_id,
            PlaylistModel.user_id == user_id
        ).first()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Get user's current listening history
        user_tracks = []
        try:
            # Get top tracks from Spotify
            top_tracks = spotify_service.get_user_top_tracks(user.access_token, limit=50)
            user_tracks.extend(top_tracks)
            
            # Get saved tracks from Spotify
            saved_tracks = spotify_service.get_user_saved_tracks(user.access_token, limit=50)
            user_tracks.extend(saved_tracks)
            
            logger.info(f"Retrieved {len(user_tracks)} tracks for user {user.display_name}")
            
        except Exception as e:
            logger.error(f"Failed to fetch user tracks: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch user listening history")
        
        # Check if user has enough tracks
        if len(user_tracks) < settings.MIN_TRACKS_REQUIRED:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough tracks in your library. You need at least {settings.MIN_TRACKS_REQUIRED} tracks, but you have {len(user_tracks)}."
            )
        
        # Get seed track if specified
        seed_track = None
        if playlist.seed_track_id:
            seed_track = next((t for t in user_tracks if t['id'] == playlist.seed_track_id), None)
        
        # Generate new recommendations using KNN
        recommended_tracks, metrics = knn_recommender.recommend_tracks(
            user_tracks=user_tracks,
            available_tracks=user_tracks,  # Use user's library as the pool
            mood=playlist.mood,
            genre=playlist.genre if playlist.genre != "All Genres" else None,
            playlist_length=playlist.playlist_length,
            seed_track=seed_track
        )
        
        if not recommended_tracks:
            raise HTTPException(
                status_code=400,
                detail=metrics.get('error', 'Failed to generate recommendations')
            )
        
        # Clear existing tracks
        db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).delete()
        
        # Add new tracks to playlist
        for i, track in enumerate(recommended_tracks):
            playlist_track = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track['id'],
                track_name=track['name'],
                artists=", ".join(track['artists']) if isinstance(track['artists'], list) else track['artists'],
                album=track['album'],
                position=i + 1,
                spotify_uri=track['uri']
            )
            db.add(playlist_track)
        
        # Update playlist metadata
        import json
        playlist.generated_at = datetime.utcnow()
        playlist.metrics = json.dumps(metrics)
        playlist.playlist_length = len(recommended_tracks)
        
        db.commit()
        
        logger.info(f"Regenerated playlist with {len(recommended_tracks)} tracks for user {user.display_name}")
        
        # Format tracks for response
        formatted_tracks = []
        for track in recommended_tracks:
            formatted_track = {
                'id': track['id'],
                'name': track['name'],
                'artists': track['artists'] if isinstance(track['artists'], list) else [track['artists']],
                'album': track['album'],
                'album_art': track.get('album_images', [{}])[0].get('url', '') if track.get('album_images') else '',
                'uri': track['uri']
            }
            formatted_tracks.append(formatted_track)
        
        # Return updated playlist
        return Playlist(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            mood=playlist.mood,
            genre=playlist.genre,
            playlist_length=playlist.playlist_length,
            seed_track_id=playlist.seed_track_id,
            generated_at=playlist.generated_at.isoformat(),
            metrics=playlist.get_metrics(),
            tracks=formatted_tracks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating playlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to regenerate playlist")

@router.post("/{playlist_id}/save-to-spotify")
async def save_playlist_to_spotify(
    playlist_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Save a generated playlist to Spotify.
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
        
        # Get playlist from database
        playlist = db.query(PlaylistModel).filter(
            PlaylistModel.id == playlist_id,
            PlaylistModel.user_id == user_id
        ).first()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Get tracks for this playlist
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist.id
        ).order_by(PlaylistTrack.position).all()
        
        if not playlist_tracks:
            raise HTTPException(status_code=400, detail="Playlist has no tracks")
        
        # Create playlist on Spotify
        spotify_playlist = spotify_service.create_playlist(
            access_token=user.access_token,
            user_id=user.spotify_id,
            name=playlist.name,
            description=playlist.description,
            public=True
        )
        
        # Add tracks to Spotify playlist
        track_uris = [pt.spotify_uri for pt in playlist_tracks if pt.spotify_uri]
        success = spotify_service.add_tracks_to_playlist(
            access_token=user.access_token,
            playlist_id=spotify_playlist['id'],
            track_uris=track_uris
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add tracks to Spotify playlist")
        
        # Update playlist with Spotify ID
        playlist.spotify_playlist_id = spotify_playlist['id']
        playlist.spotify_playlist_url = spotify_playlist['external_urls'].get('spotify')
        playlist.saved_to_spotify = True
        playlist.saved_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Saved playlist {playlist.name} to Spotify for user {user.display_name}")
        
        return {
            "message": "Playlist saved to Spotify successfully",
            "spotify_playlist_id": spotify_playlist['id'],
            "spotify_playlist_url": spotify_playlist['external_urls'].get('spotify')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving playlist to Spotify: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save playlist to Spotify")

@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Delete a generated playlist.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get playlist from database
        playlist = db.query(PlaylistModel).filter(
            PlaylistModel.id == playlist_id,
            PlaylistModel.user_id == user_id
        ).first()
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Delete playlist tracks first
        db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).delete()
        
        # Delete playlist
        db.delete(playlist)
        db.commit()
        
        logger.info(f"Deleted playlist {playlist.name} for user {user_id}")
        
        return {"message": "Playlist deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting playlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete playlist")

@router.get("/moods")
async def get_supported_moods():
    """
    Get list of supported moods for playlist generation.
    """
    return {"moods": settings.SUPPORTED_MOODS}

@router.get("/genres")
async def get_supported_genres():
    """
    Get list of supported genres for playlist generation.
    """
    return {"genres": ["All Genres"] + settings.SUPPORTED_GENRES}
