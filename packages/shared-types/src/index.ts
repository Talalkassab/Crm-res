// Shared TypeScript types for CRM-RES system

export interface Customer {
  id: string;
  phone_number: string;
  name?: string;
  email?: string;
  language_preference: string;
  created_at: string;
  updated_at: string;
  last_contact?: string;
  total_orders: number;
  total_spent: number;
  notes?: string;
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  customer_id: string;
  whatsapp_id: string;
  status: 'active' | 'waiting' | 'resolved' | 'closed';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  assigned_to?: string;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
  resolved_at?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  customer?: Customer;
  message_count?: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  whatsapp_message_id: string;
  direction: 'inbound' | 'outbound';
  message_type: 'text' | 'image' | 'audio' | 'document' | 'video';
  content: string;
  media_url?: string;
  timestamp: string;
  created_at: string;
  is_read: boolean;
  is_ai_generated: boolean;
  sentiment?: 'positive' | 'neutral' | 'negative';
  confidence?: number;
  metadata?: Record<string, any>;
}

export interface PrayerTime {
  id: string;
  city: string;
  date: string;
  fajr: string;
  sunrise: string;
  dhuhr: string;
  asr: string;
  maghrib: string;
  isha: string;
  created_at: string;
}

export interface Order {
  id: string;
  conversation_id: string;
  customer_id: string;
  branch_id?: string;
  order_number: string;
  status: 'pending' | 'confirmed' | 'preparing' | 'ready' | 'delivered' | 'cancelled';
  total_amount: number;
  items: OrderItem[];
  notes?: string;
  created_at: string;
  updated_at: string;
  confirmed_at?: string;
  delivered_at?: string;
  metadata?: Record<string, any>;
}

export interface OrderItem {
  name: string;
  quantity: number;
  price: number;
  notes?: string;
}

export interface Restaurant {
  id: string;
  name: string;
  phone_number: string;
  address?: string;
  city: string;
  timezone: string;
  language: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  settings?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface Branch {
  id: string;
  restaurant_id: string;
  name: string;
  phone_number: string;
  address?: string;
  city: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  settings?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface DashboardAnalytics {
  total_conversations: number;
  active_conversations: number;
  resolved_conversations: number;
  total_customers: number;
  total_orders: number;
  total_revenue: number;
  average_response_time: number;
  satisfaction_score: number;
  prayer_time_active: boolean;
}

export interface ConversationAnalytics {
  period: string;
  total_conversations: number;
  conversations_by_status: Record<string, number>;
  conversations_by_hour: Record<string, number>;
  average_response_time: number;
  satisfaction_trend: Array<{
    date: string;
    score: number;
  }>;
  top_customers: Array<{
    customer_id: string;
    name: string;
    conversation_count: number;
  }>;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// WhatsApp webhook types
export interface WhatsAppWebhookMessage {
  id: string;
  from: string;
  timestamp: string;
  type: string;
  text?: {
    body: string;
  };
  image?: {
    id: string;
    mime_type: string;
    sha256: string;
  };
  audio?: {
    id: string;
    mime_type: string;
    sha256: string;
  };
  document?: {
    id: string;
    mime_type: string;
    sha256: string;
    filename: string;
  };
  video?: {
    id: string;
    mime_type: string;
    sha256: string;
  };
}

export interface WhatsAppWebhookEntry {
  id: string;
  changes: Array<{
    field: string;
    value: {
      messaging_product: string;
      metadata: {
        display_phone_number: string;
        phone_number_id: string;
      };
      messages?: WhatsAppWebhookMessage[];
    };
  }>;
}

export interface WhatsAppWebhook {
  object: string;
  entry: WhatsAppWebhookEntry[];
}

// AI Processing types
export interface AIProcessingRequest {
  message: string;
  conversation_id: string;
  customer_id: string;
  context?: Record<string, any>;
}

export interface AIProcessingResponse {
  response: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  confidence?: number;
  suggested_actions?: string[];
  is_prayer_time: boolean;
  should_escalate: boolean;
}

// Form types
export interface CustomerFormData {
  phone_number: string;
  name?: string;
  email?: string;
  language_preference: string;
  notes?: string;
}

export interface ConversationFormData {
  customer_id: string;
  whatsapp_id: string;
  status: string;
  priority: string;
  assigned_to?: string;
  tags?: string[];
}

export interface MessageFormData {
  conversation_id: string;
  content: string;
  message_type: string;
  direction: 'inbound' | 'outbound';
}

// Filter and search types
export interface ConversationFilters {
  status?: string;
  priority?: string;
  assigned_to?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface CustomerFilters {
  language_preference?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

// Prayer time types
export interface PrayerTimeStatus {
  is_prayer_time: boolean;
  current_prayer?: PrayerTime;
  next_prayer?: PrayerTime;
}

// Error types
export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, any>;
}

// Constants
export const CONVERSATION_STATUS = {
  ACTIVE: 'active',
  WAITING: 'waiting',
  RESOLVED: 'resolved',
  CLOSED: 'closed'
} as const;

export const MESSAGE_DIRECTION = {
  INBOUND: 'inbound',
  OUTBOUND: 'outbound'
} as const;

export const MESSAGE_TYPE = {
  TEXT: 'text',
  IMAGE: 'image',
  AUDIO: 'audio',
  DOCUMENT: 'document',
  VIDEO: 'video'
} as const;

export const SENTIMENT = {
  POSITIVE: 'positive',
  NEUTRAL: 'neutral',
  NEGATIVE: 'negative'
} as const;

export const ORDER_STATUS = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  PREPARING: 'preparing',
  READY: 'ready',
  DELIVERED: 'delivered',
  CANCELLED: 'cancelled'
} as const;