import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Optional, Tuple
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SpotifyService:
    """
    Service class for handling all Spotify API interactions.
    """
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        
        # Initialize Spotify client
        self.sp = None
        self._setup_spotify_client()
    
    def _setup_spotify_client(self):
        """Initialize Spotify client with OAuth configuration."""
        try:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    scope=" ".join([
                        "user-read-private",
                        "user-read-email",
                        "user-top-read",
                        "user-library-read",
                        "playlist-read-private",
                        "playlist-modify-public",
                        "playlist-modify-private"
                    ])
                )
            )
            logger.info("Spotify client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {str(e)}")
            raise
    
    def get_auth_url(self) -> str:
        """
        Get the Spotify OAuth authorization URL.
        
        Returns:
            Authorization URL for Spotify OAuth
        """
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=" ".join([
                    "user-read-private",
                    "user-read-email",
                    "user-top-read",
                    "user-library-read",
                    "playlist-read-private",
                    "playlist-modify-public",
                    "playlist-modify-private"
                ])
            )
            return auth_manager.get_authorize_url()
        except Exception as e:
            logger.error(f"Failed to generate auth URL: {str(e)}")
            raise
    
    def get_tokens_from_code(self, code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Spotify callback
            
        Returns:
            Dictionary containing access_token, refresh_token, and expires_at
        """
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=" ".join([
                    "user-read-private",
                    "user-read-email",
                    "user-top-read",
                    "user-library-read",
                    "playlist-read-private",
                    "playlist-modify-public",
                    "playlist-modify-private"
                ])
            )
            
            # Get tokens
            token_info = auth_manager.get_access_token(code)
            
            if not token_info:
                raise Exception("Failed to get access token")
            
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(seconds=token_info.get('expires_in', 3600))
            
            return {
                'access_token': token_info['access_token'],
                'refresh_token': token_info.get('refresh_token'),
                'expires_at': expires_at.isoformat(),
                'token_type': token_info.get('token_type', 'Bearer')
            }
            
        except Exception as e:
            logger.error(f"Failed to get tokens from code: {str(e)}")
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh the access token using refresh token.
        
        Args:
            refresh_token: Refresh token from previous authentication
            
        Returns:
            Dictionary containing new access_token and expires_at
        """
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=" ".join([
                    "user-read-private",
                    "user-read-email",
                    "user-top-read",
                    "user-library-read",
                    "playlist-read-private",
                    "playlist-modify-public",
                    "playlist-modify-private"
                ])
            )
            
            # Refresh token
            token_info = auth_manager.refresh_access_token(refresh_token)
            
            if not token_info:
                raise Exception("Failed to refresh access token")
            
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(seconds=token_info.get('expires_in', 3600))
            
            return {
                'access_token': token_info['access_token'],
                'expires_at': expires_at.isoformat(),
                'token_type': token_info.get('token_type', 'Bearer')
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            raise
    
    def _set_access_token(self, access_token: str):
        """Set the access token for the Spotify client."""
        try:
            self.sp = spotipy.Spotify(auth=access_token)
            logger.debug("Access token set successfully")
        except Exception as e:
            logger.error(f"Failed to set access token: {str(e)}")
            raise
    
    def get_user_profile(self, access_token: str) -> Dict:
        """
        Get the current user's profile information.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User profile information
        """
        try:
            self._set_access_token(access_token)
            user = self.sp.current_user()
            
            return {
                'id': user['id'],
                'display_name': user['display_name'],
                'email': user.get('email'),
                'country': user.get('country'),
                'followers': user['followers']['total'],
                'images': user.get('images', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            raise
    
    def get_user_top_tracks(self, access_token: str, limit: int = 50, 
                           time_range: str = 'medium_term') -> List[Dict]:
        """
        Get the user's top tracks.
        
        Args:
            access_token: Valid access token
            limit: Number of tracks to retrieve (max 50)
            time_range: Time range for top tracks (short_term, medium_term, long_term)
            
        Returns:
            List of top tracks with audio features
        """
        try:
            self._set_access_token(access_token)
            
            # Get top tracks
            top_tracks = self.sp.current_user_top_tracks(limit=limit, time_range=time_range)
            
            # Get audio features for all tracks
            track_ids = [track['id'] for track in top_tracks['items']]
            audio_features = self.sp.audio_features(track_ids)
            
            # Combine track info with audio features
            enriched_tracks = []
            for i, track in enumerate(top_tracks['items']):
                track_data = {
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'album': track['album']['name'],
                    'album_id': track['album']['id'],
                    'album_images': track['album']['images'],
                    'duration_ms': track['duration_ms'],
                    'popularity': track['popularity'],
                    'external_urls': track['external_urls'],
                    'uri': track['uri']
                }
                
                # Add audio features if available
                if audio_features and i < len(audio_features) and audio_features[i]:
                    track_data.update(audio_features[i])
                
                # Get genres for the track's artists
                artist_ids = [artist['id'] for artist in track['artists']]
                if artist_ids:
                    try:
                        artists = self.sp.artists(artist_ids)
                        all_genres = []
                        for artist in artists['artists']:
                            all_genres.extend(artist.get('genres', []))
                        track_data['genres'] = list(set(all_genres))
                    except Exception as e:
                        logger.warning(f"Failed to get genres for track {track['id']}: {str(e)}")
                        track_data['genres'] = []
                
                enriched_tracks.append(track_data)
            
            logger.info(f"Retrieved {len(enriched_tracks)} top tracks with audio features")
            return enriched_tracks
            
        except Exception as e:
            logger.error(f"Failed to get user top tracks: {str(e)}")
            raise
    
    def get_user_saved_tracks(self, access_token: str, limit: int = 50) -> List[Dict]:
        """
        Get the user's saved tracks.
        
        Args:
            access_token: Valid access token
            limit: Number of tracks to retrieve (max 50)
            
        Returns:
            List of saved tracks with audio features
        """
        try:
            self._set_access_token(access_token)
            
            # Get saved tracks
            saved_tracks = self.sp.current_user_saved_tracks(limit=limit)
            
            # Get audio features for all tracks
            track_ids = [item['track']['id'] for item in saved_tracks['items']]
            audio_features = self.sp.audio_features(track_ids)
            
            # Combine track info with audio features
            enriched_tracks = []
            for i, item in enumerate(saved_tracks['items']):
                track = item['track']
                track_data = {
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'album': track['album']['name'],
                    'album_id': track['album']['id'],
                    'album_images': track['album']['images'],
                    'duration_ms': track['duration_ms'],
                    'popularity': track['popularity'],
                    'external_urls': track['external_urls'],
                    'uri': track['uri'],
                    'added_at': item['added_at']
                }
                
                # Add audio features if available
                if audio_features and i < len(audio_features) and audio_features[i]:
                    track_data.update(audio_features[i])
                
                # Get genres for the track's artists
                artist_ids = [artist['id'] for artist in track['artists']]
                if artist_ids:
                    try:
                        artists = self.sp.artists(artist_ids)
                        all_genres = []
                        for artist in artists['artists']:
                            all_genres.extend(artist.get('genres', []))
                        track_data['genres'] = list(set(all_genres))
                    except Exception as e:
                        logger.warning(f"Failed to get genres for track {track['id']}: {str(e)}")
                        track_data['genres'] = []
                
                enriched_tracks.append(track_data)
            
            logger.info(f"Retrieved {len(enriched_tracks)} saved tracks with audio features")
            return enriched_tracks
            
        except Exception as e:
            logger.error(f"Failed to get user saved tracks: {str(e)}")
            raise
    
    def get_track_audio_features(self, access_token: str, track_ids: List[str]) -> List[Dict]:
        """
        Get audio features for specific tracks.
        
        Args:
            access_token: Valid access token
            track_ids: List of Spotify track IDs
            
        Returns:
            List of audio features for the tracks
        """
        try:
            self._set_access_token(access_token)
            
            # Get audio features (Spotify API allows max 100 tracks per request)
            all_features = []
            for i in range(0, len(track_ids), 100):
                batch_ids = track_ids[i:i+100]
                features = self.sp.audio_features(batch_ids)
                if features:
                    all_features.extend(features)
            
            logger.info(f"Retrieved audio features for {len(all_features)} tracks")
            return all_features
            
        except Exception as e:
            logger.error(f"Failed to get track audio features: {str(e)}")
            raise
    
    def get_track_genres(self, access_token: str, track_ids: List[str]) -> List[Dict]:
        """
        Get genre information for tracks by analyzing their artists.
        
        Args:
            access_token: Valid access token
            track_ids: List of Spotify track IDs
            
        Returns:
            List of genre information for the tracks
        """
        try:
            self._set_access_token(access_token)
            
            # Get tracks to extract artist IDs
            tracks = self.sp.tracks(track_ids)
            
            # Collect all unique artist IDs
            artist_ids = set()
            for track in tracks['tracks']:
                if track:
                    for artist in track['artists']:
                        artist_ids.add(artist['id'])
            
            # Get artist information including genres
            artists = self.sp.artists(list(artist_ids))
            
            # Create mapping from artist ID to genres
            artist_genres = {}
            for artist in artists['artists']:
                artist_genres[artist['id']] = artist.get('genres', [])
            
            # Map genres back to tracks
            track_genres = []
            for track in tracks['tracks']:
                if track:
                    track_artist_genres = []
                    for artist in track['artists']:
                        track_artist_genres.extend(artist_genres.get(artist['id'], []))
                    track_genres.append({
                        'track_id': track['id'],
                        'genres': list(set(track_artist_genres))
                    })
                else:
                    track_genres.append({
                        'track_id': track_ids[len(track_genres)],
                        'genres': []
                    })
            
            logger.info(f"Retrieved genre information for {len(track_genres)} tracks")
            return track_genres
            
        except Exception as e:
            logger.error(f"Failed to get track genres: {str(e)}")
            raise
    
    def create_playlist(self, access_token: str, user_id: str, name: str, 
                        description: str = "", public: bool = True) -> Dict:
        """
        Create a new playlist for the user.
        
        Args:
            access_token: Valid access token
            user_id: Spotify user ID
            name: Playlist name
            description: Playlist description
            public: Whether the playlist is public
            
        Returns:
            Created playlist information
        """
        try:
            self._set_access_token(access_token)
            
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=name,
                description=description,
                public=public
            )
            
            logger.info(f"Created playlist '{name}' with ID: {playlist['id']}")
            return {
                'id': playlist['id'],
                'name': playlist['name'],
                'description': playlist.get('description', ''),
                'public': playlist['public'],
                'external_urls': playlist['external_urls'],
                'uri': playlist['uri']
            }
            
        except Exception as e:
            logger.error(f"Failed to create playlist: {str(e)}")
            raise
    
    def add_tracks_to_playlist(self, access_token: str, playlist_id: str, 
                              track_uris: List[str]) -> bool:
        """
        Add tracks to an existing playlist.
        
        Args:
            access_token: Valid access token
            playlist_id: Spotify playlist ID
            track_uris: List of Spotify track URIs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._set_access_token(access_token)
            
            # Spotify API allows max 100 tracks per request
            for i in range(0, len(track_uris), 100):
                batch_uris = track_uris[i:i+100]
                self.sp.playlist_add_items(playlist_id, batch_uris)
            
            logger.info(f"Added {len(track_uris)} tracks to playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add tracks to playlist: {str(e)}")
            return False
    
    def get_playlist_tracks(self, access_token: str, playlist_id: str) -> List[Dict]:
        """
        Get tracks from a specific playlist.
        
        Args:
            access_token: Valid access token
            playlist_id: Spotify playlist ID
            
        Returns:
            List of tracks in the playlist
        """
        try:
            self._set_access_token(access_token)
            
            playlist = self.sp.playlist(playlist_id)
            tracks = []
            
            for item in playlist['tracks']['items']:
                track = item['track']
                if track:
                    track_data = {
                        'id': track['id'],
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']],
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'uri': track['uri'],
                        'added_at': item['added_at']
                    }
                    tracks.append(track_data)
            
            logger.info(f"Retrieved {len(tracks)} tracks from playlist {playlist_id}")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get playlist tracks: {str(e)}")
            raise
    
    def search_tracks(self, access_token: str, query: str, limit: int = 20, 
                     market: str = 'US') -> List[Dict]:
        """
        Search for tracks using Spotify's search API.
        
        Args:
            access_token: Valid access token
            query: Search query
            limit: Maximum number of results
            market: Market for search results
            
        Returns:
            List of search results
        """
        try:
            self._set_access_token(access_token)
            
            results = self.sp.search(
                q=query,
                type='track',
                limit=limit,
                market=market
            )
            
            tracks = []
            for track in results['tracks']['items']:
                track_data = {
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'album': track['album']['name'],
                    'album_id': track['album']['id'],
                    'album_images': track['album']['images'],
                    'duration_ms': track['duration_ms'],
                    'popularity': track['popularity'],
                    'external_urls': track['external_urls'],
                    'uri': track['uri']
                }
                tracks.append(track_data)
            
            logger.info(f"Search returned {len(tracks)} tracks for query: {query}")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to search tracks: {str(e)}")
            raise
