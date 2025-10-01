#!/usr/bin/env python3
"""
Test user authentication flow
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import json

def test_user_auth_flow():
    """Test the complete user authentication flow"""
    
    from app.config import settings
    
    print("Testing User Authentication Flow...")
    print("="*50)
    
    # Check if we have a user in the database
    import sqlite3
    conn = sqlite3.connect('spotify_recommender.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, display_name, access_token, token_expires_at FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users found in database")
        print("You need to authenticate a user first through the web interface")
        conn.close()
        return False
    
    user_id, display_name, access_token, expires_at = user
    print(f"Found user: {display_name} (ID: {user_id})")
    print(f"Token expires at: {expires_at}")
    
    if not access_token:
        print("❌ User has no access token")
        conn.close()
        return False
    
    # Test API calls with user token
    try:
        sp = spotipy.Spotify(auth=access_token)
        
        # Test user profile
        print("\n1. Testing user profile...")
        user_profile = sp.current_user()
        print(f"✅ User profile: {user_profile.get('display_name')}")
        
        # Test getting user's top tracks
        print("\n2. Testing user's top tracks...")
        top_tracks = sp.current_user_top_tracks(limit=5)
        print(f"✅ Top tracks: {len(top_tracks['items'])} tracks found")
        
        if top_tracks['items']:
            # Test audio features with user's tracks
            print("\n3. Testing audio features with user authentication...")
            track_ids = [track['id'] for track in top_tracks['items'][:3]]
            print(f"Testing audio features for tracks: {track_ids}")
            
            audio_features = sp.audio_features(track_ids)
            if audio_features and all(audio_features):
                print("✅ Audio features work with user authentication!")
                for i, features in enumerate(audio_features):
                    if features:
                        print(f"  Track {i+1}: {list(features.keys())[:5]}")
                return True
            else:
                print("❌ Audio features failed with user authentication")
                print(f"Response: {audio_features}")
                return False
        
    except Exception as e:
        print(f"❌ User authentication test failed: {e}")
        if "401" in str(e):
            print("  -> Token expired or invalid")
            print("  -> Need to refresh token or re-authenticate")
        elif "403" in str(e):
            print("  -> Insufficient permissions")
        conn.close()
        return False
    
    conn.close()
    return True

def test_token_refresh():
    """Test token refresh functionality"""
    
    from app.config import settings
    from app.services.spotify_service import SpotifyService
    
    print("\n" + "="*50)
    print("Testing Token Refresh...")
    print("="*50)
    
    # Check if we have a user with refresh token
    import sqlite3
    conn = sqlite3.connect('spotify_recommender.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, display_name, refresh_token FROM users WHERE refresh_token IS NOT NULL LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users with refresh tokens found")
        conn.close()
        return False
    
    user_id, display_name, refresh_token = user
    print(f"Found user with refresh token: {display_name}")
    
    # Test token refresh
    try:
        spotify_service = SpotifyService(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI
        )
        
        new_tokens = spotify_service.refresh_access_token(refresh_token)
        print("✅ Token refresh successful!")
        print(f"New access token: {new_tokens['access_token'][:20]}...")
        print(f"Expires at: {new_tokens['expires_at']}")
        
        # Update database with new token
        cursor.execute("""
            UPDATE users 
            SET access_token = ?, token_expires_at = ?
            WHERE id = ?
        """, (new_tokens['access_token'], new_tokens['expires_at'], user_id))
        
        conn.commit()
        print("✅ Database updated with new token")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
        conn.close()
        return False

if __name__ == "__main__":
    print("🔍 User Authentication Test")
    print("="*50)
    
    # Test user authentication
    auth_works = test_user_auth_flow()
    
    # Test token refresh
    refresh_works = test_token_refresh()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"User authentication: {'✅' if auth_works else '❌'}")
    print(f"Token refresh: {'✅' if refresh_works else '❌'}")
    
    if auth_works or refresh_works:
        print("\n🎉 User authentication is working!")
        print("You can now test the full recommendation system.")
    else:
        print("\n💥 User authentication needs to be fixed.")
        print("Try re-authenticating through the web interface.")
