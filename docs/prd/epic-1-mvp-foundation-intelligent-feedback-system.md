# Epic 1: MVP - Foundation & Intelligent Feedback System

**Goal:** Deliver a complete working product that proves the core value proposition by combining WhatsApp integration with culturally-aware AI to collect intelligent feedback. This epic establishes technical foundation while providing immediate value to pilot restaurants through automated, culturally-appropriate customer engagement.

## Story 1.1: Project Foundation and Development Environment

**As a** developer,  
**I want** a properly configured monorepo with development environment,  
**So that** the team can begin building features with consistent tooling and structure.

**Acceptance Criteria:**
1. Monorepo initialized with Turborepo, containing `/apps/dashboard`, `/apps/api`, `/services/whatsapp`, `/packages/shared` structure
2. Next.js 14+ dashboard app created with TypeScript, Tailwind CSS, and RTL support configured
3. Python FastAPI service skeleton created for future AI processing with basic health check endpoint
4. Node.js/TypeScript API service initialized with Express/Fastify for real-time operations
5. Docker Compose configuration enables local development with all services running
6. GitHub repository created with branch protection, PR templates, and GitHub Actions CI pipeline
7. README documentation includes setup instructions, architecture overview, and development guidelines
8. Supabase project initialized with basic schema for restaurants, conversations, and messages tables

## Story 1.2: WhatsApp Business API Integration

**As a** restaurant owner,  
**I want** my restaurant connected to WhatsApp Business API,  
**So that** I can automatically receive and respond to customer messages.

**Acceptance Criteria:**
1. WhatsApp Cloud API webhook endpoint receives and verifies incoming messages with signature validation
2. Message queue (BullMQ) processes incoming messages asynchronously with retry logic
3. Basic echo response confirms message receipt (temporary, replaced by AI in next story)
4. Outbound message sending works with template messages for feedback requests
5. Phone number provisioning process documented for restaurant onboarding
6. Rate limiting implemented to stay within WhatsApp's 80 messages/second limit
7. Webhook processes message status updates (sent, delivered, read) for analytics
8. Error handling gracefully manages API failures with exponential backoff

## Story 1.3: Gemini Flash AI Integration with Arabic Support

**As a** restaurant owner,  
**I want** culturally-aware AI handling customer conversations in Arabic,  
**So that** feedback collection feels natural and personalized.

**Acceptance Criteria:**
1. Gemini Flash 2.0 integrated with Arabic-optimized system prompts
2. Basic personality templates (Formal/Casual) with Arabic dialect awareness
3. Saudi, Egyptian, Levantine dialects recognized with appropriate responses
4. Prayer time intelligence delays messages during religious observances
5. Sentiment analysis identifies negative feedback for immediate alerts
6. Common Arabic greetings and cultural phrases handled appropriately
7. Conversation context maintained for coherent multi-turn dialogues
8. Human escalation triggered for complex or negative scenarios

## Story 1.4: Intelligent Feedback Collection System

**As a** restaurant owner,  
**I want** automated feedback requests that adapt to customer responses,  
**So that** I collect more detailed insights from the silent majority.

**Acceptance Criteria:**
1. CSV upload for customer phone numbers with visit timestamps
2. AI-powered feedback requests sent 2-4 hours post-visit with prayer time awareness
3. Natural conversation flow adapts based on initial rating (probe issues if negative)
4. Sentiment-appropriate responses thank happy customers, apologize to unhappy ones
5. Detailed feedback extraction from conversational responses using AI
6. Real-time alerts for negative feedback requiring immediate attention
7. Daily summary reports with AI-generated insights from feedback patterns
8. A/B testing different feedback request approaches for optimization

## Story 1.5: Minimal Viable Dashboard

**As a** restaurant owner,  
**I want** to monitor AI conversations and feedback metrics,  
**So that** I can track system performance and customer satisfaction.

**Acceptance Criteria:**
1. Real-time conversation monitor shows active AI chats with intervention capability
2. Feedback analytics display ratings, sentiment trends, and response rates
3. Message history searchable by customer phone or content
4. AI performance metrics show automation rate and escalation frequency
5. Mobile-responsive design works on phones (primary usage device)
6. Arabic/English toggle for interface language
7. Export functionality for feedback data (CSV format)
8. Configuration panel for basic settings (hours, personality, escalation rules)
