export interface Restaurant {
  id: string
  name: string
  nameAr: string
  logoUrl?: string
  createdAt: string
  updatedAt: string
}

export interface Branch {
  id: string
  restaurantId: string
  name: string
  nameAr: string
  city: string
  cityAr: string
  phoneNumber: string
  operatingHours: {
    [key: string]: {
      open: string
      close: string
    }
  }
  prayerTimeClosures: boolean
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface Customer {
  id: string
  phoneNumber: string
  name?: string
  preferredLanguage: 'ar' | 'en'
  totalOrders: number
  totalFeedback: number
  lastContactDate: string
  tags: string[]
  createdAt: string
  updatedAt: string
}

export interface Message {
  id: string
  conversationId: string
  sender: 'customer' | 'ai' | 'agent'
  content: string
  contentAr?: string
  timestamp: string
  metadata?: {
    confidence?: number
    intent?: string
    sentiment?: 'positive' | 'neutral' | 'negative'
  }
}

export interface Conversation {
  id: string
  customerId: string
  restaurantId: string
  branchId?: string
  status: 'active' | 'escalated' | 'resolved' | 'abandoned'
  type: 'feedback' | 'order' | 'support' | 'general'
  aiConfidence: number
  messages: Message[]
  startedAt: string
  escalatedAt?: string
  resolvedAt?: string
  customer?: Customer
  branch?: Branch
}

export interface Feedback {
  id: string
  conversationId: string
  customerId: string
  restaurantId: string
  branchId: string
  rating: 1 | 2 | 3 | 4 | 5
  comment?: string
  sentiment: 'positive' | 'neutral' | 'negative'
  categories: string[]
  requiresFollowup: boolean
  createdAt: string
}

export interface DashboardMetrics {
  conversationsToday: number
  conversationsTrend: number
  averageRating: number
  ratingTrend: number
  responseRate: number
  responseTrend: number
  automationRate: number
  automationTrend: number
  activeConversations: number
  escalatedConversations: number
  negativeFeedbackCount: number
  lastUpdated: string
}

export interface ConversationFilters {
  status?: 'active' | 'escalated' | 'resolved' | 'abandoned'
  type?: 'feedback' | 'order' | 'support' | 'general'
  branchId?: string
  dateRange?: {
    from: string
    to: string
  }
  searchQuery?: string
}