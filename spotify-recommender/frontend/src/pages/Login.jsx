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
    const success = searchParams.get('success')
    const userId = searchParams.get('user_id')
    const accessToken = searchParams.get('access_token')
    const error = searchParams.get('error')
    
    if (success === 'true' && userId && accessToken) {
      handleSpotifyCallbackSuccess(userId, accessToken)
    } else if (success === 'false' || error) {
      handleSpotifyCallbackError(error || 'Authentication failed')
    }
  }, [searchParams])

  const handleSpotifyCallbackSuccess = (userId, accessToken) => {
    setIsLoading(true)
    setError('')
    
    try {
      // Create a mock user object for the auth context
      const user = {
        id: userId,
        display_name: 'Spotify User', // We'll get this from the backend later
        access_token: accessToken
      }
      
      login(user, {
        access_token: accessToken
      })
      navigate('/dashboard')
    } catch (err) {
      setError('Failed to complete authentication')
      console.error('Auth callback error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSpotifyCallbackError = (errorMessage) => {
    setError(errorMessage)
    setIsLoading(false)
  }

  const handleSpotifyLogin = () => {
    setIsLoading(true)
    setError('')
    
    // Redirect to Spotify OAuth
    const loginUrl = authAPI.spotifyLogin()
    console.log('Redirecting to:', loginUrl)
    window.location.href = loginUrl
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
            <a
              href={authAPI.spotifyLogin()}
              className="w-full btn-primary text-lg py-3 flex items-center justify-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Music className="w-5 h-5" />
              <span>Continue with Spotify</span>
            </a>
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
