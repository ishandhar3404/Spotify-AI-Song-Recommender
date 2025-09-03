import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { userAPI } from '../services/api'
import { Music, Heart, Play, Users, TrendingUp, Clock } from 'lucide-react'

const Dashboard = () => {
  const { user, isAuthenticated } = useAuth()
  const [userData, setUserData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthenticated) {
      return
    }

    const fetchUserData = async () => {
      try {
        const [profileResponse, tracksResponse] = await Promise.all([
          userAPI.getProfile(),
          userAPI.getTracks()
        ])

        if (profileResponse.status === 200 && tracksResponse.status === 200) {
          setUserData({
            profile: profileResponse.data,
            tracks: tracksResponse.data
          })
        } else {
          setError('Failed to fetch user data')
        }
      } catch (err) {
        setError('Error loading dashboard data')
        console.error('Dashboard error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [isAuthenticated])

  if (!isAuthenticated) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-semibold mb-4">Please log in to view your dashboard</h2>
        <Link to="/login" className="btn-primary">
          Connect Spotify
        </Link>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-spotify-green mx-auto mb-4"></div>
        <p>Loading your dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded-md max-w-md mx-auto mb-4">
          {error}
        </div>
        <button 
          onClick={() => window.location.reload()} 
          className="btn-secondary"
        >
          Try Again
        </button>
      </div>
    )
  }

  const { profile, tracks } = userData || {}
  const totalTracks = (tracks?.top_tracks?.length || 0) + (tracks?.saved_tracks?.length || 0)

  return (
    <div className="max-w-6xl mx-auto">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">
          Welcome back, {profile?.display_name || user?.display_name}!
        </h1>
        <p className="text-gray-400 text-lg">
          Ready to discover your next favorite playlist?
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Link 
          to="/generate" 
          className="card hover:bg-gray-700 transition-colors cursor-pointer group"
        >
          <div className="flex items-center space-x-4">
            <div className="bg-spotify-green rounded-full p-3 group-hover:scale-110 transition-transform">
              <Music className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-1">Generate Playlist</h3>
              <p className="text-gray-400">Create a new personalized playlist</p>
            </div>
          </div>
        </Link>

        <button 
          onClick={() => userAPI.refreshData()}
          className="card hover:bg-gray-700 transition-colors cursor-pointer group text-left"
        >
          <div className="flex items-center space-x-4">
            <div className="bg-blue-600 rounded-full p-3 group-hover:scale-110 transition-transform">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-1">Refresh Data</h3>
              <p className="text-gray-400">Update your listening history</p>
            </div>
          </div>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <div className="card text-center">
          <div className="bg-spotify-green rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
            <Music className="w-6 h-6 text-white" />
          </div>
          <h3 className="text-2xl font-bold mb-1">{totalTracks}</h3>
          <p className="text-gray-400">Total Tracks</p>
        </div>

        <div className="card text-center">
          <div className="bg-purple-600 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
            <Heart className="w-6 h-6 text-white" />
          </div>
          <h3 className="text-2xl font-bold mb-1">{tracks?.saved_tracks?.length || 0}</h3>
          <p className="text-gray-400">Saved Tracks</p>
        </div>

        <div className="card text-center">
          <div className="bg-blue-600 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
            <Play className="w-6 h-6 text-white" />
          </div>
          <h3 className="text-2xl font-bold mb-1">{tracks?.top_tracks?.length || 0}</h3>
          <p className="text-gray-400">Top Tracks</p>
        </div>

        <div className="card text-center">
          <div className="bg-orange-600 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
            <Users className="w-6 h-6 text-white" />
          </div>
          <h3 className="text-2xl font-bold mb-1">{profile?.followers || 0}</h3>
          <p className="text-gray-400">Followers</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Top Tracks */}
        <div className="card">
          <h3 className="text-xl font-semibold mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-spotify-green" />
            Your Top Tracks
          </h3>
          <div className="space-y-3">
            {tracks?.top_tracks?.slice(0, 5).map((track, index) => (
              <div key={track.id} className="flex items-center space-x-3 p-2 rounded hover:bg-gray-700">
                <span className="text-sm text-gray-400 w-6">{index + 1}</span>
                <img 
                  src={track.album_art} 
                  alt={track.album} 
                  className="w-10 h-10 rounded"
                />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{track.name}</p>
                  <p className="text-sm text-gray-400 truncate">{track.artists?.join(', ')}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <h3 className="text-xl font-semibold mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-spotify-green" />
            Recent Activity
          </h3>
          <div className="space-y-3">
            <div className="p-3 bg-gray-700 rounded">
              <p className="text-sm text-gray-300">Connected to Spotify</p>
              <p className="text-xs text-gray-500">Just now</p>
            </div>
            {profile?.last_login && (
              <div className="p-3 bg-gray-700 rounded">
                <p className="text-sm text-gray-300">Last login</p>
                <p className="text-xs text-gray-500">
                  {new Date(profile.last_login).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
