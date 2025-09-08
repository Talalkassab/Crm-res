# Frontend Architecture

## Component Architecture

### Component Organization
```text
apps/dashboard/
├── src/
│   ├── app/                    # Next.js 14 App Router
│   │   ├── (auth)/             # Auth-required pages
│   │   │   ├── dashboard/
│   │   │   ├── conversations/
│   │   │   ├── analytics/
│   │   │   ├── settings/
│   │   │   └── orders/
│   │   ├── (public)/           # Public pages
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── api/                # API routes (BFF pattern)
│   │   ├── layout.tsx          # Root layout with providers
│   │   └── globals.css         # Global styles with Tailwind
│   ├── components/
│   │   ├── ui/                 # Shadcn/ui components
│   │   ├── dashboard/          # Dashboard-specific components
│   │   ├── conversations/      # Conversation components
│   │   ├── analytics/          # Chart components
│   │   └── shared/             # Shared components
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utilities and configs
│   ├── stores/                 # Zustand stores
│   └── types/                  # TypeScript types
```

## State Management Architecture

### State Structure
```typescript
// Zustand store structure for global state
interface AppState {
  // Restaurant context
  restaurant: Restaurant | null;
  selectedBranch: Branch | null;
  branches: Branch[];
  
  // Conversations state
  conversations: {
    items: Conversation[];
    activeId: string | null;
    filters: ConversationFilters;
    isLoading: boolean;
  };
  
  // Real-time metrics
  metrics: {
    dashboard: DashboardMetrics;
    lastUpdated: string;
  };
  
  // UI state
  ui: {
    sidebarOpen: boolean;
    theme: 'light' | 'dark' | 'system';
    language: 'ar' | 'en';
  };
  
  // Actions
  actions: {
    setRestaurant: (restaurant: Restaurant) => void;
    selectBranch: (branchId: string) => void;
    updateConversation: (id: string, updates: Partial<Conversation>) => void;
    addMessage: (conversationId: string, message: Message) => void;
    updateMetrics: (metrics: DashboardMetrics) => void;
  };
}
```

## Routing Architecture

### Route Organization
```text
/                           # Redirect to dashboard
/login                      # Public login page
/register                   # Public registration
/dashboard                  # Main dashboard (metrics overview)
/conversations              # Conversation list and chat view
  /[id]                    # Specific conversation
/analytics                  # Detailed analytics
  /feedback                # Feedback analytics
  /revenue                 # Revenue analytics
/orders                     # Order management
  /[id]                    # Order details
/settings                   # Settings pages
  /restaurant              # Restaurant settings
  /branches                # Branch management
  /team                    # Team management
  /personality             # AI personality config
  /integrations           # Third-party integrations
```

## Frontend Services Layer

### API Client Setup
```typescript
// Centralized API client with interceptors
import axios from 'axios';
import { createClient } from '@supabase/supabase-js';

// Supabase client for auth and realtime
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// API client for backend services
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor for auth
apiClient.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  
  return config;
});
```
