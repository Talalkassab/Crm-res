-- Seed data for development and testing

-- Insert sample restaurant
INSERT INTO restaurants (
    id,
    name,
    description,
    whatsapp_number,
    subscription_tier,
    personality_type,
    address,
    city,
    country,
    settings
) VALUES (
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'Al Baik Restaurant',
    'Famous Saudi fast food chain specializing in fried chicken',
    '+966501234567',
    'premium',
    'friendly',
    'King Fahd Road, Al Malaz District',
    'Riyadh',
    'SA',
    '{
        "operating_hours": {
            "sunday": {"open": "11:00", "close": "23:00"},
            "monday": {"open": "11:00", "close": "23:00"},
            "tuesday": {"open": "11:00", "close": "23:00"},
            "wednesday": {"open": "11:00", "close": "23:00"},
            "thursday": {"open": "11:00", "close": "23:00"},
            "friday": {"open": "14:00", "close": "23:00"},
            "saturday": {"open": "11:00", "close": "23:00"}
        },
        "menu_categories": ["chicken", "burgers", "sides", "drinks"],
        "payment_methods": ["cash", "card", "stc_pay", "apple_pay"],
        "delivery_areas": ["Al Malaz", "Al Olaya", "Al Sulaymaniyyah"]
    }'
);

-- Insert sample admin user
INSERT INTO users (
    id,
    email,
    role,
    restaurant_id,
    first_name,
    last_name,
    phone,
    is_active
) VALUES (
    'a47ac10b-58cc-4372-a567-0e02b2c3d480',
    'admin@albaik.com',
    'admin',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'Ahmed',
    'Al-Rashid',
    '+966501234568',
    true
);

-- Insert sample manager user
INSERT INTO users (
    id,
    email,
    role,
    restaurant_id,
    first_name,
    last_name,
    phone,
    is_active
) VALUES (
    'b47ac10b-58cc-4372-a567-0e02b2c3d481',
    'manager@albaik.com',
    'manager',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'Fatima',
    'Al-Zahra',
    '+966501234569',
    true
);

-- Insert sample customers
INSERT INTO customers (
    id,
    restaurant_id,
    whatsapp_number,
    display_name,
    language_preference,
    conversation_context,
    preferences,
    total_orders,
    total_spent,
    last_interaction_at
) VALUES 
(
    'c47ac10b-58cc-4372-a567-0e02b2c3d482',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    '+966505555001',
    'Omar Al-Harbi',
    'ar',
    '{"preferred_name": "أبو عبدالله", "dietary_restrictions": [], "usual_orders": ["chicken_meal", "garlic_sauce"]}',
    '{"notification_time": "evening", "spice_level": "medium", "delivery_address": "Al Malaz District"}',
    15,
    450.00,
    NOW() - INTERVAL '2 days'
),
(
    'd47ac10b-58cc-4372-a567-0e02b2c3d483',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    '+966505555002',
    'Sarah Al-Qahtani',
    'ar',
    '{"preferred_name": "أم محمد", "dietary_restrictions": ["no_spicy"], "usual_orders": ["burger_meal"]}',
    '{"notification_time": "afternoon", "spice_level": "mild", "delivery_address": "Al Olaya District"}',
    8,
    240.00,
    NOW() - INTERVAL '1 day'
),
(
    'e47ac10b-58cc-4372-a567-0e02b2c3d484',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    '+966505555003',
    'Mohammed Al-Ghamdi',
    'en',
    '{"preferred_name": "Mohammed", "dietary_restrictions": [], "usual_orders": ["family_meal"]}',
    '{"notification_time": "evening", "spice_level": "hot", "delivery_address": "Al Sulaymaniyyah District"}',
    22,
    880.00,
    NOW() - INTERVAL '3 hours'
);

-- Insert sample conversations
INSERT INTO conversations (
    id,
    restaurant_id,
    customer_id,
    status,
    type,
    subject,
    summary,
    ai_confidence,
    started_at,
    last_message_at
) VALUES 
(
    'f47ac10b-58cc-4372-a567-0e02b2c3d485',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'c47ac10b-58cc-4372-a567-0e02b2c3d482',
    'resolved',
    'feedback',
    'Customer Feedback - Excellent Service',
    'Customer provided positive feedback about food quality and delivery time',
    0.95,
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days' + INTERVAL '5 minutes'
),
(
    'g47ac10b-58cc-4372-a567-0e02b2c3d486',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'd47ac10b-58cc-4372-a567-0e02b2c3d483',
    'active',
    'order',
    'New Order Request',
    'Customer requesting to place a new order for delivery',
    0.88,
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '30 minutes'
);

-- Insert sample messages
INSERT INTO messages (
    id,
    conversation_id,
    restaurant_id,
    whatsapp_message_id,
    direction,
    type,
    content,
    ai_generated,
    sentiment_score,
    sentiment_label,
    created_at
) VALUES 
(
    'h47ac10b-58cc-4372-a567-0e02b2c3d487',
    'f47ac10b-58cc-4372-a567-0e02b2c3d485',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'whatsapp_msg_001',
    'inbound',
    'text',
    'السلام عليكم، أريد أن أشكركم على الخدمة الممتازة والطعام اللذيذ. استمروا على هذا المستوى الرائع!',
    false,
    0.92,
    'positive',
    NOW() - INTERVAL '2 days'
),
(
    'i47ac10b-58cc-4372-a567-0e02b2c3d488',
    'f47ac10b-58cc-4372-a567-0e02b2c3d485',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'whatsapp_msg_002',
    'outbound',
    'text',
    'وعليكم السلام أبو عبدالله، شكراً جزيلاً لك على كلماتك الطيبة! نحن سعداء جداً لرضاك عن خدمتنا. هل تود أن نرسل لك عرضاً خاصاً كتقدير لولائك؟',
    true,
    0.85,
    'positive',
    NOW() - INTERVAL '2 days' + INTERVAL '2 minutes'
),
(
    'j47ac10b-58cc-4372-a567-0e02b2c3d489',
    'g47ac10b-58cc-4372-a567-0e02b2c3d486',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'whatsapp_msg_003',
    'inbound',
    'text',
    'مرحبا، أريد أطلب وجبة دجاج عادية مع صوص الثوم وبطاطس كبيرة',
    false,
    0.75,
    'neutral',
    NOW() - INTERVAL '1 hour'
);

-- Insert sample feedback
INSERT INTO feedback (
    id,
    restaurant_id,
    customer_id,
    conversation_id,
    rating,
    comment,
    category,
    sentiment_score,
    sentiment_label,
    tags,
    response_sent
) VALUES 
(
    'k47ac10b-58cc-4372-a567-0e02b2c3d490',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'c47ac10b-58cc-4372-a567-0e02b2c3d482',
    'f47ac10b-58cc-4372-a567-0e02b2c3d485',
    5,
    'الخدمة ممتازة والطعام لذيذ جداً. الطلب وصل سريع وساخن. شكراً لكم',
    'service_quality',
    0.95,
    'positive',
    ARRAY['excellent_service', 'fast_delivery', 'hot_food', 'satisfied_customer'],
    true
),
(
    'l47ac10b-58cc-4372-a567-0e02b2c3d491',
    'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'd47ac10b-58cc-4372-a567-0e02b2c3d483',
    NULL,
    4,
    'الطعام جيد لكن التوصيل تأخر قليلاً',
    'delivery',
    0.65,
    'mixed',
    ARRAY['good_food', 'delayed_delivery', 'room_for_improvement'],
    false
);