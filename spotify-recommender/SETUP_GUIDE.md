# Spotify Playlist Recommender - Setup Guide

## Prerequisites
- Node.js 16+ and npm installed
- Python 3.8+ installed
- Spotify Developer account

## Environment Setup

### 1. Spotify Developer Dashboard Configuration

**IMPORTANT**: You need to update your Spotify app settings:

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click on your app
3. Go to "Edit Settings"
4. Update the **Redirect URIs** to include:
   - `http://127.0.0.1:3000/auth/callback`

### 2. Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd spotify-recommender/backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Rename environment file:**
   ```bash
   # Copy the environment template
   copy env.local .env
   ```

6. **Start the backend server:**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 3. Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd spotify-recommender/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Rename environment file:**
   ```bash
   # Copy the environment template
   copy env.local .env
   ```

4. **Start the frontend server:**
   ```bash
   npm run dev
   ```

## Testing the Application

1. **Open your browser** to `http://localhost:3000`
2. **Click "Connect with Spotify"**
3. **Authorize the application** in Spotify
4. **You should be redirected back** to the dashboard
5. **Try generating a playlist** with different moods and genres

## Troubleshooting

### Common Issues:

1. **CORS Errors**: Make sure both servers are running on the correct ports
2. **Authentication Failures**: Verify your Spotify app redirect URIs are correct
3. **API Errors**: Check that your Spotify credentials are correct in the env files

### Environment Files:

- **Backend**: `spotify-recommender/backend/env.local` → rename to `.env`
- **Frontend**: `spotify-recommender/frontend/env.local` → rename to `.env`

## Current Configuration:

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Spotify Redirect**: http://127.0.0.1:3000/auth/callback
- **Client ID**: f1319edcc9204b05aaf7465c1884aad7

## Next Steps:

1. Update Spotify app redirect URIs
2. Test the full authentication flow
3. Generate your first playlist!
4. Debug any issues that arise
