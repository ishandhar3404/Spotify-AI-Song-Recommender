import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Check if user is already authenticated
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('spotify_access_token')
        const userId = localStorage.getItem('user_id')
        if (token && userId) {
          // Verify token with backend
          const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/status`, {
            headers: {
              'X-User-ID': userId,
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            const authData = await response.json()
            if (authData.authenticated) {
              setUser(authData.user)
              setIsAuthenticated(true)
            } else {
              // Token invalid, clear storage
              localStorage.removeItem('spotify_access_token')
              localStorage.removeItem('spotify_refresh_token')
              localStorage.removeItem('user_id')
            }
          } else {
            // Token invalid, clear storage
            localStorage.removeItem('spotify_access_token')
            localStorage.removeItem('spotify_refresh_token')
            localStorage.removeItem('user_id')
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = (userData, tokens) => {
    setUser(userData)
    setIsAuthenticated(true)
    localStorage.setItem('spotify_access_token', tokens.access_token)
    localStorage.setItem('user_id', userData.id)
    if (tokens.refresh_token) {
      localStorage.setItem('spotify_refresh_token', tokens.refresh_token)
    }
  }

  const logout = () => {
    setUser(null)
    setIsAuthenticated(false)
    localStorage.removeItem('spotify_access_token')
    localStorage.removeItem('spotify_refresh_token')
    localStorage.removeItem('user_id')
  }

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
