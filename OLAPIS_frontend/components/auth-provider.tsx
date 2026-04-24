"use client"

import { useEffect } from "react"
import { useAuthStore } from "@/lib/store"
import { getCurrentUser } from "@/lib/api"

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading, setNeedsOnboarding } = useAuthStore()

  useEffect(() => {
    const initAuth = async () => {
      try {
        const user = await getCurrentUser()
        if (user) {
          setUser(user)
          // Check if user needs onboarding
          if (!user.interests || user.interests.length === 0) {
            setNeedsOnboarding(true)
          }
        }
      } catch {
        // User not authenticated, that's fine
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [setUser, setLoading, setNeedsOnboarding])

  return <>{children}</>
}
