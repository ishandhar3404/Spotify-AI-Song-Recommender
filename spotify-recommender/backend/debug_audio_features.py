#!/usr/bin/env python3
"""
Debug script to test audio features API call
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import json

def test_audio_features_direct():
    """Test audio features API call directly with requests"""
    
    # Load credentials
    from app.config import settings
    
    print("Testing audio features API directly...")
    
    # Get client credentials token
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET
    )
    
    # Get access token
    token_info = client_credentials_manager.get_access_token()
    token = token_info['access_token']
    print(f"Got access token: {token[:20]}...")
    
    # Test track ID - using a known working track
    track_id = "2takcwOaAZWiXQijPHIx7B"  # From the documentation example
    
    # Test direct API call
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test single track
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Direct API call works!")
            print(f"Sample features: {list(data.keys())[:5]}")
        else:
            print(f"❌ Direct API call failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Direct API call error: {e}")
    
    # Test with query parameter format
    url2 = f"https://api.spotify.com/v1/audio-features?ids={track_id}"
    print(f"\nTesting URL: {url2}")
    
    try:
        response = requests.get(url2, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Query parameter API call works!")
            print(f"Sample features: {list(data.keys())[:5]}")
        else:
            print(f"❌ Query parameter API call failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Query parameter API call error: {e}")

def test_spotipy_audio_features():
    """Test audio features with spotipy library"""
    
    from app.config import settings
    
    print("\nTesting audio features with spotipy...")
    
    # Get client credentials token
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET
    )
    
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Test track ID - using a known working track
    track_id = "2takcwOaAZWiXQijPHIx7B"  # From the documentation example
    
    try:
        # Test single track
        features = sp.audio_features([track_id])
        print(f"Spotipy response: {features}")
        
        if features and features[0]:
            print("✅ Spotipy audio features works!")
            print(f"Sample features: {list(features[0].keys())[:5]}")
        else:
            print("❌ Spotipy audio features failed - no data")
            
    except Exception as e:
        print(f"❌ Spotipy audio features error: {e}")

if __name__ == "__main__":
    print("🔍 Audio Features API Debug")
    print("="*50)
    
    test_audio_features_direct()
    test_spotipy_audio_features()
