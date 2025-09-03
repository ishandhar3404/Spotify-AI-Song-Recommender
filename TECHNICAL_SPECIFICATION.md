# Spotify Playlist Recommender - Technical Specification

## Project Overview

A personalized Spotify playlist recommender with a web interface that uses content-based filtering with K-Nearest Neighbors (KNN) to generate personalized playlists based on user listening history and audio features.

## Success Criteria

- **Functional MVP**: Users can authenticate via Spotify, select mood/genre preferences, specify playlist length, and generate personalized playlists
- **Technical Excellence**: Clean, modular, well-documented code demonstrating best practices
- **Production Ready**: Deployed on cloud platform with caching, logging, and error handling
- **User Experience**: Intuitive, responsive interface supporting iterative playlist generation
- **Portfolio Quality**: Demonstrates full-stack ML, backend, frontend, and deployment skills

## Technical Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI Backend│    │   Spotify API   │
│                 │◄──►│                 │◄──►│                 │
│ - Mood/Genre UI │    │ - KNN Algorithm │    │ - OAuth Auth    │
│ - Playlist Display│   │ - Data Processing│   │ - Track Data    │
│ - User Controls │    │ - Caching Layer │    │ - Audio Features│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   SQLite/Postgres│
                       │                 │
                       │ - User Data     │
                       │ - Playlists     │
                       │ - Cache Data    │
                       └─────────────────┘
```

### Technology Stack
- **Backend**: FastAPI (Python 3.8+)
- **Frontend**: React 18+ with Tailwind CSS
- **Database**: SQLite (development) / PostgreSQL (production)
- **ML**: Custom KNN implementation with NumPy
- **Deployment**: Heroku or similar cloud platform
- **Authentication**: Spotify OAuth 2.0

## Core Features & Requirements

### 1. Spotify Authentication & Data Collection
- **OAuth 2.0 Flow**: Implement Spotify login with automatic token refresh
- **User Data Requirements**: Minimum 20-50 tracks (top tracks + saved songs)
- **Data Collection**: Fetch user's top tracks, saved songs, and track audio features
- **Caching Strategy**: Cache user data and track features to reduce API calls

### 2. KNN Recommendation Engine
- **Algorithm**: Custom KNN implementation using cosine similarity
- **Feature Vector**: Audio features (valence, energy, danceability, tempo, etc.)
- **Two-Stage Filtering**: 
  1. Genre filtering (hard filter)
  2. Mood-based KNN similarity within genre subset
- **Fallback Logic**: If genre filtering yields insufficient tracks, apply mood KNN to entire dataset

### 3. User Interface
- **Mood Selection**: 8-12 predefined moods (Energetic, Chill, Focused, Party, Relaxed, Workout)
- **Genre Selection**: Standard genres (Pop, Rock, Jazz, Electronic, Hip-Hop, Classical)
- **Playlist Length**: 5-50 songs with input validation
- **Optional Seed Track**: Select from user's top tracks to guide recommendations
- **Playlist Display**: Track info (title, artist, album, album art) with Spotify preview links

### 4. Playlist Generation & Management
- **Generation**: Create playlists based on mood/genre/length preferences
- **Iteration**: "Generate New Playlist" button with same parameters
- **Modification**: Change mood/genre/length and regenerate
- **Export Options**: Save to Spotify account or export track list
- **Memory**: Remember previous selections for easier iteration

## Implementation Priorities

### Week 1: Core MVP
1. **Project Setup**: Repository structure, dependencies, basic FastAPI app
2. **Spotify Integration**: OAuth implementation, API endpoints for user data
3. **KNN Algorithm**: Core algorithm implementation with audio features
4. **Basic Backend**: Routes for playlist generation, data processing
5. **Simple Frontend**: Basic React app with mood/genre selection
6. **Database**: User data storage and basic models

### Week 2: Enhancements & Polish
1. **Advanced Features**: Seed track selection, iterative generation
2. **Playlist Management**: Save to Spotify, export functionality
3. **Frontend Polish**: Responsive design, better UX, error handling
4. **Backend Robustness**: Caching, logging, error handling
5. **Testing**: Unit tests, integration tests, edge case handling
6. **Deployment**: Cloud platform deployment, monitoring setup

### Optional Features (Time Permitting)
- Weighted audio features for refined recommendations
- Embedded audio previews
- Advanced analytics and performance metrics
- User preference learning over time

## Project Structure

```
spotify-recommender/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models/              # Database models
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Business logic
│   │   │   ├── spotify_service.py
│   │   │   ├── knn_service.py
│   │   │   └── playlist_service.py
│   │   ├── repositories/        # Data access layer
│   │   └── utils/               # Helper functions
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── knn_algorithm.py     # Custom KNN implementation
│   │   ├── feature_processing.py # Audio feature handling
│   │   └── similarity.py        # Similarity calculations
│   ├── tests/                   # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API calls
│   │   ├── utils/               # Helper functions
│   │   └── App.js
│   ├── public/
│   ├── package.json
│   └── tailwind.config.js
├── docs/                        # Documentation
├── README.md                    # Project overview and setup
└── docker-compose.yml           # Local development
```

## Data Models

### User Model
```python
class User:
    id: str                    # Spotify user ID
    access_token: str          # Encrypted Spotify access token
    refresh_token: str         # Encrypted Spotify refresh token
    top_tracks: List[Track]    # User's top tracks
    saved_tracks: List[Track]  # User's saved tracks
    created_at: datetime
    updated_at: datetime
