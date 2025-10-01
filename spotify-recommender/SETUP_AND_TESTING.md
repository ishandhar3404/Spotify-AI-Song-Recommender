# Spotify Playlist Recommender - Setup & Testing Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Spotify Developer Account

### 1. Backend Setup

```bash
cd spotify-recommender/backend

# Activate virtual environment (if not already active)
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd spotify-recommender/frontend

# Install dependencies
npm install

# Start the frontend development server
npm run dev
```

### 3. Environment Configuration

The environment files are already configured:
- **Backend**: `backend/env.local`
- **Frontend**: `frontend/env.local`

## 🔧 Testing the Implementation

### Test Authentication Flow

1. **Start both servers** (backend on port 8000, frontend on port 3000)
2. **Navigate to** `http://localhost:3000`
3. **Click "Connect Spotify"** - should redirect to Spotify OAuth
4. **Authorize the app** - should redirect back to frontend with success
5. **Verify login** - should show dashboard with user data

### Test Playlist Generation

1. **Ensure you're logged in** and have at least 20 tracks in your Spotify library
2. **Navigate to** the playlist generator page
3. **Select mood** (e.g., "Energetic")
4. **Choose genre** (optional)
5. **Set playlist length** (5-50 songs)
6. **Click "Generate Playlist"** - should create a playlist with recommendations
7. **Test regenerate** - should create a new playlist with same parameters
8. **Test save to Spotify** - should save playlist to your Spotify account

## 🐛 Troubleshooting

### Common Issues

1. **"Failed to load your music library"**
   - Ensure you have at least 20 tracks in your Spotify library
   - Check if Spotify API credentials are correct

2. **"Authentication failed"**
   - Verify Spotify app settings match the redirect URI
   - Check if backend and frontend are running on correct ports

3. **"CORS errors"**
   - Ensure frontend URL is in backend's ALLOWED_ORIGINS
   - Check if both servers are running

4. **"Token expired"**
   - The app should auto-refresh tokens
   - If persistent, try logging out and back in

### Debug Mode

Enable debug logging by setting `DEBUG=True` in `backend/env.local`

## 📊 What's Implemented

### ✅ Backend Features
- **Complete Authentication Flow** - Spotify OAuth with token refresh
- **Playlist Generation** - KNN algorithm with mood/genre filtering
- **User Management** - Profile and track data fetching
- **Database Integration** - SQLite with proper models
- **API Endpoints** - All CRUD operations for playlists

### ✅ Frontend Features
- **Authentication UI** - Login/logout with Spotify integration
- **Playlist Generator** - Beautiful form with mood/genre selection
- **Track Display** - Album art, metadata, and Spotify links
- **Error Handling** - Comprehensive error messages and loading states
- **Responsive Design** - Works on mobile and desktop

### ✅ Integration Features
- **Real-time Generation** - Instant playlist creation
- **Spotify Integration** - Save playlists directly to Spotify
- **Recommendation Quality** - Shows similarity metrics
- **Custom Playlist Names** - User can name their playlists

## 🎯 Next Steps

The core functionality is complete! You can now:

1. **Test the full flow** from login to playlist generation
2. **Customize the UI** with your preferred styling
3. **Add more features** like playlist history, sharing, etc.
4. **Deploy to production** with proper environment variables

## 🔗 API Endpoints

### Authentication
- `GET /auth/spotify/login` - Initiate Spotify OAuth
- `GET /auth/callback` - Handle OAuth callback
- `POST /auth/refresh` - Refresh access token
- `GET /auth/status` - Check authentication status

### Playlists
- `POST /api/playlists/generate` - Generate new playlist
- `GET /api/playlists/list` - Get user's playlists
- `POST /api/playlists/{id}/regenerate` - Regenerate playlist
- `POST /api/playlists/{id}/save-to-spotify` - Save to Spotify

### User
- `GET /api/user/profile` - Get user profile
- `GET /api/user/tracks` - Get user's tracks

The application is now fully functional and ready for testing! 🎉
