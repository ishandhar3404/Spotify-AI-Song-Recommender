from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, desc

from ..schemas import AnalyticsMetrics, RecommendationQuality
from ml.knn_algorithm import KNNRecommender
from ..config import settings
from ..database import get_db, User, Playlist as PlaylistModel, PlaylistTrack, UserTopTrack, UserSavedTrack
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize KNN recommender for quality calculations
knn_recommender = KNNRecommender(k=settings.KNN_K)

@router.get("/recommendation-quality/{playlist_id}", response_model=RecommendationQuality)
async def get_recommendation_quality(
    playlist_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get detailed quality metrics for a specific playlist.
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
        
        # Get playlist tracks
        playlist_tracks = db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist.id
        ).order_by(PlaylistTrack.position).all()
        
        if not playlist_tracks:
            raise HTTPException(status_code=400, detail="Playlist has no tracks")
        
        # Get user's listening history for comparison
        user_tracks = []
        
        # Get top tracks
        top_tracks = db.query(UserTopTrack).filter(UserTopTrack.user_id == user_id).all()
        for track in top_tracks:
            if track.audio_features:
                track_data = {
                    'id': track.spotify_track_id,
                    'name': track.name,
                    'artists': track.artists.split(", ") if track.artists else [],
                    'album': track.album,
                    'genres': track.genres or [],
                    **track.audio_features
                }
                user_tracks.append(track_data)
        
        # Get saved tracks
        saved_tracks = db.query(UserSavedTrack).filter(UserSavedTrack.user_id == user_id).all()
        for track in saved_tracks:
            if track.audio_features:
                track_data = {
                    'id': track.spotify_track_id,
                    'name': track.name,
                    'artists': track.artists.split(", ") if track.artists else [],
                    'album': track.album,
                    'genres': track.genres or [],
                    **track.audio_features
                }
                user_tracks.append(track_data)
        
        # Convert playlist tracks to format expected by KNN
        recommended_tracks = []
        for pt in playlist_tracks:
            # Find the original track data with audio features
            original_track = next((t for t in user_tracks if t['id'] == pt.track_id), None)
            if original_track:
                recommended_tracks.append(original_track)
        
        if not recommended_tracks:
            raise HTTPException(status_code=400, detail="No audio features available for playlist tracks")
        
        # Calculate quality metrics using KNN algorithm
        quality_metrics = knn_recommender.calculate_recommendation_quality(
            recommended_tracks=recommended_tracks,
            user_tracks=user_tracks,
            mood=playlist.mood,
            genre=playlist.genre
        )
        
        if 'error' in quality_metrics:
            raise HTTPException(status_code=400, detail=quality_metrics['error'])
        
        # Get stored metrics from playlist
        stored_metrics = playlist.metrics or {}
        
        return RecommendationQuality(
            playlist_id=playlist.id,
            playlist_name=playlist.name,
            mood=playlist.mood,
            genre=playlist.genre,
            playlist_length=playlist.playlist_length,
            internal_similarity=quality_metrics.get('internal_similarity', 0.0),
            genre_accuracy=quality_metrics.get('genre_accuracy', 0.0),
            mood_consistency=quality_metrics.get('mood_consistency', 0.0),
            average_similarity=stored_metrics.get('average_similarity', 0.0),
            tracks_found=stored_metrics.get('tracks_found', 0),
            requested_length=stored_metrics.get('requested_length', 0),
            generated_at=playlist.generated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendation quality: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendation quality")

@router.get("/user-stats", response_model=AnalyticsMetrics)
async def get_user_statistics(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistics for the current user.
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
        
        # Get track counts
        top_tracks_count = db.query(UserTopTrack).filter(UserTopTrack.user_id == user_id).count()
        saved_tracks_count = db.query(UserSavedTrack).filter(UserSavedTrack.user_id == user_id).count()
        total_tracks = top_tracks_count + saved_tracks_count
        
        # Get playlist statistics
        playlists = db.query(PlaylistModel).filter(PlaylistModel.user_id == user_id).all()
        total_playlists = len(playlists)
        
        # Calculate average playlist length
        if playlists:
            avg_playlist_length = sum(p.playlist_length for p in playlists) / len(playlists)
        else:
            avg_playlist_length = 0
        
        # Get most popular moods and genres
        mood_counts = {}
        genre_counts = {}
        
        for playlist in playlists:
            # Count moods
            mood = playlist.mood
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
            
            # Count genres
            genre = playlist.genre or "All Genres"
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sort by count
        top_moods = sorted(mood_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate average recommendation quality
        quality_scores = []
        for playlist in playlists:
            if playlist.metrics and 'average_similarity' in playlist.metrics:
                quality_scores.append(playlist.metrics['average_similarity'])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Get recent activity
        recent_playlists = db.query(PlaylistModel).filter(
            PlaylistModel.user_id == user_id
        ).order_by(PlaylistModel.generated_at.desc()).limit(5).all()
        
        recent_activity = []
        for playlist in recent_playlists:
            recent_activity.append({
                'playlist_id': playlist.id,
                'name': playlist.name,
                'mood': playlist.mood,
                'genre': playlist.genre,
                'generated_at': playlist.generated_at.isoformat(),
                'quality_score': playlist.metrics.get('average_similarity', 0) if playlist.metrics else 0
            })
        
        return AnalyticsMetrics(
            user_id=user.id,
            display_name=user.display_name,
            total_tracks=total_tracks,
            top_tracks_count=top_tracks_count,
            saved_tracks_count=saved_tracks_count,
            total_playlists=total_playlists,
            average_playlist_length=round(avg_playlist_length, 1),
            average_quality_score=round(avg_quality, 3),
            top_moods=top_moods,
            top_genres=top_genres,
            recent_activity=recent_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user statistics")

@router.get("/system-performance")
async def get_system_performance(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get system-wide performance metrics.
    """
    try:
        # Get user ID from request (for authorization)
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get total users
        total_users = db.query(User).count()
        
        # Get total playlists generated
        total_playlists = db.query(PlaylistModel).count()
        
        # Get total tracks stored
        total_top_tracks = db.query(UserTopTrack).count()
        total_saved_tracks = db.query(UserSavedTrack).count()
        total_tracks = total_top_tracks + total_saved_tracks
        
        # Get recent system activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_users = db.query(User).filter(User.last_login >= yesterday).count()
        recent_playlists = db.query(PlaylistModel).filter(PlaylistModel.generated_at >= yesterday).count()
        
        # Get average playlist quality
        quality_scores = db.query(PlaylistModel.metrics).filter(
            PlaylistModel.metrics.isnot(None)
        ).all()
        
        avg_quality = 0
        if quality_scores:
            scores = []
            for score_data in quality_scores:
                if score_data and 'average_similarity' in score_data:
                    scores.append(score_data['average_similarity'])
            if scores:
                avg_quality = sum(scores) / len(scores)
        
        # Get most popular moods and genres across all users
        mood_counts = db.query(
            PlaylistModel.mood,
            func.count(PlaylistModel.id).label('count')
        ).group_by(PlaylistModel.mood).order_by(desc('count')).limit(5).all()
        
        genre_counts = db.query(
            PlaylistModel.genre,
            func.count(PlaylistModel.id).label('count')
        ).group_by(PlaylistModel.genre).order_by(desc('count')).limit(5).all()
        
        return {
            "system_metrics": {
                "total_users": total_users,
                "total_playlists": total_playlists,
                "total_tracks": total_tracks,
                "recent_users_24h": recent_users,
                "recent_playlists_24h": recent_playlists,
                "average_quality_score": round(avg_quality, 3)
            },
            "popular_moods": [{"mood": mood, "count": count} for mood, count in mood_counts],
            "popular_genres": [{"genre": genre or "All Genres", "count": count} for genre, count in genre_counts]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system performance")

@router.get("/playlist-quality-trends")
async def get_playlist_quality_trends(
    request: Request,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get quality trends over time for the current user.
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
        
        # Validate days parameter
        if days < 1 or days > 365:
            days = 30
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get playlists in date range
        playlists = db.query(PlaylistModel).filter(
            PlaylistModel.user_id == user_id,
            PlaylistModel.generated_at >= start_date,
            PlaylistModel.generated_at <= end_date
        ).order_by(PlaylistModel.generated_at).all()
        
        # Group by date and calculate daily averages
        daily_quality = {}
        daily_counts = {}
        
        for playlist in playlists:
            date_key = playlist.generated_at.date().isoformat()
            
            if playlist.metrics and 'average_similarity' in playlist.metrics:
                quality = playlist.metrics['average_similarity']
                
                if date_key in daily_quality:
                    daily_quality[date_key].append(quality)
                    daily_counts[date_key] += 1
                else:
                    daily_quality[date_key] = [quality]
                    daily_counts[date_key] = 1
        
        # Calculate daily averages
        trends = []
        for date_key in sorted(daily_quality.keys()):
            avg_quality = sum(daily_quality[date_key]) / len(daily_quality[date_key])
            trends.append({
                "date": date_key,
                "average_quality": round(avg_quality, 3),
                "playlist_count": daily_counts[date_key]
            })
        
        # Calculate overall trends
        if trends:
            first_week_avg = sum(t['average_quality'] for t in trends[:7]) / min(len(trends), 7)
            last_week_avg = sum(t['average_quality'] for t in trends[-7:]) / min(len(trends), 7)
            quality_change = round(last_week_avg - first_week_avg, 3)
        else:
            quality_change = 0
        
        return {
            "user_id": user.id,
            "display_name": user.display_name,
            "period_days": days,
            "quality_change": quality_change,
            "daily_trends": trends,
            "total_playlists_in_period": len(playlists)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quality trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get quality trends")

@router.get("/mood-genre-analysis")
async def get_mood_genre_analysis(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis of mood and genre combinations.
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
        
        # Get all user playlists
        playlists = db.query(PlaylistModel).filter(PlaylistModel.user_id == user_id).all()
        
        # Analyze mood-genre combinations
        mood_genre_combinations = {}
        mood_quality = {}
        genre_quality = {}
        
        for playlist in playlists:
            mood = playlist.mood
            genre = playlist.genre or "All Genres"
            quality = playlist.metrics.get('average_similarity', 0) if playlist.metrics else 0
            
            # Count combinations
            key = f"{mood}_{genre}"
            if key in mood_genre_combinations:
                mood_genre_combinations[key]['count'] += 1
                mood_genre_combinations[key]['total_quality'] += quality
            else:
                mood_genre_combinations[key] = {
                    'mood': mood,
                    'genre': genre,
                    'count': 1,
                    'total_quality': quality
                }
            
            # Track mood quality
            if mood in mood_quality:
                mood_quality[mood]['count'] += 1
                mood_quality[mood]['total_quality'] += quality
            else:
                mood_quality[mood] = {'count': 1, 'total_quality': quality}
            
            # Track genre quality
            if genre in genre_quality:
                genre_quality[genre]['count'] += 1
                genre_quality[genre]['total_quality'] += quality
            else:
                genre_quality[genre] = {'count': 1, 'total_quality': quality}
        
        # Calculate averages
        for key, data in mood_genre_combinations.items():
            data['average_quality'] = round(data['total_quality'] / data['count'], 3)
        
        for mood, data in mood_quality.items():
            data['average_quality'] = round(data['total_quality'] / data['count'], 3)
        
        for genre, data in genre_quality.items():
            data['average_quality'] = round(data['total_quality'] / data['count'], 3)
        
        # Sort by count and quality
        sorted_combinations = sorted(
            mood_genre_combinations.values(),
            key=lambda x: (x['count'], x['average_quality']),
            reverse=True
        )
        
        sorted_moods = sorted(
            mood_quality.items(),
            key=lambda x: (x[1]['count'], x[1]['average_quality']),
            reverse=True
        )
        
        sorted_genres = sorted(
            genre_quality.items(),
            key=lambda x: (x[1]['count'], x[1]['average_quality']),
            reverse=True
        )
        
        return {
            "user_id": user.id,
            "display_name": user.display_name,
            "mood_genre_combinations": sorted_combinations,
            "mood_analysis": [{"mood": mood, **data} for mood, data in sorted_moods],
            "genre_analysis": [{"genre": genre, **data} for genre, data in sorted_genres]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mood-genre analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get mood-genre analysis")
