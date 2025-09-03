import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class KNNRecommender:
    """
    Custom K-Nearest Neighbors algorithm for music recommendations
    based on Spotify audio features.
    """
    
    def __init__(self, k: int = 20):
        self.k = k
        self.scaler = StandardScaler()
        self.feature_columns = [
            'acousticness', 'danceability', 'energy', 'instrumentalness',
            'liveness', 'loudness', 'speechiness', 'tempo', 'valence'
        ]
        
    def _extract_normalized_features(self, tracks_data: List[Dict]) -> np.ndarray:
        """
        Extract and normalize audio features from tracks data.
        
        Args:
            tracks_data: List of track dictionaries with audio features
            
        Returns:
            Normalized feature matrix
        """
        features = []
        for track in tracks_data:
            track_features = []
            for col in self.feature_columns:
                value = track.get(col, 0.0)
                # Handle missing values
                if value is None:
                    value = 0.0
                track_features.append(float(value))
            features.append(track_features)
        
        features_array = np.array(features)
        
        # Normalize features
        if len(features_array) > 0:
            features_array = self.scaler.fit_transform(features_array)
            
        return features_array
    
    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two feature vectors.
        
        Args:
            vec1: First feature vector
            vec2: Second feature vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def _calculate_user_profile(self, user_tracks: List[Dict]) -> np.ndarray:
        """
        Calculate user profile as average of their track features.
        
        Args:
            user_tracks: List of user's tracks with audio features
            
        Returns:
            Average feature vector representing user's taste
        """
        if not user_tracks:
            return np.zeros(len(self.feature_columns))
            
        features = self._extract_normalized_features(user_tracks)
        return np.mean(features, axis=0)
    
    def _filter_by_genre(self, tracks: List[Dict], target_genre: Optional[str]) -> List[Dict]:
        """
        Filter tracks by genre if specified.
        
        Args:
            tracks: List of tracks to filter
            target_genre: Genre to filter by (None for all genres)
            
        Returns:
            Filtered list of tracks
        """
        if not target_genre or target_genre.lower() == "all genres":
            return tracks
            
        filtered_tracks = []
        for track in tracks:
            track_genres = track.get('genres', [])
            if isinstance(track_genres, str):
                track_genres = [track_genres]
            
            # Check if any of the track's genres match the target genre
            if any(genre.lower() == target_genre.lower() for genre in track_genres):
                filtered_tracks.append(track)
                
        return filtered_tracks
    
    def _apply_mood_weights(self, features: np.ndarray, mood: str) -> np.ndarray:
        """
        Apply mood-specific weights to audio features.
        
        Args:
            features: Audio feature vector
            mood: Target mood for recommendations
            
        Returns:
            Weighted feature vector
        """
        mood_weights = {
            'energetic': [1.0, 1.5, 1.8, 1.0, 1.2, 1.3, 0.8, 1.4, 1.2],
            'chill': [1.5, 0.7, 0.5, 1.2, 0.6, 0.8, 0.5, 0.7, 0.8],
            'focused': [1.2, 0.6, 0.7, 1.5, 0.5, 0.9, 0.3, 0.8, 0.6],
            'party': [0.8, 1.8, 1.6, 0.9, 1.4, 1.5, 1.2, 1.3, 1.4],
            'relaxed': [1.6, 0.5, 0.4, 1.3, 0.4, 0.7, 0.4, 0.6, 0.7],
            'workout': [0.7, 1.6, 1.7, 0.8, 1.3, 1.4, 0.9, 1.5, 1.1],
            'happy': [0.9, 1.3, 1.2, 0.8, 1.1, 1.0, 1.0, 1.1, 1.6],
            'melancholic': [1.4, 0.6, 0.5, 1.1, 0.7, 0.8, 0.6, 0.7, 0.4]
        }
        
        weights = mood_weights.get(mood.lower(), [1.0] * len(self.feature_columns))
        return features * np.array(weights)
    
    def _blend_with_seed_track(self, features: np.ndarray, seed_track: Optional[Dict], 
                               blend_weight: float = 0.3) -> np.ndarray:
        """
        Blend features with seed track if provided.
        
        Args:
            features: Current feature vector
            seed_track: Optional seed track for guidance
            blend_weight: Weight for seed track influence
            
        Returns:
            Blended feature vector
        """
        if not seed_track:
            return features
            
        seed_features = self._extract_normalized_features([seed_track])
        if len(seed_features) > 0:
            blended = (1 - blend_weight) * features + blend_weight * seed_features[0]
            return blended
            
        return features
    
    def recommend_tracks(self, 
                        user_tracks: List[Dict],
                        available_tracks: List[Dict],
                        mood: str,
                        genre: Optional[str] = None,
                        playlist_length: int = 20,
                        seed_track: Optional[Dict] = None) -> Tuple[List[Dict], Dict]:
        """
        Generate track recommendations using KNN algorithm.
        
        Args:
            user_tracks: User's listening history
            available_tracks: Pool of tracks to recommend from
            mood: Target mood for recommendations
            genre: Optional genre filter
            playlist_length: Number of tracks to recommend
            seed_track: Optional seed track for guidance
            
        Returns:
            Tuple of (recommended_tracks, metrics)
        """
        try:
            # Filter tracks by genre first
            filtered_tracks = self._filter_by_genre(available_tracks, genre)
            
            if not filtered_tracks:
                logger.warning(f"No tracks found for genre: {genre}")
                return [], {"error": f"No tracks available for genre: {genre}"}
            
            # Calculate user profile
            user_profile = self._calculate_user_profile(user_tracks)
            
            # Extract features from available tracks
            track_features = self._extract_normalized_features(filtered_tracks)
            
            if len(track_features) == 0:
                logger.warning("No valid features found in available tracks")
                return [], {"error": "No valid audio features found"}
            
            # Calculate similarities
            similarities = []
            for i, features in enumerate(track_features):
                # Apply mood weights
                weighted_features = self._apply_mood_weights(features, mood)
                
                # Blend with seed track if provided
                blended_features = self._blend_with_seed_track(weighted_features, seed_track)
                
                # Calculate similarity to user profile
                similarity = self._calculate_cosine_similarity(user_profile, blended_features)
                similarities.append((similarity, i))
            
            # Sort by similarity (descending)
            similarities.sort(reverse=True, key=lambda x: x[0])
            
            # Select top K tracks
            k = min(self.k, len(similarities))
            top_indices = [idx for _, idx in similarities[:k]]
            
            # Limit to requested playlist length
            final_indices = top_indices[:playlist_length]
            
            # Get recommended tracks
            recommended_tracks = [filtered_tracks[i] for i in final_indices]
            
            # Calculate metrics
            avg_similarity = np.mean([sim for sim, _ in similarities[:len(final_indices)]])
            metrics = {
                "average_similarity": float(avg_similarity),
                "tracks_found": len(recommended_tracks),
                "requested_length": playlist_length,
                "genre_filter": genre,
                "mood": mood
            }
            
            logger.info(f"Generated {len(recommended_tracks)} recommendations with avg similarity: {avg_similarity:.3f}")
            
            return recommended_tracks, metrics
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return [], {"error": f"Failed to generate recommendations: {str(e)}"}
    
    def calculate_recommendation_quality(self, recommended_tracks: List[Dict], 
                                       user_tracks: List[Dict], mood: str, 
                                       genre: Optional[str] = None) -> Dict:
        """
        Calculate quality metrics for recommendations.
        
        Args:
            recommended_tracks: List of recommended tracks
            user_tracks: User's listening history
            mood: Target mood
            genre: Optional genre filter
            
        Returns:
            Dictionary of quality metrics
        """
        if not recommended_tracks:
            return {"error": "No tracks to evaluate"}
            
        try:
            # Calculate average similarity within recommendations
            rec_features = self._extract_normalized_features(recommended_tracks)
            if len(rec_features) > 1:
                similarities = []
                for i in range(len(rec_features)):
                    for j in range(i + 1, len(rec_features)):
                        sim = self._calculate_cosine_similarity(rec_features[i], rec_features[j])
                        similarities.append(sim)
                avg_internal_similarity = np.mean(similarities)
            else:
                avg_internal_similarity = 1.0
            
            # Calculate genre matching accuracy
            genre_accuracy = 0.0
            if genre and genre.lower() != "all genres":
                matching_genres = 0
                for track in recommended_tracks:
                    track_genres = track.get('genres', [])
                    if isinstance(track_genres, str):
                        track_genres = [track_genres]
                    if any(genre.lower() in g.lower() for g in track_genres):
                        matching_genres += 1
                genre_accuracy = matching_genres / len(recommended_tracks)
            
            # Calculate mood consistency
            user_profile = self._calculate_user_profile(user_tracks)
            rec_profile = self._calculate_user_profile(recommended_tracks)
            mood_consistency = self._calculate_cosine_similarity(user_profile, rec_profile)
            
            return {
                "internal_similarity": float(avg_internal_similarity),
                "genre_accuracy": float(genre_accuracy),
                "mood_consistency": float(mood_consistency),
                "total_tracks": len(recommended_tracks)
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {str(e)}")
            return {"error": f"Failed to calculate quality metrics: {str(e)}"}
