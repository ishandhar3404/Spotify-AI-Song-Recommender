import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Home from './pages/Home'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import SongMix from './pages/SongMix'
import PlaylistGenerator from './pages/PlaylistGenerator'
import { AuthProvider } from './contexts/AuthContext'
import './App.css'

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-spotify-black">
          <Header />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/auth/callback" element={<Login />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/generate" element={<SongMix />} /><Route path="/generate/mood" element={<PlaylistGenerator />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App
