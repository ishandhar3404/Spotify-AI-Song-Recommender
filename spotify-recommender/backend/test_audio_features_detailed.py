#!/usr/bin/env python3
"""
Detailed test of audio features API to understand the 403 errors
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import json

def test_audio_features_with_different_approaches():
    """Test audio features API with different approaches"""
    
    from app.config import settings
    
    print("🔍 Detailed Audio Features API Test")
    print("="*60)
    
    # Get fresh user token
    import sqlite3
    conn = sqlite3.connect('spotify_recommender.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, display_name, access_token FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users found")
        return False
    
    user_id, display_name, access_token = user
    print(f"Testing with user: {display_name}")
    print(f"Access token: {access_token[:20]}...")
    
    # Test different approaches
    sp = spotipy.Spotify(auth=access_token)
    
    # Get user's top tracks first
    print("\n1. Getting user's top tracks...")
    try:
        top_tracks = sp.current_user_top_tracks(limit=5)
        track_ids = [track['id'] for track in top_tracks['items']]
        print(f"✅ Got {len(track_ids)} tracks: {track_ids}")
    except Exception as e:
        print(f"❌ Failed to get top tracks: {e}")
        return False
    
    # Test 1: Single track audio features
    print(f"\n2. Testing single track audio features...")
    test_track_id = track_ids[0]
    try:
        features = sp.audio_features([test_track_id])
        if features and features[0]:
            print(f"✅ Single track audio features work!")
            print(f"Features: {list(features[0].keys())}")
            return True
        else:
            print(f"❌ Single track returned no data")
    except Exception as e:
        print(f"❌ Single track failed: {e}")
    
    # Test 2: Multiple tracks audio features
    print(f"\n3. Testing multiple tracks audio features...")
    try:
        features = sp.audio_features(track_ids[:3])
        if features and all(features):
            print(f"✅ Multiple tracks audio features work!")
            print(f"Got features for {len(features)} tracks")
            return True
        else:
            print(f"❌ Multiple tracks returned partial data")
    except Exception as e:
        print(f"❌ Multiple tracks failed: {e}")
    
    # Test 3: Direct API call
    print(f"\n4. Testing direct API call...")
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test single track
        url = f"https://api.spotify.com/v1/audio-features/{test_track_id}"
        response = requests.get(url, headers=headers)
        print(f"Direct API status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Direct API call works!")
            print(f"Features: {list(data.keys())}")
            return True
        else:
            print(f"❌ Direct API failed: {response.text}")
    except Exception as e:
        print(f"❌ Direct API error: {e}")
    
    # Test 4: Check if it's a specific track issue
    print(f"\n5. Testing with different track IDs...")
    test_track_ids = [
        "4iV5W9uYEdYUVa79Axb7Rh",  # Popular track
        "2takcwOaAZWiXQijPHIx7B",  # Documentation example
        track_ids[0]  # User's track
    ]
    
    for track_id in test_track_ids:
        try:
            features = sp.audio_features([track_id])
            if features and features[0]:
                print(f"✅ Track {track_id} works!")
                return True
            else:
                print(f"❌ Track {track_id} returned no data")
        except Exception as e:
            print(f"❌ Track {track_id} failed: {e}")
    
    conn.close()
    return False

def test_alternative_approaches():
    """Test alternative approaches if audio features don't work"""
    
    from app.config import settings
    
    print("\n" + "="*60)
    print("🔄 Testing Alternative Approaches")
    print("="*60)
    
    # Get user token
    import sqlite3
    conn = sqlite3.connect('spotify_recommender.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT access_token FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users found")
        return False
    
    access_token = user[0]
    sp = spotipy.Spotify(auth=access_token)
    
    # Test 1: Get user's saved tracks
    print("\n1. Testing user's saved tracks...")
    try:
        saved_tracks = sp.current_user_saved_tracks(limit=10)
        print(f"✅ Got {len(saved_tracks['items'])} saved tracks")
        
        # Get track details
        track_ids = [item['track']['id'] for item in saved_tracks['items']]
        tracks = sp.tracks(track_ids)
        
        print(f"✅ Got track details for {len(tracks['tracks'])} tracks")
        
        # Check what data we have
        sample_track = tracks['tracks'][0]
        print(f"Sample track data: {list(sample_track.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Saved tracks failed: {e}")
        return False
    
    # Test 2: Get user's playlists
    print("\n2. Testing user's playlists...")
    try:
        playlists = sp.current_user_playlists(limit=5)
        print(f"✅ Got {len(playlists['items'])} playlists")
        
        if playlists['items']:
            playlist_id = playlists['items'][0]['id']
            playlist_tracks = sp.playlist_tracks(playlist_id, limit=10)
            print(f"✅ Got {len(playlist_tracks['items'])} tracks from playlist")
        
        return True
        
    except Exception as e:
        print(f"❌ Playlists failed: {e}")
        return False
    
    conn.close()
    return False

if __name__ == "__main__":
    print("🎵 Audio Features & Alternative Data Test")
    print("="*60)
    
    # Test audio features
    audio_features_work = test_audio_features_with_different_approaches()
    
    # Test alternatives
    alternatives_work = test_alternative_approaches()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Audio features API: {'✅' if audio_features_work else '❌'}")
    print(f"Alternative data sources: {'✅' if alternatives_work else '❌'}")
    
    if audio_features_work:
        print("\n🎉 Audio features work! You can use ML on Spotify's data.")
    elif alternatives_work:
        print("\n🔄 Audio features don't work, but alternatives do!")
        print("You can still build a recommendation system using:")
        print("- User's saved tracks")
        print("- Playlist data")
        print("- Track metadata (name, artist, album)")
        print("- Popularity and other basic features")
    else:
        print("\n💥 Both approaches failed. Need to debug further.")
