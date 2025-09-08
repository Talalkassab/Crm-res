-- Migration 007: Feedback Collection System
-- Creates tables for feedback campaigns, A/B testing, and analytics

-- Feedback campaigns table
CREATE TABLE IF NOT EXISTS feedback_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' 
        CHECK (status IN ('draft', 'scheduled', 'active', 'completed', 'cancelled', 'deleted')),
    scheduled_start TIMESTAMPTZ,
    scheduled_end TIMESTAMPTZ,
    settings JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    deleted_at TIMESTAMPTZ
);

-- Campaign recipients table
CREATE TABLE IF NOT EXISTS campaign_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES feedback_campaigns(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    visit_timestamp TIMESTAMPTZ NOT NULL,
    scheduled_send_time TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'responded', 'failed')),
    conversation_id UUID REFERENCES conversations(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Campaign messages tracking table
CREATE TABLE IF NOT EXISTS campaign_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES feedback_campaigns(id) ON DELETE CASCADE,
    recipient_id UUID REFERENCES campaign_recipients(id) ON DELETE CASCADE,
    message_template VARCHAR(50),
    variant_id VARCHAR(50), -- For A/B testing
    task_id VARCHAR(255), -- Celery task ID
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    response_received_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'queued', 'sent', 'delivered', 'read', 'responded', 'failed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- A/B testing experiments table
CREATE TABLE IF NOT EXISTS feedback_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES feedback_campaigns(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    variants JSONB NOT NULL, -- Array of variant configurations
    assignment_strategy VARCHAR(20) DEFAULT 'weighted'
        CHECK (assignment_strategy IN ('random', 'weighted', 'hash_based')),
    min_sample_size INTEGER DEFAULT 100,
    confidence_level DECIMAL(3,2) DEFAULT 0.95,
    status VARCHAR(20) DEFAULT 'draft'
        CHECK (status IN ('draft', 'running', 'paused', 'completed', 'archived')),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    winning_variant VARCHAR(50),
    statistical_significance JSONB,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Variant assignments tracking
CREATE TABLE IF NOT EXISTS variant_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES feedback_experiments(id) ON DELETE CASCADE,
    customer_phone VARCHAR(20) NOT NULL,
    variant_id VARCHAR(50) NOT NULL,
    campaign_id UUID REFERENCES feedback_campaigns(id),
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(experiment_id, customer_phone) -- One assignment per customer per experiment
);

-- Enhanced feedback table (extends existing feedback functionality)
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES feedback_campaigns(id),
    campaign_recipient_id UUID REFERENCES campaign_recipients(id),
    message_id UUID REFERENCES campaign_messages(id),
    
    -- Ratings
    overall_rating INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 5),
    food_quality_rating INTEGER CHECK (food_quality_rating >= 1 AND food_quality_rating <= 5),
    service_rating INTEGER CHECK (service_rating >= 1 AND service_rating <= 5),
    cleanliness_rating INTEGER CHECK (cleanliness_rating >= 1 AND cleanliness_rating <= 5),
    value_rating INTEGER CHECK (value_rating >= 1 AND value_rating <= 5),
    
    -- Sentiment analysis
    sentiment_score DECIMAL(4,3) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    confidence_score DECIMAL(4,3) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Content
    message TEXT NOT NULL,
    topics TEXT[], -- Array of mentioned topics
    specific_items TEXT[], -- Specific dishes/items mentioned
    key_phrases TEXT[],
    
    -- Extracted insights
    improvement_suggestions TEXT[],
    would_recommend BOOLEAN,
    is_repeat_customer BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    feedback_type VARCHAR(20) DEFAULT 'campaign'
        CHECK (feedback_type IN ('campaign', 'organic', 'survey')),
    collection_method VARCHAR(20) DEFAULT 'whatsapp'
        CHECK (collection_method IN ('whatsapp', 'web', 'sms', 'email')),
    conversation_length INTEGER, -- Number of messages in feedback conversation
    template_used VARCHAR(50),
    variant_id VARCHAR(50), -- A/B test variant if applicable
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    extracted_at TIMESTAMPTZ -- When AI extraction was completed
);

-- Feedback alerts table
CREATE TABLE IF NOT EXISTS feedback_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    feedback_id UUID REFERENCES feedback(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    campaign_id UUID REFERENCES feedback_campaigns(id),
    
    rule_id VARCHAR(50) NOT NULL, -- Which alert rule triggered this
    priority VARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('low', 'medium', 'high', 'immediate')),
    title VARCHAR(255) NOT NULL,
    message TEXT,
    details JSONB DEFAULT '{}',
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'acknowledged', 'resolved', 'dismissed')),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by UUID REFERENCES users(id),
    acknowledgment_notes TEXT,
    resolved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Real-time alerts broadcast table (for Supabase Realtime)
CREATE TABLE IF NOT EXISTS realtime_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(255) NOT NULL, -- e.g., "alerts:restaurant_id"
    type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Analytics reports storage
CREATE TABLE IF NOT EXISTS analytics_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    report_type VARCHAR(50) NOT NULL DEFAULT 'daily_summary',
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(restaurant_id, report_date, report_type)
);

