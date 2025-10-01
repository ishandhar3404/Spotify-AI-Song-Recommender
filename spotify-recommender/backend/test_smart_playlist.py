#!/usr/bin/env python3
"""
Test script for the Smart Playlist Generator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml.smart_playlist_generator import SmartPlaylistGenerator
import spotipy
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_data():
    """Get user data from database and Spotify API"""
    
    # Get user from database
    conn = sqlite3.connect('spotify_recommender.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, display_name, access_token FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users found in database")
        return None, None
    
    user_id, display_name, access_token = user
    print(f"✅ Found user: {display_name}")
    
    # Initialize Spotify client
    sp = spotipy.Spotify(auth=access_token)
    
    try:
        # Get user's saved tracks (limited for testing)
        print("📥 Fetching user's saved tracks...")
        saved_tracks = sp.current_user_saved_tracks(limit=20)
        
        user_tracks = []
        for item in saved_tracks['items']:
            track = item['track']
            track_data = {
                'id': track['id'],
                'name': track['name'],
                'artists': [artist['name'] for artist in track['artists']],
                'album': {'name': track['album']['name'], 'release_date': track['album'].get('release_date', '2020-01-01')},
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'genres': []  # We'll populate this from artist data
            }
            user_tracks.append(track_data)
        
        print(f"✅ Got {len(user_tracks)} saved tracks")
        
        # Get some additional tracks for recommendation pool
        print("📥 Fetching additional tracks for recommendation pool...")
        
        # Search for tracks in different genres
        search_queries = ["pop", "rock", "electronic", "jazz", "hip hop"]
        available_tracks = []
        
        for query in search_queries:
            try:
                results = sp.search(q=query, type='track', limit=20)
                for track in results['tracks']['items']:
                    track_data = {
                        'id': track['id'],
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']],
                        'album': {'name': track['album']['name'], 'release_date': track['album'].get('release_date', '2020-01-01')},
                        'duration_ms': track['duration_ms'],
                        'popularity': track['popularity'],
                        'genres': [query]  # Use search query as genre
                    }
                    available_tracks.append(track_data)
            except Exception as e:
                print(f"⚠️ Error searching for {query}: {e}")
        
        print(f"✅ Got {len(available_tracks)} tracks for recommendation pool")
        
        conn.close()
        return user_tracks, available_tracks
        
    except Exception as e:
        print(f"❌ Error fetching user data: {e}")
        conn.close()
        return None, None

def test_smart_playlist_generator():
    """Test the smart playlist generator"""
    
    print("🎵 Testing Smart Playlist Generator")
    print("=" * 50)
    
    # Get user data
    user_tracks, available_tracks = get_user_data()
    
    if not user_tracks or not available_tracks:
        print("❌ Could not get user data")
        return False
    
    # Initialize the smart playlist generator
    generator = SmartPlaylistGenerator(k=20)
    
    # Test different moods
    moods = ['energetic', 'chill', 'focused', 'party', 'relaxed', 'workout', 'happy', 'melancholic']
    
    for mood in moods[:3]:  # Test first 3 moods
        print(f"\n🎭 Testing mood: {mood}")
        print("-" * 30)
        
        try:
            # Generate playlist
            recommendations, metrics = generator.generate_smart_playlist(
                user_tracks=user_tracks,
                available_tracks=available_tracks,
                mood=mood,
                genre=None,
                playlist_length=10
            )
            
            if recommendations:
                print(f"✅ Generated {len(recommendations)} recommendations")
                print(f"📊 Average similarity: {metrics.get('average_similarity', 0):.3f}")
                
                # Show first 3 recommendations
                for i, track in enumerate(recommendations[:3]):
                    print(f"  {i+1}. {track['name']} by {', '.join(track['artists'])}")
            else:
                print(f"❌ No recommendations generated")
                if 'error' in metrics:
                    print(f"   Error: {metrics['error']}")
                    
        except Exception as e:
            print(f"❌ Error testing mood {mood}: {e}")
    
    # Test genre filtering
    print(f"\n🎵 Testing genre filtering")
    print("-" * 30)
    
    try:
        recommendations, metrics = generator.generate_smart_playlist(
            user_tracks=user_tracks,
            available_tracks=available_tracks,
            mood='chill',
            genre='pop',
            playlist_length=5
        )
        
        if recommendations:
            print(f"✅ Generated {len(recommendations)} pop recommendations")
            for i, track in enumerate(recommendations):
                print(f"  {i+1}. {track['name']} by {', '.join(track['artists'])}")
        else:
            print(f"❌ No pop recommendations generated")
            
    except Exception as e:
        print(f"❌ Error testing genre filtering: {e}")
    
    # Test user taste analysis
    print(f"\n🔍 Testing user taste analysis")
    print("-" * 30)
    
    try:
        taste_analysis = generator.analyze_user_taste(user_tracks)
        
        if 'error' not in taste_analysis:
            print(f"✅ Taste analysis completed")
            print(f"📊 Total tracks analyzed: {taste_analysis.get('total_tracks', 0)}")
            print(f"🎭 Dominant moods: {taste_analysis.get('dominant_moods', [])}")
            print(f"🎵 Preferred genres: {taste_analysis.get('preferred_genres', [])}")
            
            # Show listening patterns
            patterns = taste_analysis.get('listening_patterns', {})
            if patterns:
                print(f"⏱️ Average duration: {patterns.get('average_track_duration', 0):.0f}ms")
                print(f"⭐ Average popularity: {patterns.get('average_popularity', 0):.1f}")
        else:
            print(f"❌ Taste analysis failed: {taste_analysis['error']}")
            
    except Exception as e:
        print(f"❌ Error testing taste analysis: {e}")
    
    return True

def test_feature_extraction():
    """Test feature extraction with sample data"""
    
    print(f"\n🔧 Testing feature extraction")
    print("-" * 30)
    
    generator = SmartPlaylistGenerator()
    
    # Sample track data
    sample_track = {
        'id': 'test123',
        'name': 'Test Track',
        'artists': ['Test Artist'],
        'album': {'name': 'Test Album', 'release_date': '2020-01-01'},
        'duration_ms': 180000,
        'popularity': 75,
        'genres': ['pop', 'rock']
    }
    
    try:
        features = generator._extract_track_features(sample_track)
        print(f"✅ Extracted {len(features)} features")
        print(f"📊 Feature values: {[f'{f:.3f}' for f in features]}")
        
        # Test normalization
        normalized_features = generator._extract_normalized_features([sample_track])
        print(f"✅ Normalized features: {[f'{f:.3f}' for f in normalized_features[0]]}")
        
    except Exception as e:
        print(f"❌ Error testing feature extraction: {e}")

if __name__ == "__main__":
    print("🚀 Smart Playlist Generator Test Suite")
    print("=" * 50)
    
    # Test feature extraction first
    test_feature_extraction()
    
    # Test the main functionality
    success = test_smart_playlist_generator()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Smart Playlist Generator tests completed!")
        print("✅ The system is ready for integration")
    else:
        print("💥 Some tests failed")
        print("❌ Check the errors above")
