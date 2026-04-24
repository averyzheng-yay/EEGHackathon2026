// Global state store using Zustand
import { create } from "zustand"
import type { User } from "./types"

interface AuthState {
  user: User | null
  isLoading: boolean
  needsOnboarding: boolean
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  setNeedsOnboarding: (needs: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  needsOnboarding: false,
  setUser: (user) => set({ user }),
  setLoading: (isLoading) => set({ isLoading }),
  setNeedsOnboarding: (needsOnboarding) => set({ needsOnboarding }),
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
    }
    set({ user: null, needsOnboarding: false })
  },
}))
