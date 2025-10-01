#!/usr/bin/env python3
"""
Smart Playlist Generator using ML techniques with available Spotify data.
This replaces audio features with alternative features we can actually access.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SmartPlaylistGenerator:
    """
    Smart playlist generator using ML techniques with available Spotify data.
    Uses artist similarity, popularity patterns, and user behavior instead of audio features.
    """
    
    def __init__(self, k: int = 20):
        self.k = k
        self.scaler = StandardScaler()
        
        # Features we can actually extract from available data
        self.feature_columns = [
            'popularity_score',      # Track popularity (0-100)
            'duration_category',     # Duration in categories (short/medium/long)
            'artist_popularity',     # Artist's average popularity
            'album_recency',         # How recent the album is
            'genre_diversity',       # Number of genres for the track
            'energy_estimate',       # Estimated energy based on popularity/duration
            'danceability_estimate', # Estimated danceability based on patterns
            'valence_estimate'       # Estimated mood based on artist/genre patterns
        ]
        
        # Mood definitions based on available data
        self.mood_profiles = {
            'energetic': {
                'popularity_weight': 1.2,
                'duration_preference': 'medium',
                'artist_popularity_weight': 1.3,
                'energy_estimate_weight': 1.5,
                'danceability_estimate_weight': 1.4
            },
            'chill': {
                'popularity_weight': 0.8,
                'duration_preference': 'long',
                'artist_popularity_weight': 0.9,
                'energy_estimate_weight': 0.5,
                'danceability_estimate_weight': 0.6
            },
            'focused': {
                'popularity_weight': 0.7,
                'duration_preference': 'medium',
                'artist_popularity_weight': 0.8,
                'energy_estimate_weight': 0.6,
                'danceability_estimate_weight': 0.5
            },
            'party': {
                'popularity_weight': 1.4,
                'duration_preference': 'short',
                'artist_popularity_weight': 1.5,
                'energy_estimate_weight': 1.6,
                'danceability_estimate_weight': 1.7
            },
            'relaxed': {
                'popularity_weight': 0.6,
                'duration_preference': 'long',
                'artist_popularity_weight': 0.7,
                'energy_estimate_weight': 0.4,
                'danceability_estimate_weight': 0.5
            },
            'workout': {
                'popularity_weight': 1.3,
                'duration_preference': 'medium',
                'artist_popularity_weight': 1.4,
                'energy_estimate_weight': 1.7,
                'danceability_estimate_weight': 1.6
            },
            'happy': {
                'popularity_weight': 1.1,
                'duration_preference': 'medium',
                'artist_popularity_weight': 1.2,
                'energy_estimate_weight': 1.2,
                'danceability_estimate_weight': 1.3
            },
            'melancholic': {
                'popularity_weight': 0.5,
                'duration_preference': 'long',
                'artist_popularity_weight': 0.6,
                'energy_estimate_weight': 0.3,
                'danceability_estimate_weight': 0.4
            }
        }
        
        # Genre mapping for available genres
        self.available_genres = [
            'pop', 'rock', 'hip hop', 'electronic', 'jazz', 
            'classical', 'country', 'folk', 'blues', 'reggae'
        ]
    
    def _extract_track_features(self, track_data: Dict) -> List[float]:
        """
        Extract features from available track data.
        
        Args:
            track_data: Track dictionary with available Spotify data
            
        Returns:
            List of extracted features
        """
        # Ensure track_data is a dictionary
        if not isinstance(track_data, dict):
            logger.warning(f"Track data is not a dictionary: {type(track_data)}")
            # Return default features for invalid data
            return [50.0, 1.0, 50.0, 0.5, 0.1, 0.5, 0.5, 0.5]
        
        features = []
        
        # 1. Popularity score (0-100)
        popularity = track_data.get('popularity', 50)
        features.append(float(popularity))
        
        # 2. Duration category (0=short, 1=medium, 2=long)
        duration_ms = track_data.get('duration_ms', 180000)
        if duration_ms < 120000:  # < 2 minutes
            duration_cat = 0
        elif duration_ms < 240000:  # 2-4 minutes
            duration_cat = 1
        else:  # > 4 minutes
            duration_cat = 2
        features.append(float(duration_cat))
        
        # 3. Artist popularity (average of all artists)
        artists = track_data.get('artists', [])
        if isinstance(artists, list) and artists:
            # For now, use track popularity as proxy for artist popularity
            artist_popularity = popularity * 0.9  # Slightly lower than track
        else:
            artist_popularity = 50
        features.append(float(artist_popularity))
        
        # 4. Album recency (years since release, normalized)
        album = track_data.get('album', {})
        if isinstance(album, dict):
            release_date = album.get('release_date', '2020-01-01')
        else:
            release_date = '2020-01-01'
            
        try:
            if len(release_date) == 4:  # Year only
                release_year = int(release_date)
            else:  # Full date
                release_year = datetime.strptime(release_date, '%Y-%m-%d').year
            years_old = 2025 - release_year
            recency = max(0, min(1, (10 - years_old) / 10))  # 0-1 scale
        except:
            recency = 0.5  # Default for unknown dates
        features.append(recency)
        
        # 5. Genre diversity (number of genres, normalized)
        genres = track_data.get('genres', [])
        if isinstance(genres, str):
            genres = [genres]
        elif not isinstance(genres, list):
            genres = []
        genre_diversity = min(1.0, len(genres) / 5.0)  # Normalize to 0-1
        features.append(genre_diversity)
        
        # 6. Energy estimate (based on popularity and duration)
        energy = (popularity / 100) * (1 - duration_cat / 2)  # Higher for popular, shorter tracks
        features.append(energy)
        
        # 7. Danceability estimate (based on genre and popularity)
        track_genres = [g.lower() for g in genres if isinstance(g, str)]
        danceable_genres = ['pop', 'hip hop', 'electronic', 'reggae']
        danceability_base = 0.3
        if any(g in danceable_genres for g in track_genres):
            danceability_base = 0.8
        danceability = danceability_base + (popularity / 100) * 0.2
        features.append(min(1.0, danceability))
        
        # 8. Valence estimate (mood based on genre patterns)
        positive_genres = ['pop', 'folk', 'reggae']
        neutral_genres = ['rock', 'electronic', 'country']
        negative_genres = ['blues', 'classical']
        
        valence_base = 0.5
        if any(g in positive_genres for g in track_genres):
            valence_base = 0.8
        elif any(g in negative_genres for g in track_genres):
            valence_base = 0.2
        
        valence = valence_base + (popularity / 100) * 0.1
        features.append(max(0.0, min(1.0, valence)))
        
        return features
    
    def _extract_normalized_features(self, tracks_data: List[Dict]) -> np.ndarray:
        """
        Extract and normalize features from tracks data.
        
        Args:
            tracks_data: List of track dictionaries
            
        Returns:
            Normalized feature matrix
        """
        features = []
        for track in tracks_data:
            track_features = self._extract_track_features(track)
            features.append(track_features)
        
        features_array = np.array(features)
        
        # Normalize features
        if len(features_array) > 0:
            features_array = self.scaler.fit_transform(features_array)
            
        return features_array
    
    def _apply_mood_weights(self, features: np.ndarray, mood: str) -> np.ndarray:
        """
        Apply mood-specific weights to features.
        
        Args:
            features: Feature vector
            mood: Target mood for recommendations
            
        Returns:
            Weighted feature vector
        """
        mood_profile = self.mood_profiles.get(mood.lower(), self.mood_profiles['chill'])
        
        # Create weight vector based on mood profile
        weights = np.array([
            mood_profile['popularity_weight'],
            1.0,  # duration_category
            mood_profile['artist_popularity_weight'],
            1.0,  # album_recency
            1.0,  # genre_diversity
            mood_profile['energy_estimate_weight'],
            mood_profile['danceability_estimate_weight'],
            1.0   # valence_estimate
        ])
        
        return features * weights
    
    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two feature vectors."""
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
            user_tracks: List of user's tracks
            
        Returns:
            Average feature vector representing user's taste
        """
        if not user_tracks:
            return np.zeros(len(self.feature_columns))
            
        features = self._extract_normalized_features(user_tracks)
        return np.mean(features, axis=0)
    
    def _cluster_user_tracks(self, user_tracks: List[Dict], n_clusters: int = 3) -> Dict:
        """
        Cluster user's tracks into mood groups using K-means.
        
        Args:
            user_tracks: List of user's tracks
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary with cluster assignments and centroids
        """
        if len(user_tracks) < n_clusters:
            return {"clusters": [], "centroids": [], "labels": []}
        
        features = self._extract_normalized_features(user_tracks)
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(features)
        
        # Create cluster information
        clusters = {}
        for i in range(n_clusters):
            cluster_tracks = [user_tracks[j] for j in range(len(user_tracks)) if labels[j] == i]
            clusters[i] = {
                'tracks': cluster_tracks,
                'centroid': kmeans.cluster_centers_[i],
                'size': len(cluster_tracks)
            }
        
        return {
            "clusters": clusters,
            "centroids": kmeans.cluster_centers_,
            "labels": labels
        }
    
    def _find_similar_tracks_knn(self, target_features: np.ndarray, 
                                available_tracks: List[Dict], k: int = 20) -> List[Tuple[int, float]]:
        """
        Find similar tracks using KNN algorithm.
        
        Args:
            target_features: Target feature vector
            available_tracks: Pool of tracks to search
            k: Number of neighbors to find
            
        Returns:
            List of (track_index, similarity_score) tuples
        """
        if not available_tracks:
            return []
        
        track_features = self._extract_normalized_features(available_tracks)
        
        # Use sklearn's NearestNeighbors for efficiency
        nbrs = NearestNeighbors(n_neighbors=min(k, len(track_features)), 
                               algorithm='auto', metric='cosine')
        nbrs.fit(track_features)
        
        # Find neighbors
        distances, indices = nbrs.kneighbors([target_features])
        
        # Convert distances to similarities (cosine similarity = 1 - cosine distance)
        similarities = 1 - distances[0]
        
        return list(zip(indices[0], similarities))
    
    def generate_smart_playlist(self,
                              user_tracks: List[Dict],
                              available_tracks: List[Dict],
                              mood: str,
                              genre: Optional[str] = None,
                              playlist_length: int = 20,
                              seed_track: Optional[Dict] = None) -> Tuple[List[Dict], Dict]:
        """
        Generate smart playlist using ML techniques.
        
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
            logger.info(f"Generating smart playlist: mood={mood}, genre={genre}, length={playlist_length}")
            
            # Filter tracks by genre if specified
            if genre and genre.lower() != "all genres":
                available_tracks = self._filter_by_genre(available_tracks, genre)
            
            if not available_tracks:
                logger.warning(f"No tracks found for genre: {genre}")
                return [], {"error": f"No tracks available for genre: {genre}"}
            
            # Cluster user's tracks to understand their taste patterns
            user_clusters = self._cluster_user_tracks(user_tracks)
            
            # Calculate user profile
            user_profile = self._calculate_user_profile(user_tracks)
            
            # Apply mood weights to user profile
            weighted_profile = self._apply_mood_weights(user_profile, mood)
            
            # If seed track is provided, blend with it
            if seed_track:
                seed_features = self._extract_normalized_features([seed_track])[0]
                weighted_seed = self._apply_mood_weights(seed_features, mood)
                # Blend user profile with seed track (30% seed influence)
                weighted_profile = 0.7 * weighted_profile + 0.3 * weighted_seed
            
            # Find similar tracks using KNN
            similar_tracks = self._find_similar_tracks_knn(weighted_profile, available_tracks, k=self.k * 2)
            
            # Select top tracks for playlist
            selected_indices = [idx for idx, _ in similar_tracks[:playlist_length]]
            recommended_tracks = [available_tracks[i] for i in selected_indices]
            
            # Calculate metrics
            similarities = [sim for _, sim in similar_tracks[:len(recommended_tracks)]]
            avg_similarity = np.mean(similarities) if similarities else 0.0
            
            metrics = {
                "average_similarity": float(avg_similarity),
                "tracks_found": len(recommended_tracks),
                "requested_length": playlist_length,
                "genre_filter": genre,
                "mood": mood,
                "user_clusters": len(user_clusters.get("clusters", {})),
                "seed_track_used": seed_track is not None
            }
            
            logger.info(f"Generated {len(recommended_tracks)} recommendations with avg similarity: {avg_similarity:.3f}")
            
            return recommended_tracks, metrics
            
        except Exception as e:
            logger.error(f"Error generating smart playlist: {str(e)}")
            return [], {"error": f"Failed to generate playlist: {str(e)}"}
    
    def _filter_by_genre(self, tracks: List[Dict], target_genre: str) -> List[Dict]:
        """Filter tracks by genre."""
        if not target_genre or target_genre.lower() == "all genres":
            return tracks
        
        # Handle enum values by converting to lowercase for comparison
        target_genre_lower = target_genre.lower().replace('-', ' ').replace('&', 'and')
        
        filtered_tracks = []
        for track in tracks:
            track_genres = track.get('genres', [])
            if isinstance(track_genres, str):
                track_genres = [track_genres]
            
            # Check if any of the track's genres match the target genre
            track_genres_lower = [g.lower().replace('-', ' ').replace('&', 'and') for g in track_genres]
            if any(target_genre_lower in genre or genre in target_genre_lower for genre in track_genres_lower):
                filtered_tracks.append(track)
        
        return filtered_tracks
    
    def analyze_user_taste(self, user_tracks: List[Dict]) -> Dict:
        """
        Analyze user's taste patterns using ML.
        
        Args:
            user_tracks: List of user's tracks
            
        Returns:
            Dictionary with taste analysis
        """
        try:
            if not user_tracks:
                return {"error": "No user tracks provided"}
            
            # Extract features
            features = self._extract_normalized_features(user_tracks)
            user_profile = np.mean(features, axis=0)
            
            # Cluster tracks
            clusters = self._cluster_user_tracks(user_tracks, n_clusters=min(3, len(user_tracks)))
            
            # Analyze patterns
            taste_analysis = {
                "total_tracks": len(user_tracks),
                "dominant_moods": self._identify_dominant_moods(user_profile),
                "preferred_genres": self._identify_preferred_genres(user_tracks),
                "listening_patterns": self._analyze_listening_patterns(user_tracks),
                "cluster_summary": self._summarize_clusters(clusters)
            }
            
            return taste_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user taste: {str(e)}")
            return {"error": f"Failed to analyze taste: {str(e)}"}
    
    def _identify_dominant_moods(self, user_profile: np.ndarray) -> List[str]:
        """Identify user's dominant moods based on their profile."""
        mood_scores = {}
        
        for mood, profile in self.mood_profiles.items():
            # Create a mood vector based on the profile
            mood_vector = np.array([
                profile['popularity_weight'],
                1.0,  # duration_category
                profile['artist_popularity_weight'],
                1.0,  # album_recency
                1.0,  # genre_diversity
                profile['energy_estimate_weight'],
                profile['danceability_estimate_weight'],
                1.0   # valence_estimate
            ])
            
            # Calculate similarity
            similarity = self._calculate_cosine_similarity(user_profile, mood_vector)
            mood_scores[mood] = similarity
        
        # Return top 3 moods
        sorted_moods = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
        return [mood for mood, _ in sorted_moods[:3]]
    
    def _identify_preferred_genres(self, user_tracks: List[Dict]) -> List[str]:
        """Identify user's preferred genres."""
        genre_counts = {}
        
        for track in user_tracks:
            genres = track.get('genres', [])
            if isinstance(genres, str):
                genres = [genres]
            
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Return top 5 genres
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        return [genre for genre, _ in sorted_genres[:5]]
    
    def _analyze_listening_patterns(self, user_tracks: List[Dict]) -> Dict:
        """Analyze user's listening patterns."""
        if not user_tracks:
            return {}
        
        # Analyze duration patterns
        durations = [track.get('duration_ms', 0) for track in user_tracks]
        avg_duration = np.mean(durations) if durations else 0
        
        # Analyze popularity patterns
        popularities = [track.get('popularity', 0) for track in user_tracks]
        avg_popularity = np.mean(popularities) if popularities else 0
        
        return {
            "average_track_duration": float(avg_duration),
            "average_popularity": float(avg_popularity),
            "duration_variety": len(set(durations)) > 1,
            "popularity_range": max(popularities) - min(popularities) if popularities else 0
        }
    
    def _summarize_clusters(self, clusters: Dict) -> List[Dict]:
        """Summarize the clustering results."""
        cluster_summary = []
        
        for cluster_id, cluster_info in clusters.get("clusters", {}).items():
            tracks = cluster_info['tracks']
            if not tracks:
                continue
                
            # Analyze cluster characteristics
            avg_popularity = np.mean([t.get('popularity', 0) for t in tracks])
            avg_duration = np.mean([t.get('duration_ms', 0) for t in tracks])
            
            # Get dominant genres in this cluster
            cluster_genres = {}
            for track in tracks:
                genres = track.get('genres', [])
                if isinstance(genres, str):
                    genres = [genres]
                for genre in genres:
                    cluster_genres[genre] = cluster_genres.get(genre, 0) + 1
            
            dominant_genres = sorted(cluster_genres.items(), key=lambda x: x[1], reverse=True)[:3]
            
            cluster_summary.append({
                "cluster_id": cluster_id,
                "size": len(tracks),
                "average_popularity": float(avg_popularity),
                "average_duration": float(avg_duration),
                "dominant_genres": [genre for genre, _ in dominant_genres]
            })
        
        return cluster_summary
