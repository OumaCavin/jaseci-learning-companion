'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, AuthContextType } from '@/types/auth'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (token) {
          // Validate token with backend
          const response = await fetch('/api/v1/auth/me', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          })
          
          if (response.ok) {
            const userData = await response.json()
            setUser(userData)
            setIsAuthenticated(true)
          } else {
            localStorage.removeItem('auth_token')
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        localStorage.removeItem('auth_token')
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        throw new Error('Login failed')
      }

      const { access_token, user: userData } = await response.json()
      
      localStorage.setItem('auth_token', access_token)
      setUser(userData)
      setIsAuthenticated(true)
      
      return { success: true, user: userData }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, error: 'Invalid credentials' }
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setUser(null)
    setIsAuthenticated(false)
  }

  const register = async (userData: {
    email: string
    password: string
    username: string
    first_name?: string
    last_name?: string
  }) => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Registration failed')
      }

      const { access_token, user: newUser } = await response.json()
      
      localStorage.setItem('auth_token', access_token)
      setUser(newUser)
      setIsAuthenticated(true)
      
      return { success: true, user: newUser }
    } catch (error) {
      console.error('Registration error:', error)
      return { success: false, error: error instanceof Error ? error.message : 'Registration failed' }
    } finally {
      setIsLoading(false)
    }
  }

  const updateProfile = async (profileData: Partial<User>) => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) throw new Error('No authentication token')

      const response = await fetch('/api/v1/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(profileData),
      })

      if (!response.ok) {
        throw new Error('Profile update failed')
      }

      const updatedUser = await response.json()
      setUser(updatedUser)
      
      return { success: true, user: updatedUser }
    } catch (error) {
      console.error('Profile update error:', error)
      return { success: false, error: 'Profile update failed' }
    }
  }

  const refreshToken = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) throw new Error('No refresh token available')

      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const { access_token } = await response.json()
      localStorage.setItem('auth_token', access_token)
      
      return { success: true, token: access_token }
    } catch (error) {
      console.error('Token refresh error:', error)
      // If refresh fails, log out the user
      logout()
      return { success: false, error: 'Token refresh failed' }
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    register,
    updateProfile,
    refreshToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}