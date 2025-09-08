# Database Schema

## PostgreSQL Schema Definition

```sql
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis"; -- For location-based features
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For Arabic text search

-- Enum types
CREATE TYPE subscription_tier AS ENUM ('starter', 'growth', 'enterprise');
CREATE TYPE personality_type AS ENUM ('formal', 'casual', 'traditional', 'modern');
CREATE TYPE language_preference AS ENUM ('ar-SA', 'ar-EG', 'ar-LV', 'en');
CREATE TYPE conversation_status AS ENUM ('active', 'escalated', 'resolved', 'abandoned');
CREATE TYPE conversation_type AS ENUM ('feedback', 'order', 'support', 'general');
CREATE TYPE message_sender AS ENUM ('customer', 'ai', 'staff');
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled');
CREATE TYPE delivery_type AS ENUM ('pickup', 'delivery');
CREATE TYPE sentiment AS ENUM ('positive', 'neutral', 'negative');

-- Restaurants table
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name JSONB NOT NULL, -- {ar: "مطعم", en: "Restaurant"}
    subscription_tier subscription_tier DEFAULT 'starter',
    personality_type personality_type DEFAULT 'casual',
    timezone TEXT DEFAULT 'Asia/Riyadh',
    prayer_time_enabled BOOLEAN DEFAULT true,
    whatsapp_number TEXT UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Branches table
CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    address JSONB NOT NULL, -- {street, city, coordinates: {lat, lng}}
    phone TEXT NOT NULL,
    operating_hours JSONB NOT NULL, -- {monday: {open: "09:00", close: "22:00"}}
    is_active BOOLEAN DEFAULT true,
    manager_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    -- Spatial index for location queries
    location GEOGRAPHY(POINT, 4326) GENERATED ALWAYS AS (
        ST_SetSRID(ST_MakePoint(
            (address->>'coordinates')::json->>'lng'::float,
            (address->>'coordinates')::json->>'lat'::float
        ), 4326)
    ) STORED
);

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    whatsapp_number TEXT UNIQUE NOT NULL,
    name TEXT,
    language_preference language_preference DEFAULT 'ar-SA',
    dietary_restrictions TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    lifetime_value DECIMAL(10,2) DEFAULT 0,
    last_interaction TIMESTAMPTZ,
    conversation_context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id),
    branch_id UUID REFERENCES branches(id),
    status conversation_status DEFAULT 'active',
    type conversation_type DEFAULT 'general',
    ai_confidence DECIMAL(3,2),
    messages JSONB DEFAULT '[]', -- Array of message objects
    started_at TIMESTAMPTZ DEFAULT NOW(),
    escalated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    branch_id UUID NOT NULL REFERENCES branches(id),
    items JSONB NOT NULL, -- Array of {menuItemId, name, quantity, price, modifications}
    total_amount DECIMAL(10,2) NOT NULL,
    status order_status DEFAULT 'pending',
    delivery_type delivery_type DEFAULT 'pickup',
    scheduled_time TIMESTAMPTZ,
    special_instructions TEXT,
    pos_order_id TEXT, -- External POS system ID
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    branch_id UUID NOT NULL REFERENCES branches(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    sentiment sentiment,
    categories TEXT[] DEFAULT '{}',
    requires_followup BOOLEAN DEFAULT false,
    followup_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security Policies
ALTER TABLE restaurants ENABLE ROW LEVEL SECURITY;
ALTER TABLE branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policies for multi-tenancy
CREATE POLICY "Users can view own restaurant" ON restaurants
    FOR ALL USING (auth.uid() IN (
        SELECT id FROM users WHERE restaurant_id = restaurants.id
    ));

CREATE POLICY "Users can view own branches" ON branches
    FOR ALL USING (restaurant_id IN (
        SELECT restaurant_id FROM users WHERE id = auth.uid()
    ));

-- Create indexes for performance
CREATE INDEX idx_customers_whatsapp ON customers(whatsapp_number);
CREATE INDEX idx_conversations_restaurant ON conversations(restaurant_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_started ON conversations(started_at DESC);
CREATE INDEX idx_orders_branch ON orders(branch_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
CREATE INDEX idx_feedback_branch ON feedback(branch_id);
CREATE INDEX idx_feedback_sentiment ON feedback(sentiment);
CREATE INDEX idx_feedback_created ON feedback(created_at DESC);
```

## Indexing Strategy

1. **Primary Keys** - UUID for all tables (globally unique, no collisions)
2. **Foreign Keys** - Indexed automatically for joins
3. **Phone Numbers** - Indexed for fast customer lookup
4. **Timestamps** - DESC indexes for recent data queries
5. **Status Fields** - Indexed for filtering active/pending items
6. **Spatial Index** - PostGIS for location-based branch queries
7. **Text Search** - pg_trgm for Arabic text searching
