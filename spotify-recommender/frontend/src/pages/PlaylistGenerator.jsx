import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { playlistAPI, userAPI } from '../services/api'
import { SUPPORTED_MOODS, SUPPORTED_GENRES, PLAYLIST_LENGTH } from '../utils/constants'
import { Music, Heart, Play, Save, RefreshCw, Loader } from 'lucide-react'

const PlaylistGenerator = () => {
  const { isAuthenticated } = useAuth()
  const [formData, setFormData] = useState({
    mood: 'Energetic',
    genre: 'All Genres',
    playlist_length: PLAYLIST_LENGTH.DEFAULT,
    seed_track: '',
    playlist_name: ''
  })
  const [userTracks, setUserTracks] = useState([])
  const [generatedPlaylist, setGeneratedPlaylist] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingTracks, setLoadingTracks] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (isAuthenticated) {
      fetchUserTracks()
    }
  }, [isAuthenticated])

  const fetchUserTracks = async () => {
    setLoadingTracks(true)
    setError('')
    try {
      const response = await userAPI.getTracks()
      if (response.status === 200) {
        const tracks = [
          ...(response.data.top_tracks || []),
          ...(response.data.saved_tracks || [])
        ]
        setUserTracks(tracks)
      }
    } catch (err) {
      console.error('Failed to fetch user tracks:', err)
      setError('Failed to load your music library. Please try refreshing the page.')
    } finally {
      setLoadingTracks(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleGeneratePlaylist = async () => {
    setLoading(true)
    setError('')
    setSuccess('')
    setGeneratedPlaylist(null)

    try {
      const response = await playlistAPI.generate({
        mood: formData.mood,
        genre: formData.genre === 'All Genres' ? null : formData.genre,
        playlist_length: formData.playlist_length,
        seed_track_id: formData.seed_track || null,
        playlist_name: formData.playlist_name || null
      })

      if (response.status === 200) {
        setGeneratedPlaylist(response.data)
        setSuccess('Playlist generated successfully!')
      } else {
        setError('Failed to generate playlist. Please try again.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while generating the playlist.')
      console.error('Playlist generation error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRegenerate = async () => {
    if (!generatedPlaylist?.id) return

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await playlistAPI.regenerate(generatedPlaylist.id)
      if (response.status === 200) {
        setGeneratedPlaylist(response.data)
        setSuccess('Playlist regenerated successfully!')
      } else {
        setError('Failed to regenerate playlist. Please try again.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while regenerating the playlist.')
      console.error('Playlist regeneration error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveToSpotify = async () => {
    if (!generatedPlaylist?.id) return

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await playlistAPI.saveToSpotify(generatedPlaylist.id)
      if (response.status === 200) {
        setSuccess('Playlist saved to Spotify successfully!')
        // Optionally open the Spotify playlist URL
        if (response.data?.spotify_playlist_url) {
          window.open(response.data.spotify_playlist_url, '_blank')
        }
      } else {
        setError('Failed to save playlist to Spotify.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save playlist to Spotify.')
      console.error('Save to Spotify error:', err)
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-semibold mb-4">Please log in to generate playlists</h2>
        <p className="text-gray-400 mb-6">Connect your Spotify account to get started</p>
        <a href="/login" className="btn-primary">
          Connect Spotify
        </a>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-4">Generate Your Playlist</h1>
        <p className="text-gray-400 text-lg">
          Choose your mood and preferences to create a personalized playlist
        </p>
      </div>

      {/* Configuration Form */}
      <div className="card mb-8">
        <h2 className="text-2xl font-semibold mb-6">Playlist Settings</h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          {/* Playlist Name */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-3">Playlist Name (Optional)</label>
            <input
              type="text"
              name="playlist_name"
              value={formData.playlist_name}
              onChange={handleInputChange}
              placeholder="Enter a custom name for your playlist"
              className="input-field w-full"
            />
          </div>

          {/* Mood Selection */}
          <div>
            <label className="block text-sm font-medium mb-3">Mood</label>
            <div className="grid grid-cols-2 gap-3">
              {SUPPORTED_MOODS.map((mood) => (
                <button
                  key={mood}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, mood }))}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    formData.mood === mood
                      ? 'border-spotify-green bg-spotify-green bg-opacity-20'
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  {mood}
                </button>
              ))}
            </div>
          </div>

          {/* Genre Selection */}
          <div>
            <label className="block text-sm font-medium mb-3">Genre (Optional)</label>
            <select
              name="genre"
              value={formData.genre}
              onChange={handleInputChange}
              className="input-field w-full"
            >
              <option value="All Genres">All Genres</option>
              {SUPPORTED_GENRES.map((genre) => (
                <option key={genre} value={genre}>{genre}</option>
              ))}
            </select>
          </div>

          {/* Playlist Length */}
          <div>
            <label className="block text-sm font-medium mb-3">
              Playlist Length: {formData.playlist_length} songs
            </label>
            <input
              type="range"
              name="playlist_length"
              min={PLAYLIST_LENGTH.MIN}
              max={PLAYLIST_LENGTH.MAX}
              value={formData.playlist_length}
              onChange={handleInputChange}
              className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-sm text-gray-400 mt-1">
              <span>{PLAYLIST_LENGTH.MIN}</span>
              <span>{PLAYLIST_LENGTH.MAX}</span>
            </div>
          </div>

          {/* Seed Track */}
          <div>
            <label className="block text-sm font-medium mb-3">Seed Track (Optional)</label>
            {loadingTracks ? (
              <div className="flex items-center space-x-2 text-gray-400">
                <Loader className="w-4 h-4 animate-spin" />
                <span>Loading your tracks...</span>
              </div>
            ) : (
              <select
                name="seed_track"
                value={formData.seed_track}
                onChange={handleInputChange}
                className="input-field w-full"
              >
                <option value="">No seed track</option>
                {userTracks.slice(0, 20).map((track) => (
                  <option key={track.id} value={track.id}>
                    {track.name} - {track.artists?.join(', ')}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Generate Button */}
        <div className="mt-8 text-center">
          <button
            onClick={handleGeneratePlaylist}
            disabled={loading || loadingTracks || userTracks.length < 20}
            className="btn-primary text-lg px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Music className="w-5 h-5 mr-2" />
                Generate Playlist
              </>
            )}
          </button>
          
          {/* Validation Message */}
          {!loadingTracks && userTracks.length < 20 && (
            <p className="text-sm text-yellow-400 mt-2">
              You need at least 20 tracks in your library to generate playlists. 
              You currently have {userTracks.length} tracks.
            </p>
          )}
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded-md mb-6">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-900 border border-green-700 text-green-200 px-4 py-3 rounded-md mb-6">
          {success}
        </div>
      )}

      {/* Generated Playlist */}
      {generatedPlaylist && (
        <div className="card">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Your Generated Playlist</h2>
            <div className="space-x-3">
              <button
                onClick={handleRegenerate}
                disabled={loading}
                className="btn-secondary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>{loading ? 'Processing...' : 'Regenerate'}</span>
              </button>
              <button
                onClick={handleSaveToSpotify}
                disabled={loading}
                className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4" />
                <span>{loading ? 'Saving...' : 'Save to Spotify'}</span>
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {generatedPlaylist.tracks?.map((track, index) => (
              <div key={track.id} className="flex items-center space-x-4 p-3 bg-gray-700 rounded-lg">
                <span className="text-lg font-bold text-spotify-green w-8">{index + 1}</span>
                <div className="w-12 h-12 rounded bg-gray-600 flex items-center justify-center">
                  {track.album_art ? (
                    <img 
                      src={track.album_art} 
                      alt={track.album} 
                      className="w-12 h-12 rounded object-cover"
                    />
                  ) : (
                    <Music className="w-6 h-6 text-gray-400" />
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="font-medium">{track.name}</h3>
                  <p className="text-gray-400">{track.artists?.join(', ')}</p>
                  <p className="text-sm text-gray-500">{track.album}</p>
                </div>
                <a
                  href={`https://open.spotify.com/track/${track.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-spotify-green hover:text-green-400 transition-colors"
                >
                  <Play className="w-5 h-5" />
                </a>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-gray-600">
            <div className="grid md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-sm text-gray-400">Mood</p>
                <p className="font-semibold">{generatedPlaylist.mood}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Genre</p>
                <p className="font-semibold">{generatedPlaylist.genre || 'All Genres'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Length</p>
                <p className="font-semibold">{generatedPlaylist.tracks?.length || 0} songs</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Generated</p>
                <p className="font-semibold">{new Date(generatedPlaylist.generated_at).toLocaleDateString()}</p>
              </div>
            </div>
            
            {/* Playlist Metrics */}
            {generatedPlaylist.metrics && (
              <div className="mt-4 pt-4 border-t border-gray-600">
                <h4 className="text-sm font-medium text-gray-400 mb-2">Recommendation Quality</h4>
                <div className="grid grid-cols-2 gap-4 text-center">
                  {generatedPlaylist.metrics.average_similarity && (
                    <div>
                      <p className="text-xs text-gray-500">Avg Similarity</p>
                      <p className="text-sm font-semibold">
                        {(generatedPlaylist.metrics.average_similarity * 100).toFixed(1)}%
                      </p>
                    </div>
                  )}
                  {generatedPlaylist.metrics.tracks_found && (
                    <div>
                      <p className="text-xs text-gray-500">Tracks Found</p>
                      <p className="text-sm font-semibold">{generatedPlaylist.metrics.tracks_found}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default PlaylistGenerator