```

### Track Model
```python
class Track:
    id: str                    # Spotify track ID
    title: str                 # Track title
    artist: str                # Artist name
    album: str                 # Album name
    album_art: str             # Album art URL
    audio_features: dict       # Spotify audio features
    genres: List[str]          # Associated genres
    created_at: datetime
```

### Playlist Model
```python
class Playlist:
    id: str                    # Generated playlist ID
    user_id: str               # User who generated it
    tracks: List[Track]        # Recommended tracks
    mood: str                  # Selected mood
    genre: Optional[str]       # Selected genre (optional)
    length: int                # Requested playlist length
    seed_track: Optional[str]  # Optional seed track ID
    created_at: datetime
```

## API Endpoints

### Authentication
- `POST /auth/spotify/login` - Initiate Spotify OAuth
- `GET /auth/spotify/callback` - OAuth callback handler
- `POST /auth/refresh` - Refresh expired tokens

### User Data
- `GET /api/user/profile` - Get user profile and track data
- `GET /api/user/tracks` - Get user's top and saved tracks
- `POST /api/user/refresh-data` - Refresh user data from Spotify

### Playlist Generation
- `POST /api/playlists/generate` - Generate new playlist
- `GET /api/playlists/{id}` - Get playlist details
- `POST /api/playlists/{id}/regenerate` - Generate new playlist with same params
- `POST /api/playlists/{id}/save-to-spotify` - Save playlist to Spotify

### Analytics
- `GET /api/analytics/performance` - ML model performance metrics
- `GET /api/analytics/system` - System performance metrics

## KNN Algorithm Specification

### Feature Vector
```python
audio_features = {
    'valence': float,        # Musical positiveness (0.0 to 1.0)
    'energy': float,         # Perceived energy (0.0 to 1.0)
    'danceability': float,   # Danceability (0.0 to 1.0)
    'tempo': float,          # Tempo in BPM
    'acousticness': float,   # Acoustic vs electronic (0.0 to 1.0)
    'instrumentalness': float, # Instrumental vs vocal (0.0 to 1.0)
    'liveness': float,       # Presence of audience (0.0 to 1.0)
    'speechiness': float     # Presence of speech (0.0 to 1.0)
}
```

### Similarity Calculation
```python
def cosine_similarity(vector_a, vector_b):
    """Calculate cosine similarity between two feature vectors"""
    dot_product = np.dot(vector_a, vector_b)
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    return dot_product / (norm_a * norm_b)

def knn_recommendations(user_tracks, available_tracks, mood, genre, k=20):
    """Generate recommendations using KNN algorithm"""
    # 1. Filter by genre if specified
    if genre and genre != "All Genres":
        available_tracks = filter_by_genre(available_tracks, genre)
    
    # 2. Calculate average feature vector from user's top tracks
    user_feature_vector = calculate_average_features(user_tracks)
    
    # 3. Find k-nearest neighbors using cosine similarity
    similarities = []
    for track in available_tracks:
        similarity = cosine_similarity(user_feature_vector, track.audio_features)
        similarities.append((track, similarity))
    
    # 4. Sort by similarity and return top k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [track for track, _ in similarities[:k]]
