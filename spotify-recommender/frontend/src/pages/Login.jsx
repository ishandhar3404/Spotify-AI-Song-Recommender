import React, { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { authAPI } from '../services/api'
import { Music, Loader } from 'lucide-react'

const Login = () => {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [isLoading, setIsLoading] = React.useState(false)
  const [error, setError] = React.useState('')

  // Check if user is already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard')
    }
  }, [isAuthenticated, navigate])

  // Handle OAuth callback
  useEffect(() => {
    const code = searchParams.get('code')
    if (code) {
      handleSpotifyCallback(code)
    }
  }, [searchParams])

  const handleSpotifyCallback = async (code) => {
    setIsLoading(true)
    setError('')
    
    try {
      const response = await fetch(authAPI.spotifyCallback(code))
      if (response.ok) {
        const data = await response.json()
        login(data.user, {
          access_token: data.access_token,
          refresh_token: data.refresh_token
        })
        navigate('/dashboard')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Authentication failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
      console.error('Auth callback error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSpotifyLogin = () => {
    setIsLoading(true)
    setError('')
    
    // Redirect to Spotify OAuth
    window.location.href = authAPI.spotifyLogin()
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 text-spotify-green animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-2">Connecting to Spotify...</h2>
          <p className="text-gray-400">Please wait while we authenticate your account</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-20 w-20 bg-spotify-green rounded-full flex items-center justify-center mb-6">
            <Music className="h-10 w-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">
            Connect Your Spotify
          </h2>
          <p className="text-gray-400">
            Generate personalized playlists based on your listening history
          </p>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        <div className="space-y-6">
          <div className="text-center">
            <button
              onClick={handleSpotifyLogin}
              disabled={isLoading}
              className="w-full btn-primary text-lg py-3 flex items-center justify-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Music className="w-5 h-5" />
              <span>Continue with Spotify</span>
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-400">
              By connecting, you agree to our{' '}
              <a href="#" className="text-spotify-green hover:underline">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#" className="text-spotify-green hover:underline">
                Privacy Policy
              </a>
            </p>
          </div>
        </div>

        <div className="mt-8 text-center">
          <h3 className="text-lg font-semibold text-white mb-4">What you'll get:</h3>
          <div className="space-y-3 text-sm text-gray-400">
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-spotify-green rounded-full"></div>
              <span>AI-powered playlist recommendations</span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-spotify-green rounded-full"></div>
              <span>Mood and genre-based filtering</span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-spotify-green rounded-full"></div>
              <span>Personalized music discovery</span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-spotify-green rounded-full"></div>
              <span>Save playlists directly to Spotify</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
