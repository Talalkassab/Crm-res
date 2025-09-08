-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enum types
CREATE TYPE subscription_tier AS ENUM ('trial', 'basic', 'premium', 'enterprise');
CREATE TYPE personality_type AS ENUM ('formal', 'friendly', 'professional', 'casual');
CREATE TYPE conversation_status AS ENUM ('active', 'resolved', 'escalated', 'abandoned');
CREATE TYPE conversation_type AS ENUM ('feedback', 'order', 'inquiry', 'complaint', 'compliment');
CREATE TYPE message_type AS ENUM ('text', 'image', 'audio', 'document', 'template');
CREATE TYPE message_direction AS ENUM ('inbound', 'outbound');
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'staff');

-- Restaurants table (multi-tenant root)
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    whatsapp_number VARCHAR(20) UNIQUE NOT NULL,
    subscription_tier subscription_tier DEFAULT 'trial',
    personality_type personality_type DEFAULT 'friendly',
    settings JSONB DEFAULT '{}',
    location GEOGRAPHY(POINT),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'SA',
    timezone VARCHAR(50) DEFAULT 'Asia/Riyadh',
    prayer_times_enabled BOOLEAN DEFAULT true,
    language_preference VARCHAR(10) DEFAULT 'ar',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE restaurants ENABLE ROW LEVEL SECURITY;

-- Users table (restaurant staff)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    encrypted_password VARCHAR(255),
    role user_role DEFAULT 'staff',
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    whatsapp_number VARCHAR(20) NOT NULL,
    display_name VARCHAR(255),
    language_preference VARCHAR(10) DEFAULT 'ar',
    conversation_context JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    last_interaction_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(restaurant_id, whatsapp_number)
);

ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    status conversation_status DEFAULT 'active',
    type conversation_type DEFAULT 'inquiry',
    subject VARCHAR(255),
    summary TEXT,
    ai_confidence DECIMAL(3,2),
    escalated_to_user_id UUID REFERENCES users(id),
    escalated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    whatsapp_message_id VARCHAR(255),
    direction message_direction NOT NULL,
    type message_type DEFAULT 'text',
    content TEXT,
    metadata JSONB DEFAULT '{}',
    ai_generated BOOLEAN DEFAULT false,
    ai_model VARCHAR(100),
    sentiment_score DECIMAL(3,2),
    sentiment_label VARCHAR(20),
    processed_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    category VARCHAR(100),
    sentiment_score DECIMAL(3,2),
    sentiment_label VARCHAR(20),
    tags TEXT[],
    response_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Create indexes for performance
CREATE INDEX idx_restaurants_whatsapp_number ON restaurants(whatsapp_number);
CREATE INDEX idx_customers_restaurant_whatsapp ON customers(restaurant_id, whatsapp_number);
CREATE INDEX idx_customers_last_interaction ON customers(last_interaction_at DESC);
CREATE INDEX idx_conversations_restaurant_status ON conversations(restaurant_id, status);
CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_restaurant_created ON messages(restaurant_id, created_at DESC);
CREATE INDEX idx_messages_whatsapp_id ON messages(whatsapp_message_id);
CREATE INDEX idx_feedback_restaurant_created ON feedback(restaurant_id, created_at DESC);
CREATE INDEX idx_feedback_rating ON feedback(rating);

-- Create GIN indexes for JSONB columns
CREATE INDEX idx_customers_context ON customers USING GIN(conversation_context);
CREATE INDEX idx_customers_preferences ON customers USING GIN(preferences);
CREATE INDEX idx_restaurants_settings ON restaurants USING GIN(settings);
CREATE INDEX idx_messages_metadata ON messages USING GIN(metadata);

-- Create text search indexes for Arabic content
CREATE INDEX idx_messages_content_search ON messages USING GIN(to_tsvector('arabic', content));
CREATE INDEX idx_feedback_comment_search ON feedback USING GIN(to_tsvector('arabic', comment));

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_restaurants_updated_at BEFORE UPDATE ON restaurants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security Policies
-- Restaurants: Users can only access their own restaurant
CREATE POLICY restaurants_policy ON restaurants FOR ALL USING (
    auth.uid() IN (SELECT id FROM users WHERE restaurant_id = restaurants.id AND is_active = true)
);

-- Users: Users can only access users from their restaurant
CREATE POLICY users_policy ON users FOR ALL USING (
    auth.uid() = id OR 
    (auth.uid() IN (SELECT id FROM users u WHERE u.restaurant_id = users.restaurant_id AND u.is_active = true))
);

-- Customers: Users can only access customers from their restaurant
CREATE POLICY customers_policy ON customers FOR ALL USING (
    auth.uid() IN (SELECT id FROM users WHERE restaurant_id = customers.restaurant_id AND is_active = true)
);

-- Conversations: Users can only access conversations from their restaurant
CREATE POLICY conversations_policy ON conversations FOR ALL USING (
    auth.uid() IN (SELECT id FROM users WHERE restaurant_id = conversations.restaurant_id AND is_active = true)
);

-- Messages: Users can only access messages from their restaurant
CREATE POLICY messages_policy ON messages FOR ALL USING (
    auth.uid() IN (SELECT id FROM users WHERE restaurant_id = messages.restaurant_id AND is_active = true)
);

-- Feedback: Users can only access feedback from their restaurant
CREATE POLICY feedback_policy ON feedback FOR ALL USING (
    auth.uid() IN (SELECT id FROM users WHERE restaurant_id = feedback.restaurant_id AND is_active = true)
);