```

## Error Handling & Edge Cases

### Input Validation
- Playlist length: 5-50 songs with clear error messages
- Required fields: Mood selection, user authentication
- Optional fields: Genre selection, seed track

### Data Availability
- Insufficient tracks: Inform user and suggest adding more music
- Genre filtering: Return available tracks with explanation
- API failures: Graceful degradation and retry mechanisms

### User Experience
- Loading states for API calls
- Clear error messages and user guidance
- Fallback options when primary features fail

## Performance Requirements

### Response Times
- Playlist generation: < 3 seconds
- User data fetch: < 2 seconds
- Page load: < 1 second

### Scalability
- Support multiple concurrent users
- Efficient caching to reduce API calls
- Database query optimization

### Reliability
- 99% uptime for deployed version
- Graceful handling of Spotify API rate limits
- Robust error handling and logging

## Testing Strategy

### Unit Tests
- KNN algorithm implementation
- Feature processing functions
- Data validation utilities

### Integration Tests
- Spotify API endpoints
- Database operations
- Full playlist generation flow

### End-to-End Tests
- Complete user journey
- Error handling scenarios
- Edge case validation

### Manual Testing
- User experience validation
- Cross-browser compatibility
- Mobile responsiveness

## Deployment & Monitoring

### Development Environment
- Local FastAPI server with hot reload
- SQLite database for development
- React development server

### Production Deployment
- Heroku or similar cloud platform
- PostgreSQL database
- Environment variable configuration
- SSL certificate setup

### Monitoring & Logging
- API response time tracking
- Error rate monitoring
- User behavior analytics
- ML model performance metrics

## Security Considerations

### Data Protection
- Encrypt sensitive tokens in database
- Secure OAuth flow implementation
- Input validation and sanitization

### API Security
- Rate limiting for public endpoints
- CORS configuration
- Secure headers and HTTPS enforcement

## Documentation Requirements

### Code Documentation
- Comprehensive docstrings for all functions
- Clear variable and function naming
- Inline comments for complex logic

### User Documentation
- Setup and installation instructions
- API usage examples
- Troubleshooting guide

### Technical Documentation
- Architecture decisions and rationale
- Deployment procedures
- Testing and maintenance guides

## Success Metrics

### Technical Metrics
- API response times < 3 seconds
- Cache hit rate > 80%
- Error rate < 1%
- Test coverage > 90%

### User Experience Metrics
- Successful playlist generation rate > 95%
- User session completion rate > 80%
- Feature usage distribution across moods/genres

### ML Model Metrics
- Average similarity scores for recommendations
- Genre/mood matching accuracy
- User satisfaction with generated playlists

## Timeline & Milestones

### Week 1: Core MVP
- **Day 1-2**: Project setup, Spotify API integration
- **Day 3-4**: KNN algorithm implementation, basic backend
- **Day 5-7**: Simple frontend, database setup, basic testing

### Week 2: Enhancements & Deployment
- **Day 8-10**: Advanced features, frontend polish
- **Day 11-12**: Testing, error handling, performance optimization
- **Day 13-14**: Deployment, monitoring setup, final testing

## Risk Mitigation

### Technical Risks
- Spotify API changes: Use stable endpoints and versioning
- Performance issues: Implement caching and optimization early
- Deployment challenges: Test deployment process in development

### Timeline Risks
- Scope creep: Focus on MVP features first
- Technical blockers: Research Spotify API thoroughly before starting
- Testing delays: Write tests alongside development

## Future Enhancements

### Phase 2 Features
- User preference learning over time
- Collaborative filtering recommendations
- Advanced audio feature analysis
- Social sharing and discovery

### Scalability Improvements
- Multi-user support with user management
- Advanced caching strategies
- Database optimization and indexing
- Microservices architecture

---

This specification provides a comprehensive roadmap for building a production-ready Spotify playlist recommender that will showcase your full-stack development, machine learning, and deployment skills. The project is designed to be both technically impressive and practically useful, making it an excellent portfolio piece for your resume.
