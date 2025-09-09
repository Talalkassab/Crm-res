import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Restaurant, Branch, Conversation, ConversationFilters, DashboardMetrics } from '@/types'

interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  language: 'ar' | 'en'
}

interface ConversationsState {
  items: Conversation[]
  activeId: string | null
  filters: ConversationFilters
  isLoading: boolean
}

interface MetricsState {
  dashboard: DashboardMetrics | null
  lastUpdated: string | null
}

interface AppState {
  // Restaurant context
  restaurant: Restaurant | null
  selectedBranch: Branch | null
  branches: Branch[]
  setRestaurant: (restaurant: Restaurant | null) => void
  setSelectedBranch: (branch: Branch | null) => void
  setBranches: (branches: Branch[]) => void
  
  // Conversations state
  conversations: ConversationsState
  setConversations: (conversations: Conversation[]) => void
  setActiveConversation: (id: string | null) => void
  setConversationFilters: (filters: ConversationFilters) => void
  setConversationsLoading: (loading: boolean) => void
  addConversation: (conversation: Conversation) => void
  updateConversation: (id: string, updates: Partial<Conversation>) => void
  
  // Real-time metrics
  metrics: MetricsState
  setDashboardMetrics: (metrics: DashboardMetrics) => void
  
  // UI state
  ui: UIState
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  setLanguage: (language: 'ar' | 'en') => void
  toggleLanguage: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Restaurant context
      restaurant: null,
      selectedBranch: null,
      branches: [],
      setRestaurant: (restaurant) => set({ restaurant }),
      setSelectedBranch: (selectedBranch) => set({ selectedBranch }),
      setBranches: (branches) => set({ branches }),
      
      // Conversations state
      conversations: {
        items: [],
        activeId: null,
        filters: {},
        isLoading: false,
      },
      setConversations: (items) => set((state) => ({
        conversations: {
          ...state.conversations,
          items,
        },
      })),
      setActiveConversation: (activeId) => set((state) => ({
        conversations: {
          ...state.conversations,
          activeId,
        },
      })),
      setConversationFilters: (filters) => set((state) => ({
        conversations: {
          ...state.conversations,
          filters,
        },
      })),
      setConversationsLoading: (isLoading) => set((state) => ({
        conversations: {
          ...state.conversations,
          isLoading,
        },
      })),
      addConversation: (conversation) => set((state) => ({
        conversations: {
          ...state.conversations,
          items: [conversation, ...state.conversations.items],
        },
      })),
      updateConversation: (id, updates) => set((state) => ({
        conversations: {
          ...state.conversations,
          items: state.conversations.items.map(c => 
            c.id === id ? { ...c, ...updates } : c
          ),
        },
      })),
      
      // Real-time metrics
      metrics: {
        dashboard: null,
        lastUpdated: null,
      },
      setDashboardMetrics: (dashboard) => set({
        metrics: {
          dashboard,
          lastUpdated: new Date().toISOString(),
        },
      }),
      
      // UI state
      ui: {
        sidebarOpen: true,
        theme: 'system',
        language: 'ar',
      },
      setSidebarOpen: (sidebarOpen) => set((state) => ({
        ui: { ...state.ui, sidebarOpen },
      })),
      setTheme: (theme) => set((state) => ({
        ui: { ...state.ui, theme },
      })),
      setLanguage: (language) => set((state) => ({
        ui: { ...state.ui, language },
      })),
      toggleLanguage: () => set((state) => ({
        ui: { ...state.ui, language: state.ui.language === 'ar' ? 'en' : 'ar' },
      })),
    }),
    {
      name: 'crm-res-dashboard',
      partialize: (state) => ({
        ui: state.ui,
        selectedBranch: state.selectedBranch,
      }),
    }
  )
)