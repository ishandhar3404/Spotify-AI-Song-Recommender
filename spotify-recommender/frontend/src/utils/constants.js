// Supported moods for playlist generation
export const SUPPORTED_MOODS = [
  'Energetic',
  'Chill',
  'Focused',
  'Party',
  'Relaxed',
  'Workout',
  'Romantic',
  'Nostalgic'
]

// Supported genres for playlist generation
export const SUPPORTED_GENRES = [
  'Pop',
  'Rock',
  'Hip-Hop',
  'Electronic',
  'Jazz',
  'Classical',
  'Country',
  'R&B',
  'Indie',
  'Alternative'
]

// Playlist length constraints
export const PLAYLIST_LENGTH = {
  MIN: 5,
  MAX: 50,
  DEFAULT: 20
}

// Audio feature weights for mood-based recommendations
export const MOOD_WEIGHTS = {
  Energetic: {
    energy: 1.5,
    tempo: 1.3,
    danceability: 1.2,
    valence: 1.1
  },
  Chill: {
    acousticness: 1.4,
    instrumentalness: 1.3,
    energy: 0.7,
    tempo: 0.8
  },
  Focused: {
    instrumentalness: 1.3,
    acousticness: 1.2,
    energy: 0.9,
    speechiness: 0.6
  },
  Party: {
    danceability: 1.5,
    energy: 1.4,
    tempo: 1.3,
    valence: 1.2
  },
  Relaxed: {
    acousticness: 1.4,
    instrumentalness: 1.2,
    energy: 0.6,
    tempo: 0.7
  },
  Workout: {
    energy: 1.5,
    tempo: 1.4,
    danceability: 1.3,
    valence: 1.1
  },
  Romantic: {
    acousticness: 1.3,
    valence: 1.2,
    energy: 0.8,
    tempo: 0.9
  },
  Nostalgic: {
    acousticness: 1.2,
    instrumentalness: 1.1,
    energy: 0.9,
    tempo: 0.9
  }
}

// API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    SPOTIFY_LOGIN: '/auth/spotify/login',
    SPOTIFY_CALLBACK: '/auth/spotify/callback',
    REFRESH: '/auth/refresh'
  },
  USER: {
    PROFILE: '/api/user/profile',
    TRACKS: '/api/user/tracks',
    REFRESH_DATA: '/api/user/refresh-data'
  },
  PLAYLIST: {
    GENERATE: '/api/playlists/generate',
    GET: '/api/playlists',
    REGENERATE: '/api/playlists/regenerate',
    SAVE_TO_SPOTIFY: '/api/playlists/save-to-spotify'
  },
  ANALYTICS: {
    PERFORMANCE: '/api/analytics/performance',
    SYSTEM: '/api/analytics/system'
  }
}

// Local storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'spotify_access_token',
  REFRESH_TOKEN: 'spotify_refresh_token',
  USER_DATA: 'spotify_user_data',
  USER_PREFERENCES: 'user_preferences'
}

// Error messages
export const ERROR_MESSAGES = {
  AUTH_FAILED: 'Authentication failed. Please try logging in again.',
  NETWORK_ERROR: 'Network error. Please check your connection.',
  INSUFFICIENT_TRACKS: 'You need at least 20 tracks in your library to generate playlists.',
  GENERATION_FAILED: 'Failed to generate playlist. Please try again.',
  TOKEN_EXPIRED: 'Your session has expired. Please log in again.'
}
