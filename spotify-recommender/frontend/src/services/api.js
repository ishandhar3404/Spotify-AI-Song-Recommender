import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token and user ID
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('spotify_access_token')
    const userId = localStorage.getItem('user_id')
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    if (userId) {
      config.headers['X-User-ID'] = userId
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('spotify_refresh_token')
      const userId = localStorage.getItem('user_id')
      
      if (refreshToken && userId) {
        try {
          const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, {
            headers: {
              'X-User-ID': userId,
              'Authorization': `Bearer ${localStorage.getItem('spotify_access_token')}`
            }
          })
          
          const { access_token } = refreshResponse.data
          localStorage.setItem('spotify_access_token', access_token)
          
          // Retry original request
          error.config.headers.Authorization = `Bearer ${access_token}`
          return api.request(error.config)
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError)
          // Refresh failed, redirect to login
          localStorage.removeItem('spotify_access_token')
          localStorage.removeItem('spotify_refresh_token')
          localStorage.removeItem('user_id')
          window.location.href = '/login'
        }
      } else {
        // No refresh token, redirect to login
        localStorage.removeItem('spotify_access_token')
        localStorage.removeItem('spotify_refresh_token')
        localStorage.removeItem('user_id')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// API endpoints
export const authAPI = {
  spotifyLogin: () => `${API_BASE_URL}/auth/spotify/login`,
  spotifyCallback: (code) => `${API_BASE_URL}/auth/callback?code=${code}`,
  refreshToken: () => `${API_BASE_URL}/auth/refresh`,
}

export const userAPI = {
  getProfile: () => api.get('/api/user/profile'),
  getTracks: () => api.get('/api/user/tracks'),
  refreshData: () => api.post('/api/user/refresh-data'),
}

export const playlistAPI = {
  generate: (data) => api.post('/api/playlists/generate', data),
  getPlaylist: (id) => api.get(`/api/playlists/${id}`),
  regenerate: (id) => api.post(`/api/playlists/${id}/regenerate`),
  saveToSpotify: (id) => api.post(`/api/playlists/${id}/save-to-spotify`),
}

export const analyticsAPI = {
  getPerformance: () => api.get('/api/analytics/performance'),
  getSystemMetrics: () => api.get('/api/analytics/system'),
}

export default api
