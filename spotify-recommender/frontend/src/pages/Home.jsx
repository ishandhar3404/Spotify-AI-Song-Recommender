import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Music, Heart, Zap, Users } from 'lucide-react'

const Home = () => {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="text-center py-20">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-spotify-green to-green-400 bg-clip-text text-transparent">
            Discover Your Perfect Playlist
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-2xl mx-auto">
            AI-powered playlist generation using your Spotify listening history. 
            Discover tracks from the songs you choose.
          </p>
          
          {isAuthenticated ? (
            <div className="space-x-4">
              <Link 
                to="/generate" 
                className="btn-primary text-lg px-8 py-3 inline-block"
              >
                Generate Playlist
              </Link>
              <Link 
                to="/dashboard" 
                className="btn-secondary text-lg px-8 py-3 inline-block"
              >
                View Dashboard
              </Link>
            </div>
          ) : (
            <div className="space-x-4">
              <Link 
                to="/login" 
                className="btn-primary text-lg px-8 py-3 inline-block"
              >
                Connect with Spotify
              </Link>
              <a 
                href="#features" 
                className="btn-secondary text-lg px-8 py-3 inline-block"
              >
                Learn More
              </a>
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-spotify-gray">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16">
            How It Works
          </h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="bg-spotify-green rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Music className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Connect Spotify</h3>
              <p className="text-gray-300">
                Securely connect your Spotify account to analyze your listening history
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-spotify-green rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Heart className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Pick Your Starting Songs</h3>
              <p className="text-gray-300">
                Choose up to five tracks to shape your mix
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-spotify-green rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">AI Analysis</h3>
              <p className="text-gray-300">
                Our KNN algorithm analyzes audio features to find perfect matches
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-spotify-green rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Enjoy & Share</h3>
              <p className="text-gray-300">
                Save playlists to Spotify or export them to share with friends
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-4xl font-bold mb-6">
            Ready to Discover New Music?
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Join thousands of users who are already creating amazing playlists with AI
          </p>
          <Link 
            to={isAuthenticated ? "/generate" : "/login"} 
            className="btn-primary text-lg px-8 py-3 inline-block"
          >
            {isAuthenticated ? 'Start Creating' : 'Get Started Now'}
          </Link>
        </div>
      </section>
    </div>
  )
}

export default Home
