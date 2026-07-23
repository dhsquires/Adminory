import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '@/types'
import { apiClient } from '@/lib/api'
import { toast } from '@/stores/toastStore'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshTokenValue: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  setUser: (user: User | null) => void
  setTokens: (accessToken: string, refreshToken: string) => void
  clearAuth: () => void
  setError: (error: string | null) => void
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshTokenValue: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await apiClient.post<{
            access_token: string
            refresh_token: string
            user: User
          }>('/api/auth/login', { email, password })

          set({
            user: response.user,
            accessToken: response.access_token,
            refreshTokenValue: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })

          // Store tokens in localStorage for API client
          if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', response.access_token)
            localStorage.setItem('refresh_token', response.refresh_token)
          }

          toast.success('Welcome back!', `Logged in as ${response.user.email}`)
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Login failed'
          set({ error: errorMessage, isLoading: false })
          toast.error('Login failed', errorMessage)
          throw new Error(errorMessage)
        }
      },

      register: async (email: string, password: string, name: string) => {
        set({ isLoading: true, error: null })
        try {
          await apiClient.post('/api/auth/register', { email, password, name })
          set({ isLoading: false })
          toast.success('Account created!', 'Please check your email to verify your account')
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Registration failed'
          set({ error: errorMessage, isLoading: false })
          toast.error('Registration failed', errorMessage)
          throw new Error(errorMessage)
        }
      },

      logout: async () => {
        const refreshToken =
          get().refreshTokenValue ||
          (typeof window !== 'undefined'
            ? localStorage.getItem('refresh_token')
            : null)
        try {
          if (refreshToken) {
            await apiClient.post('/api/auth/logout', { refresh_token: refreshToken })
          }
          toast.info('Logged out', 'You have been successfully logged out')
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          get().clearAuth()
        }
      },

      refreshToken: async () => {
        const refreshToken =
          get().refreshTokenValue ||
          (typeof window !== 'undefined'
            ? localStorage.getItem('refresh_token')
            : null)
        if (!refreshToken) {
          get().clearAuth()
          return
        }

        try {
          const response = await apiClient.post<{
            access_token: string
            refresh_token: string
          }>('/api/auth/refresh', { refresh_token: refreshToken })

          set({
            accessToken: response.access_token,
            refreshTokenValue: response.refresh_token,
          })

          // Update tokens in localStorage
          if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', response.access_token)
            localStorage.setItem('refresh_token', response.refresh_token)
          }
        } catch (error) {
          console.error('Token refresh failed:', error)
          get().clearAuth()
        }
      },

      setUser: (user: User | null) => {
        set({ user, isAuthenticated: !!user })
      },

      setTokens: (accessToken: string, refreshToken: string) => {
        set({
          accessToken,
          refreshTokenValue: refreshToken,
          isAuthenticated: true,
        })
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken)
          localStorage.setItem('refresh_token', refreshToken)
        }
      },

      clearAuth: () => {
        set({
          user: null,
          accessToken: null,
          refreshTokenValue: null,
          isAuthenticated: false,
          error: null,
        })
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
      },

      setError: (error: string | null) => {
        set({ error })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshTokenValue: state.refreshTokenValue,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
