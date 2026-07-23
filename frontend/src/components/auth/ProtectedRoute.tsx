'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
  requireSuperAdmin?: boolean
  requireEmailVerified?: boolean
  redirectTo?: string
}

export default function ProtectedRoute({
  children,
  requireAdmin = false,
  requireSuperAdmin = false,
  requireEmailVerified = false,
  redirectTo = '/login',
}: ProtectedRouteProps) {
  const router = useRouter()
  const { isAuthenticated, isAdmin, isSuperAdmin, isEmailVerified, isLoading } =
    useAuth()

  useEffect(() => {
    if (!isLoading) {
      // Check if user is authenticated
      if (!isAuthenticated) {
        router.push(redirectTo)
        return
      }

      // Check if super admin is required
      if (requireSuperAdmin && !isSuperAdmin) {
        router.push('/unauthorized')
        return
      }

      // Check if admin is required
      if (requireAdmin && !isAdmin) {
        router.push('/unauthorized')
        return
      }

      // Check if email verification is required
      if (requireEmailVerified && !isEmailVerified) {
        router.push('/verify-email-required')
        return
      }
    }
  }, [
    isAuthenticated,
    isAdmin,
    isSuperAdmin,
    isEmailVerified,
    isLoading,
    requireAdmin,
    requireSuperAdmin,
    requireEmailVerified,
    redirectTo,
    router,
  ])

  // Show loading state while checking auth
  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Check permissions after loading
  if (requireSuperAdmin && !isSuperAdmin) {
    return null
  }

  if (requireAdmin && !isAdmin) {
    return null
  }

  if (requireEmailVerified && !isEmailVerified) {
    return null
  }

  return <>{children}</>
}
