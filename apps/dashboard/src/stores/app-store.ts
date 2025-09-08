import { create } from 'zustand'

interface AppState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  language: 'en' | 'ar'
  user: {
    id?: string
    email?: string
    role?: 'admin' | 'manager' | 'staff'
  } | null
}

interface AppActions {
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark') => void
  setLanguage: (language: 'en' | 'ar') => void
  setUser: (user: AppState['user']) => void
  logout: () => void
}

export const useAppStore = create<AppState & AppActions>((set) => ({
  sidebarOpen: false,
  theme: 'light',
  language: 'en',
  user: null,
  
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme }),
  setLanguage: (language) => set({ language }),
  setUser: (user) => set({ user }),
  logout: () => set({ user: null }),
}))