-- Report schedules table
CREATE TABLE IF NOT EXISTS report_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL,
    frequency VARCHAR(20) NOT NULL 
        CHECK (frequency IN ('daily', 'weekly', 'monthly')),
    schedule_time TIME,
    timezone VARCHAR(50) DEFAULT 'Asia/Riyadh',
    delivery_channels TEXT[] DEFAULT ARRAY['whatsapp'],
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Notification preferences per user
CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT TRUE,
    whatsapp_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,
    alert_threshold VARCHAR(20) DEFAULT 'medium'
        CHECK (alert_threshold IN ('low', 'medium', 'high')),
    report_frequency VARCHAR(20) DEFAULT 'daily'
        CHECK (report_frequency IN ('daily', 'weekly', 'monthly', 'disabled')),
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(restaurant_id, user_id)
);

-- Device tokens for push notifications
CREATE TABLE IF NOT EXISTS device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL,
    device_type VARCHAR(20) NOT NULL
        CHECK (device_type IN ('ios', 'android', 'web')),
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, token)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_feedback_campaigns_restaurant_status 
    ON feedback_campaigns(restaurant_id, status) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_campaign_recipients_campaign_status 
    ON campaign_recipients(campaign_id, status);

CREATE INDEX IF NOT EXISTS idx_campaign_recipients_phone_timestamp 
    ON campaign_recipients(phone_number, visit_timestamp);

CREATE INDEX IF NOT EXISTS idx_campaign_messages_scheduled_time 
    ON campaign_messages(scheduled_send_time) WHERE status IN ('scheduled', 'queued');

CREATE INDEX IF NOT EXISTS idx_feedback_restaurant_created 
    ON feedback(restaurant_id, created_at);

CREATE INDEX IF NOT EXISTS idx_feedback_campaign_rating 
    ON feedback(campaign_id, overall_rating) WHERE campaign_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_feedback_sentiment 
    ON feedback(restaurant_id, sentiment_score) WHERE sentiment_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_feedback_alerts_restaurant_status 
    ON feedback_alerts(restaurant_id, status, priority);

CREATE INDEX IF NOT EXISTS idx_feedback_alerts_created 
    ON feedback_alerts(created_at) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_analytics_reports_restaurant_date 
    ON analytics_reports(restaurant_id, report_date, report_type);

CREATE INDEX IF NOT EXISTS idx_variant_assignments_experiment_customer 
    ON variant_assignments(experiment_id, customer_phone);

-- Full text search indexes
CREATE INDEX IF NOT EXISTS idx_feedback_message_fts 
    ON feedback USING gin(to_tsvector('arabic', message));

CREATE INDEX IF NOT EXISTS idx_feedback_topics_gin 
    ON feedback USING gin(topics);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables with updated_at
CREATE TRIGGER update_feedback_campaigns_updated_at 
    BEFORE UPDATE ON feedback_campaigns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaign_recipients_updated_at 
    BEFORE UPDATE ON campaign_recipients 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaign_messages_updated_at 
    BEFORE UPDATE ON campaign_messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_experiments_updated_at 
    BEFORE UPDATE ON feedback_experiments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_updated_at 
    BEFORE UPDATE ON feedback 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_alerts_updated_at 
    BEFORE UPDATE ON feedback_alerts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_reports_updated_at 
    BEFORE UPDATE ON analytics_reports 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_report_schedules_updated_at 
    BEFORE UPDATE ON report_schedules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_preferences_updated_at 
    BEFORE UPDATE ON notification_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) policies
ALTER TABLE feedback_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_recipients ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE variant_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE realtime_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_tokens ENABLE ROW LEVEL SECURITY;

-- Example RLS policies (customize based on your auth setup)
CREATE POLICY "Users can manage their restaurant's campaigns" 
    ON feedback_campaigns FOR ALL 
    USING (restaurant_id IN (
        SELECT restaurant_id FROM user_restaurant_access 
        WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can view their restaurant's feedback" 
    ON feedback FOR SELECT 
    USING (restaurant_id IN (
        SELECT restaurant_id FROM user_restaurant_access 
        WHERE user_id = auth.uid()
    ));

-- Add comments for documentation
COMMENT ON TABLE feedback_campaigns IS 'Feedback collection campaigns with CSV uploads and scheduling';
COMMENT ON TABLE campaign_recipients IS 'Recipients from CSV uploads for each campaign';
COMMENT ON TABLE campaign_messages IS 'Individual message tracking with status updates';
COMMENT ON TABLE feedback_experiments IS 'A/B test experiments for optimizing feedback collection';
COMMENT ON TABLE variant_assignments IS 'Tracks which customers got which A/B test variants';
COMMENT ON TABLE feedback IS 'Structured feedback data extracted from conversations';
COMMENT ON TABLE feedback_alerts IS 'Real-time alerts for negative feedback requiring attention';
COMMENT ON TABLE analytics_reports IS 'Generated reports with insights and metrics';
COMMENT ON TABLE report_schedules IS 'Automated report delivery schedules';
COMMENT ON TABLE notification_preferences IS 'User preferences for alerts and reports';

-- Sample data for testing (optional)
-- INSERT INTO feedback_campaigns (restaurant_id, name, description, status) 
-- VALUES (gen_random_uuid(), 'Test Campaign', 'Testing feedback collection', 'draft');

COMMIT;