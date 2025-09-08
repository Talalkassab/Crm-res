# Data Models

## Core Data Models

### Restaurant
**Purpose:** Represents a restaurant account with configuration and subscription details

**Key Attributes:**
- `id`: UUID - Unique identifier
- `name`: string - Restaurant name in Arabic and English
- `subscription_tier`: enum - Current plan (starter/growth/enterprise)
- `personality_type`: enum - AI personality (formal/casual/traditional/modern)
- `timezone`: string - Restaurant timezone for scheduling
- `prayer_time_enabled`: boolean - Whether to pause during prayer times
- `created_at`: timestamp - Account creation date
- `whatsapp_number`: string - Primary WhatsApp business number
- `settings`: JSONB - Additional configuration

```typescript
interface Restaurant {
  id: string;
  name: { ar: string; en: string };
  subscriptionTier: 'starter' | 'growth' | 'enterprise';
  personalityType: 'formal' | 'casual' | 'traditional' | 'modern';
  timezone: string;
  prayerTimeEnabled: boolean;
  createdAt: string;
  whatsappNumber: string;
  settings: Record<string, any>;
}
```

**Relationships:**
- Has many Branches
- Has many Users (restaurant staff)
- Has many Conversations

### Branch
**Purpose:** Represents individual restaurant locations for multi-branch operations

**Key Attributes:**
- `id`: UUID - Unique identifier
- `restaurant_id`: UUID - Parent restaurant
- `name`: string - Branch name/location
- `address`: JSONB - Structured address with coordinates
- `phone`: string - Branch phone number
- `operating_hours`: JSONB - Schedule by day
- `is_active`: boolean - Whether branch is operational
- `manager_id`: UUID - Branch manager user

```typescript
interface Branch {
  id: string;
  restaurantId: string;
  name: string;
  address: {
    street: string;
    city: string;
    coordinates: { lat: number; lng: number };
  };
  phone: string;
  operatingHours: Record<string, { open: string; close: string }>;
  isActive: boolean;
  managerId: string;
}
```

**Relationships:**
- Belongs to Restaurant
- Has many Orders
- Has many Staff assignments

### Customer
**Purpose:** Represents a WhatsApp customer with preferences and history

**Key Attributes:**
- `id`: UUID - Unique identifier
- `whatsapp_number`: string - Customer's WhatsApp number
- `name`: string - Customer name (if provided)
- `language_preference`: enum - Preferred language/dialect
- `dietary_restrictions`: array - Halal, vegetarian, allergies
- `tags`: array - Customer segments
- `lifetime_value`: decimal - Total spending
- `last_interaction`: timestamp - Most recent contact
- `conversation_context`: JSONB - Persistent conversation memory

```typescript
interface Customer {
  id: string;
  whatsappNumber: string;
  name?: string;
  languagePreference: 'ar-SA' | 'ar-EG' | 'ar-LV' | 'en';
  dietaryRestrictions: string[];
  tags: string[];
  lifetimeValue: number;
  lastInteraction: string;
  conversationContext: Record<string, any>;
}
```

**Relationships:**
- Has many Conversations
- Has many Orders
- Has many Feedback entries

### Conversation
**Purpose:** Represents a WhatsApp conversation thread with state management

**Key Attributes:**
- `id`: UUID - Unique identifier
- `customer_id`: UUID - Customer in conversation
- `restaurant_id`: UUID - Restaurant handling conversation
- `branch_id`: UUID - Assigned branch (if applicable)
- `status`: enum - active/escalated/resolved/abandoned
- `type`: enum - feedback/order/support/general
- `ai_confidence`: decimal - AI's confidence in responses
- `messages`: JSONB - Message history array
- `started_at`: timestamp - Conversation start
- `escalated_at`: timestamp - When escalated to human
- `resolved_at`: timestamp - When completed

```typescript
interface Conversation {
  id: string;
  customerId: string;
  restaurantId: string;
  branchId?: string;
  status: 'active' | 'escalated' | 'resolved' | 'abandoned';
  type: 'feedback' | 'order' | 'support' | 'general';
  aiConfidence: number;
  messages: Message[];
  startedAt: string;
  escalatedAt?: string;
  resolvedAt?: string;
}

interface Message {
  id: string;
  sender: 'customer' | 'ai' | 'staff';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}
```

**Relationships:**
- Belongs to Customer
- Belongs to Restaurant
- May belong to Branch
- May have associated Order or Feedback

### Order
**Purpose:** Represents a food order placed through WhatsApp

**Key Attributes:**
- `id`: UUID - Unique identifier
- `conversation_id`: UUID - Source conversation
- `customer_id`: UUID - Customer placing order
- `branch_id`: UUID - Fulfilling branch
- `items`: JSONB - Order items with modifications
- `total_amount`: decimal - Order total
- `status`: enum - pending/confirmed/preparing/ready/delivered
- `delivery_type`: enum - pickup/delivery
- `scheduled_time`: timestamp - Pickup/delivery time
- `special_instructions`: text - Customer notes

```typescript
interface Order {
  id: string;
  conversationId: string;
  customerId: string;
  branchId: string;
  items: OrderItem[];
  totalAmount: number;
  status: 'pending' | 'confirmed' | 'preparing' | 'ready' | 'delivered';
  deliveryType: 'pickup' | 'delivery';
  scheduledTime?: string;
  specialInstructions?: string;
}

interface OrderItem {
  menuItemId: string;
  name: string;
  quantity: number;
  price: number;
  modifications?: string[];
}
```

**Relationships:**
- Belongs to Conversation
- Belongs to Customer
- Belongs to Branch

### Feedback
**Purpose:** Captures customer feedback and ratings

**Key Attributes:**
- `id`: UUID - Unique identifier
- `conversation_id`: UUID - Source conversation
- `customer_id`: UUID - Customer providing feedback
- `branch_id`: UUID - Branch being reviewed
- `rating`: integer - 1-5 star rating
- `comment`: text - Feedback text
- `sentiment`: enum - positive/neutral/negative
- `categories`: array - Food quality, service, etc.
- `requires_followup`: boolean - Needs manager attention
- `created_at`: timestamp - Feedback timestamp

```typescript
interface Feedback {
  id: string;
  conversationId: string;
  customerId: string;
  branchId: string;
  rating: 1 | 2 | 3 | 4 | 5;
  comment?: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  categories: string[];
  requiresFollowup: boolean;
  createdAt: string;
}
```

**Relationships:**
- Belongs to Conversation
- Belongs to Customer
- Belongs to Branch
