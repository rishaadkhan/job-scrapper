import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import api from '../api/client'
import type { TokenResponse } from '../types'

interface AuthUser {
  email: string
  role: string
}

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function loadUser(): AuthUser | null {
  const token = localStorage.getItem('access_token')
  const email = localStorage.getItem('user_email')
  const role = localStorage.getItem('user_role')
  if (token && email && role) return { email, role }
  return null
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(loadUser)

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post<TokenResponse>('/auth/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_email', data.email)
    localStorage.setItem('user_role', data.role)
    setUser({ email: data.email, role: data.role })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_email')
    localStorage.removeItem('user_role')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
