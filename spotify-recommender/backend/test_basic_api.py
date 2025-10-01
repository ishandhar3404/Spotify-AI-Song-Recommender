#!/usr/bin/env python3
"""
Test basic Spotify API access
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import json

def test_basic_api():
    """Test basic Spotify API endpoints"""
    
    from app.config import settings
    
    print("Testing basic Spotify API access...")
    
    # Get client credentials token
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET
    )
    
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Test 1: Search API
    print("\n1. Testing Search API...")
    try:
        results = sp.search(q="test", type="track", limit=1)
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            print(f"✅ Search works! Found track: {track['name']} by {track['artists'][0]['name']}")
            print(f"Track ID: {track['id']}")
            return track['id']  # Return the track ID for further testing
        else:
            print("❌ Search returned no results")
            return None
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return None

def test_track_details(track_id):
    """Test getting track details"""
    
    from app.config import settings
    
    print(f"\n2. Testing Track Details for {track_id}...")
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET
    )
    
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    try:
        track = sp.track(track_id)
        print(f"✅ Track details work! Track: {track['name']}")
        print(f"Popularity: {track['popularity']}")
        print(f"Duration: {track['duration_ms']}ms")
        return True
    except Exception as e:
        print(f"❌ Track details failed: {e}")
        return False

def test_audio_features(track_id):
    """Test audio features API"""
    
    from app.config import settings
    
    print(f"\n3. Testing Audio Features for {track_id}...")
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET
    )
    
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    try:
        features = sp.audio_features([track_id])
        if features and features[0]:
            print(f"✅ Audio features work! Features: {list(features[0].keys())[:5]}")
            return True
        else:
            print("❌ Audio features returned no data")
            return False
    except Exception as e:
        print(f"❌ Audio features failed: {e}")
        return False

def test_artist_details(track_id):
    """Test getting artist details"""
    
    from app.config import settings
    
    print(f"\n4. Testing Artist Details...")
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET
    )
    
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    try:
        # Get track first to get artist ID
        track = sp.track(track_id)
        artist_id = track['artists'][0]['id']
        
        # Get artist details
        artist = sp.artist(artist_id)
        print(f"✅ Artist details work! Artist: {artist['name']}")
        print(f"Genres: {artist.get('genres', [])[:3]}")
        return True
    except Exception as e:
        print(f"❌ Artist details failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Basic Spotify API Test")
    print("="*50)
    
    # Test basic API access
    track_id = test_basic_api()
    
    if track_id:
        # Test other endpoints
        test_track_details(track_id)
        test_audio_features(track_id)
        test_artist_details(track_id)
    
    print("\n" + "="*50)
    print("Test completed!")
