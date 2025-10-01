#!/usr/bin/env python3
"""
Test script to debug Spotify API issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import json

def test_spotify_connection():
    """Test basic Spotify API connection"""
    
    # Load credentials
    from app.config import settings
    
    print("Testing Spotify API connection...")
    print(f"Client ID: {settings.SPOTIFY_CLIENT_ID[:10]}...")
    print(f"Redirect URI: {settings.SPOTIFY_REDIRECT_URI}")
    
    # Test 1: Check if credentials are valid by getting client credentials token
    try:
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test basic API call
        results = sp.search(q="test", type="track", limit=1)
        print("✅ Basic Spotify API connection works")
        
        # Test audio features endpoint with a known track
        test_track_id = "4iV5W9uYEdYUVa79Axb7Rh"  # A popular track
        audio_features = sp.audio_features([test_track_id])
        
        if audio_features and audio_features[0]:
            print("✅ Audio features API call works with client credentials")
            print(f"Sample audio features: {list(audio_features[0].keys())}")
        else:
            print("❌ Audio features API call failed")
            
    except Exception as e:
        print(f"❌ Spotify API connection failed: {e}")
        return False
    
    # Test 2: Check OAuth flow (without actual authorization)
    try:
        scope = " ".join([
            "user-read-private",
            "user-read-email", 
            "user-top-read",
            "user-library-read",
            "playlist-read-private",
            "playlist-modify-public",
            "playlist-modify-private"
        ])
        
        auth_manager = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope=scope
        )
        
        auth_url = auth_manager.get_authorize_url()
        print("✅ OAuth URL generation works")
        print(f"Auth URL: {auth_url[:100]}...")
        
    except Exception as e:
        print(f"❌ OAuth setup failed: {e}")
        return False
    
    # Test 3: Check if the issue is with the specific track IDs
    print("\nTesting with different track IDs...")
    test_track_ids = [
        "4iV5W9uYEdYUVa79Axb7Rh",  # Popular track
        "7bO7a1KrtmGNDIOy2u3siZ",  # Track from your logs
        "5116BQqgzOZ24Dx0ZKkagU"   # Another track from your logs
    ]
    
    for track_id in test_track_ids:
        try:
            audio_features = sp.audio_features([track_id])
            if audio_features and audio_features[0]:
                print(f"✅ Track {track_id}: Audio features available")
            else:
                print(f"❌ Track {track_id}: No audio features")
        except Exception as e:
            print(f"❌ Track {track_id}: Error - {e}")
    
    return True

def test_user_authentication():
    """Test user authentication flow"""
    print("\n" + "="*50)
    print("Testing User Authentication Flow")
    print("="*50)
    
    from app.config import settings
    
    # Check if we have a user in the database with valid tokens
    import sqlite3
    conn = sqlite3.connect('spotify_recommender.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, display_name, access_token, token_expires_at FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users found in database")
        conn.close()
        return False
    
    user_id, display_name, access_token, expires_at = user
    print(f"Found user: {display_name} (ID: {user_id})")
    print(f"Has access token: {bool(access_token)}")
    print(f"Token expires at: {expires_at}")
    
    if not access_token:
        print("❌ User has no access token")
        conn.close()
        return False
    
    # Test API calls with user token
    try:
        sp = spotipy.Spotify(auth=access_token)
        
        # Test user profile
        user_profile = sp.current_user()
        print(f"✅ User profile: {user_profile.get('display_name')}")
        
        # Test getting user's top tracks
        top_tracks = sp.current_user_top_tracks(limit=5)
        print(f"✅ Top tracks: {len(top_tracks['items'])} tracks found")
        
        # Test audio features with user's tracks
        if top_tracks['items']:
            track_ids = [track['id'] for track in top_tracks['items'][:3]]
            print(f"Testing audio features for tracks: {track_ids}")
            
            audio_features = sp.audio_features(track_ids)
            if audio_features and all(audio_features):
                print("✅ Audio features work with user authentication")
                for i, features in enumerate(audio_features):
                    if features:
                        print(f"  Track {i+1}: {list(features.keys())[:5]}...")
            else:
                print("❌ Audio features failed with user authentication")
                print(f"Response: {audio_features}")
        
    except Exception as e:
        print(f"❌ User authentication test failed: {e}")
        if "401" in str(e):
            print("  -> Token expired or invalid")
        elif "403" in str(e):
            print("  -> Insufficient permissions")
        conn.close()
        return False
    
    conn.close()
    return True

if __name__ == "__main__":
    print("🔍 Spotify API Debug Test")
    print("="*50)
    
    # Test basic connection
    basic_works = test_spotify_connection()
    
    # Test user authentication
    user_works = test_user_authentication()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Basic API connection: {'✅' if basic_works else '❌'}")
    print(f"User authentication: {'✅' if user_works else '❌'}")
    
    if basic_works and user_works:
        print("\n🎉 All tests passed! Spotify API should work.")
    else:
        print("\n💥 Some tests failed. Check the issues above.")
