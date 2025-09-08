# CRM-RES Fullstack Architecture Document

## Introduction

This document outlines the complete fullstack architecture for CRM-RES, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

### Starter Template or Existing Project

Given the WhatsApp-centric nature and real-time requirements, this is a greenfield project optimized for:
- **Vercel + Supabase** for rapid development with built-in real-time capabilities
- **AWS Serverless** for enterprise scale with containerized microservices
- **Custom Python/Next.js** with WhatsApp Cloud API integration

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-07 | v1.0 | Initial fullstack architecture document | Winston (Architect) |

## High Level Architecture

### Technical Summary

The CRM-RES platform employs a containerized microservices architecture orchestrated on AWS ECS Fargate, utilizing Next.js for the restaurant dashboard and Python microservices in Docker containers for backend services. The system integrates directly with WhatsApp Cloud API for messaging, OpenRouter for AI-powered conversations, and maintains real-time state through Supabase (PostgreSQL) with realtime subscriptions for service orchestration. This architecture achieves sub-30 second response times through Application Load Balancer with CloudFront distribution, while supporting 100,000 concurrent conversations through auto-scaling container tasks and service mesh communication.

### Platform and Infrastructure Choice

**Platform:** AWS with Container Orchestration  
**Key Services:** ECS Fargate, ECR, ALB, Supabase, EventBridge, SQS, CloudFront, Cognito  
**Deployment Regions:** Primary: me-south-1 (Bahrain), Secondary: eu-west-1 (Ireland)  
**Container Orchestration:** ECS Fargate (serverless containers without managing EC2 instances)  
**Service Mesh:** AWS App Mesh for inter-service communication and observability

### Repository Structure

**Structure:** Monorepo with containerized services  
**Monorepo Tool:** Turborepo with Docker Compose for local development  
**Package Organization:**
- `/apps/dashboard` - Next.js restaurant owner dashboard (containerized)
- `/apps/api` - Core REST API service (containerized)
- `/services/whatsapp` - WhatsApp gateway service (containerized)
- `/services/ai` - AI processing service (containerized)
- `/services/analytics` - Real-time metrics service (containerized)
- `/packages/shared` - Shared types and utilities
- `/packages/ui` - Shared React components
- `/docker` - Dockerfile configurations for each service
- `/k8s` - Kubernetes manifests for future migration option

### High Level Architecture Diagram

```mermaid
graph TB
    subgraph "Customer Layer"
        WA[WhatsApp Users]
        OWNERS[Restaurant Owners]
    end
    
    subgraph "Edge Layer"
        CF[CloudFront CDN]
        ALB[Application Load Balancer]
    end
    
    subgraph "Container Platform - ECS Fargate"
        subgraph "Service Mesh - App Mesh"
            DASH[Dashboard Container<br/>Next.js:3000]
            WG[WhatsApp Gateway<br/>Python:3001]
            AI[AI Processor<br/>Python:3002]
            CORE[Core API<br/>Python:3003]
            ANALYTICS[Analytics Service<br/>Python:3004]
            NOTIFY[Notification Service<br/>Python:3005]
        end
    end
    
    subgraph "Data Layer"
        DB[(Supabase PostgreSQL)]
        S3[(S3 Storage)]
        REDIS[(ElastiCache)]
        ECR[ECR Registry]
    end
    
    subgraph "Integration Layer"
        WAAPI[WhatsApp Cloud API]
        OR[OpenRouter API]
        POS[Restaurant POS APIs]
    end
    
    subgraph "Event/Queue Layer"
        EB[EventBridge]
        SQS[SQS Queues]
    end
    
    WA --> WAAPI
    WAAPI --> ALB
    ALB --> WG
    
    OWNERS --> CF
    CF --> ALB
    ALB --> DASH
    ALB --> CORE
    
    WG --> EB
    EB --> AI
    EB --> ANALYTICS
    EB --> NOTIFY
    
    AI --> OR
    AI --> DB
    CORE --> DB
    CORE --> REDIS
    
    WG --> SQS
    ANALYTICS --> DB
    
    ECR -.-> Service Mesh
```

### Architectural Patterns

- **Containerized Microservices:** Docker containers on ECS Fargate for consistent deployment and local development parity - *Rationale:* Ensures "works on my machine" equals production behavior
- **Service Mesh Pattern:** AWS App Mesh for service discovery, load balancing, and observability - *Rationale:* Simplifies inter-service communication and provides detailed metrics
- **Event-Driven Architecture:** EventBridge for service decoupling and async processing - *Rationale:* Enables real-time message processing without tight coupling
- **Sidecar Pattern:** Envoy proxy sidecars for service mesh communication - *Rationale:* Handles retries, circuit breaking, and distributed tracing transparently
- **Repository Pattern:** Abstract database access for testability - *Rationale:* Enables database migration flexibility
- **API Gateway Pattern:** ALB with path-based routing to different services - *Rationale:* Centralized entry point with health checks and auto-scaling
- **Circuit Breaker Pattern:** Built into service mesh for resilient external API calls - *Rationale:* Prevents cascade failures automatically
- **Blue-Green Deployment:** ECS service updates with automated rollback - *Rationale:* Zero-downtime deployments with instant rollback capability

## Tech Stack

This is the **DEFINITIVE** technology selection for the entire CRM-RES platform. All development must use these exact versions.

### Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| Frontend Language | TypeScript | 5.3+ | Type-safe React development | Prevents runtime errors in complex dashboard |
| Frontend Framework | Next.js | 14.2+ | React framework with SSR/SSG | Optimal performance, Vercel integration |
| UI Component Library | Shadcn/ui + Tailwind | Latest | Customizable component system | Full control, Arabic RTL support |
| State Management | Zustand | 4.5+ | Lightweight state management | Simple, TypeScript-first |
| Backend Language | Python | 3.12+ | API and service development | Superior AI/ML libraries, Arabic NLP support |
| Backend Framework | FastAPI | 0.110+ | Modern async web framework | Automatic OpenAPI, async support, type hints |
| API Style | REST + WebSockets | OpenAPI 3.0 | HTTP APIs + real-time updates | FastAPI auto-generation, Supabase Realtime |
| Database | Supabase (PostgreSQL) | Latest | Relational DB with realtime | Built-in auth, realtime, RLS, instant APIs |
| Cache | Redis (Supabase) | 7.1 | In-memory caching | Integrated with Supabase, managed service |
| File Storage | Supabase Storage | Latest | Object storage for media | Integrated S3-compatible storage |
| Authentication | Supabase Auth | Latest | User auth and authorization | Built-in MFA, social logins, JWT tokens |
| Frontend Testing | Vitest + React Testing Library | Latest | Unit and component testing | Fast, Jest-compatible |
| Backend Testing | Pytest | 8.0+ | Python testing framework | Async support, fixtures, comprehensive |
| E2E Testing | Playwright | 1.42+ | Browser automation testing | Cross-browser, Python bindings available |
| Build Tool | Turborepo | 1.13+ | Monorepo orchestration | Manages mixed Python/TS repos |
| Bundler | Vite | 5.1+ | Frontend bundling | Lightning fast HMR |
| Container Platform | Docker | 24+ | Containerization | Python and Node.js containers |
| Container Orchestration | ECS Fargate | Managed | Container orchestration | Serverless containers |
| IaC Tool | Pulumi (Python) | Latest | Infrastructure as Code | Python-native IaC, type safety |
| CI/CD | GitHub Actions | Latest | Continuous Integration/Deployment | Matrix builds for Python/TS |
| Monitoring | Supabase Dashboard + DataDog | Latest | Metrics and observability | Built-in DB metrics + APM |
| Logging | Supabase Logs + CloudWatch | Latest | Centralized logging | Query logs, function logs |
| CSS Framework | Tailwind CSS | 3.4+ | Utility-first CSS | RTL support, small bundle |
| Message Queue | Supabase Queue + SQS | Latest | Async messaging | PG-based queue + AWS for WhatsApp |
| AI/ML | OpenRouter API | Latest | LLM Gateway | Multi-provider access, cost optimization |
| WhatsApp Integration | WhatsApp Cloud API | v19.0 | Messaging platform | Official API, webhook support |
| ML Libraries | LangChain + Transformers | Latest | AI orchestration and NLP | Arabic processing, conversation memory |
| Data Processing | Pandas + Polars | Latest | Analytics processing | Fast data transformation |
| Async Runtime | asyncio + httpx | Latest | Async Python operations | High-performance async I/O |

## Data Models

### Core Data Models

#### Restaurant
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

#### Branch
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

#### Customer
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

#### Conversation
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

#### Order
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

#### Feedback
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

## API Specification

Based on the REST API choice with WebSocket support, here's the comprehensive API specification for the CRM-RES platform.

### REST API Specification

```yaml
openapi: 3.0.0
info:
  title: CRM-RES WhatsApp Platform API
  version: 1.0.0
  description: REST API for Saudi restaurant WhatsApp automation platform
servers:
  - url: https://api.crm-res.com/v1
    description: Production API
  - url: https://staging-api.crm-res.com/v1
    description: Staging API

paths:
  # WhatsApp Webhook Endpoints
  /webhooks/whatsapp:
    post:
      summary: WhatsApp message webhook
      operationId: receiveWhatsAppMessage
      tags: [WhatsApp]
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WhatsAppWebhook'
      responses:
        '200':
          description: Message received
    get:
      summary: WhatsApp webhook verification
      operationId: verifyWhatsAppWebhook
      tags: [WhatsApp]
      parameters:
        - name: hub.mode
          in: query
          required: true
          schema:
            type: string
        - name: hub.verify_token
          in: query
          required: true
          schema:
            type: string
        - name: hub.challenge
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Challenge returned

  # Conversation Management
  /conversations:
    get:
      summary: List conversations
      operationId: listConversations
      tags: [Conversations]
      security:
        - bearerAuth: []
      parameters:
        - name: restaurant_id
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            type: string
            enum: [active, escalated, resolved, abandoned]
        - name: branch_id
          in: query
          schema:
            type: string
            format: uuid
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: List of conversations
          content:
            application/json:
              schema:
                type: object
                properties:
                  conversations:
                    type: array
                    items:
                      $ref: '#/components/schemas/Conversation'
                  total:
                    type: integer

  /conversations/{id}:
    get:
      summary: Get conversation details
      operationId: getConversation
      tags: [Conversations]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Conversation details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Conversation'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    WhatsAppWebhook:
      type: object
      properties:
        entry:
          type: array
          items:
            type: object
            properties:
              changes:
                type: array
                items:
                  type: object
                  properties:
                    value:
                      type: object
                      properties:
                        messages:
                          type: array
                        statuses:
                          type: array

    Conversation:
      type: object
      properties:
        id:
          type: string
          format: uuid
        customer_id:
          type: string
          format: uuid
        restaurant_id:
          type: string
          format: uuid
        branch_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [active, escalated, resolved, abandoned]
        type:
          type: string
          enum: [feedback, order, support, general]
        ai_confidence:
          type: number
        messages:
          type: array
          items:
            $ref: '#/components/schemas/Message'
        started_at:
          type: string
          format: date-time

    Message:
      type: object
      properties:
        id:
          type: string
        sender:
          type: string
          enum: [customer, ai, staff]
        content:
          type: string
        timestamp:
          type: string
          format: date-time
```

### WebSocket Events (via Supabase Realtime)

```typescript
// Realtime Subscription Events
interface RealtimeEvents {
  // New conversation started
  'conversation:new': {
    conversation: Conversation;
    customer: Customer;
  };

  // Conversation status changed
  'conversation:status': {
    conversationId: string;
    oldStatus: string;
    newStatus: string;
  };

  // New message in conversation
  'message:new': {
    conversationId: string;
    message: Message;
  };

  // AI confidence dropped (needs attention)
  'ai:low_confidence': {
    conversationId: string;
    confidence: number;
    suggestedAction: string;
  };

  // New order placed
  'order:new': {
    order: Order;
    branchId: string;
  };

  // Negative feedback received
  'feedback:negative': {
    feedback: Feedback;
    requiresFollowup: boolean;
  };
}

// Supabase Realtime Channel Setup
const channel = supabase
  .channel('restaurant_updates')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'conversations',
    filter: `restaurant_id=eq.${restaurantId}`
  }, handleNewConversation)
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'conversations',
    filter: `restaurant_id=eq.${restaurantId}`
  }, handleConversationUpdate)
  .subscribe();
```

## Components

Based on the hybrid architecture with Python backend and TypeScript frontend, here are the major logical components across the fullstack.

### Backend Components (Python/FastAPI)

#### WhatsApp Gateway Service
**Responsibility:** Manages all WhatsApp Cloud API interactions, webhook processing, and message queuing

**Key Interfaces:**
- `POST /webhooks/whatsapp` - Receive WhatsApp webhooks
- `send_message(phone, content, template)` - Send WhatsApp messages
- `validate_webhook(token, challenge)` - Webhook verification
- `process_media(media_id)` - Handle WhatsApp media downloads

**Dependencies:** WhatsApp Cloud API, Message Queue (SQS), Supabase

**Technology Stack:** FastAPI, httpx for async HTTP, python-whatsapp-business SDK, boto3 for SQS

#### AI Processor Service
**Responsibility:** Handles all AI-powered conversation processing, sentiment analysis, and personality matching

**Key Interfaces:**
- `process_message(conversation_id, message)` - Process incoming message with AI
- `analyze_sentiment(text, language)` - Arabic-aware sentiment analysis
- `generate_response(context, personality)` - Generate contextual response
- `extract_intent(message)` - Identify user intent (feedback/order/support)

**Dependencies:** OpenRouter API, LangChain, Arabic NLP libraries (CAMeL Tools)

**Technology Stack:** FastAPI, LangChain, httpx, camel-tools, transformers

#### Core API Service
**Responsibility:** Central business logic, restaurant management, and orchestration

**Key Interfaces:**
- `REST /restaurants/*` - Restaurant CRUD operations
- `REST /branches/*` - Branch management
- `REST /conversations/*` - Conversation management
- `authenticate_user()` - JWT validation with Supabase

**Dependencies:** Supabase (PostgreSQL + Auth), Redis Cache

**Technology Stack:** FastAPI, SQLAlchemy, supabase-py, redis-py

#### Analytics Service
**Responsibility:** Real-time metrics processing, aggregation, and reporting

**Key Interfaces:**
- `calculate_metrics(restaurant_id, period)` - Generate dashboard metrics
- `process_feedback_analytics()` - Aggregate feedback sentiment
- `track_conversation_metrics()` - Response time, resolution rate
- `generate_reports()` - Scheduled report generation

**Dependencies:** Supabase, Pandas for data processing

**Technology Stack:** FastAPI, pandas, polars, apscheduler for cron jobs

#### Notification Service
**Responsibility:** Alert management, escalation handling, and owner notifications

**Key Interfaces:**
- `send_escalation_alert(conversation_id, reason)` - Alert staff
- `notify_negative_feedback(feedback_id)` - Urgent alerts
- `send_daily_summary()` - Scheduled summaries
- `manage_alert_preferences()` - Per-user notification settings

**Dependencies:** WhatsApp Gateway (for WhatsApp alerts), SMTP/SendGrid

**Technology Stack:** FastAPI, celery for async tasks, sendgrid SDK

### Frontend Components (TypeScript/Next.js)

#### Dashboard Shell
**Responsibility:** Main application layout, navigation, and authentication wrapper

**Key Interfaces:**
- `<AuthProvider>` - Supabase auth context
- `<NavigationMenu>` - Multi-branch navigation
- `<NotificationCenter>` - Real-time alerts
- `useRestaurant()` - Restaurant context hook

**Dependencies:** Supabase Auth, Zustand store

**Technology Stack:** Next.js App Router, Supabase JS Client, Zustand

#### Conversation Monitor
**Responsibility:** Real-time conversation viewing and intervention interface

**Key Interfaces:**
- `<ConversationList>` - Filterable conversation list
- `<ConversationView>` - Message thread display
- `<InterventionPanel>` - Manual message sending
- `useRealtimeConversations()` - WebSocket subscription hook

**Dependencies:** Supabase Realtime, Core API

**Technology Stack:** React, Supabase Realtime Client, Tanstack Query

#### Analytics Dashboard
**Responsibility:** Metrics visualization, trend analysis, and reporting

**Key Interfaces:**
- `<MetricsGrid>` - Key performance indicators
- `<SatisfactionChart>` - Rating trends
- `<BranchComparison>` - Multi-location analytics
- `<ReportGenerator>` - Export functionality

**Dependencies:** Analytics API, Chart libraries

**Technology Stack:** React, Recharts/Tremor, react-pdf for exports

### Component Interaction Diagram

```mermaid
graph TB
    subgraph "External"
        WA[WhatsApp Cloud API]
        OR[OpenRouter]
        CUSTOMER[WhatsApp Customer]
    end
    
    subgraph "Backend Services"
        WG[WhatsApp Gateway]
        AI[AI Processor]
        CORE[Core API]
        ANALYTICS[Analytics]
        NOTIFY[Notifications]
    end
    
    subgraph "Frontend Components"
        SHELL[Dashboard Shell]
        MONITOR[Conversation Monitor]
        DASH[Analytics Dashboard]
        SETTINGS[Settings Manager]
        ORDERS[Order Management]
    end
    
    subgraph "Data Layer"
        DB[(Supabase)]
        CACHE[(Redis)]
        QUEUE[SQS]
    end
    
    CUSTOMER --> WA
    WA --> WG
    WG --> QUEUE
    QUEUE --> AI
    AI --> OR
    AI --> DB
    
    SHELL --> CORE
    MONITOR --> DB
    MONITOR -.->|Realtime| DB
    DASH --> ANALYTICS
    SETTINGS --> CORE
    ORDERS --> CORE
    ORDERS -.->|Realtime| DB
    
    CORE --> DB
    CORE --> CACHE
    ANALYTICS --> DB
    NOTIFY --> WG
```

## External APIs

### OpenRouter API (LLM Gateway)
- **Purpose:** Unified access to multiple LLM providers for conversation processing and Arabic language understanding
- **Documentation:** https://openrouter.ai/docs
- **Base URL(s):** https://openrouter.ai/api/v1
- **Authentication:** Bearer token (API Key with "Bearer" prefix)
- **Rate Limits:** Depends on selected model and account tier

**Key Endpoints Used:**
- `POST /chat/completions` - Generate conversational responses with model selection
- `GET /models` - List available models and pricing
- `POST /generation` - Streaming responses for lower latency
- `GET /limits` - Check current usage and rate limits

**Model Selection Strategy:**
- **Primary:** `google/gemini-flash-1.5` - Fast, cost-effective for Arabic
- **Fallback 1:** `anthropic/claude-3-haiku` - High quality, good Arabic support
- **Fallback 2:** `meta-llama/llama-3.1-70b-instruct` - Open source option
- **Premium:** `openai/gpt-4-turbo` - For complex conversations requiring escalation

**Integration Notes:** 
- OpenRouter handles failover between providers automatically
- Supports custom routing rules based on cost/latency/quality preferences  
- Arabic-optimized prompt templates stored in configuration
- Context window varies by model (8k-128k tokens)
- Streaming responses reduce perceived latency for customers
- Usage tracking and cost optimization built into OpenRouter dashboard

### WhatsApp Business Cloud API
- **Purpose:** Core messaging platform for all customer interactions
- **Documentation:** https://developers.facebook.com/docs/whatsapp/cloud-api
- **Base URL(s):** https://graph.facebook.com/v19.0/{phone_number_id}
- **Authentication:** Bearer token (System User Access Token)
- **Rate Limits:** 80 messages/second (business initiated), 1000 messages/second (user initiated)

**Key Endpoints Used:**
- `POST /messages` - Send text, template, and interactive messages
- `POST /media/{media_id}` - Download received media files
- `GET /phone_numbers` - Verify business phone number status
- `POST /messages/templates` - Send template messages for initial contact

**Integration Notes:** Webhook verification required on setup. Must handle status callbacks for delivery confirmation. Prayer time awareness implemented in message scheduling layer.

### Supabase Platform APIs
- **Purpose:** Database, authentication, realtime subscriptions, and storage
- **Documentation:** https://supabase.com/docs/reference
- **Base URL(s):** https://{project_ref}.supabase.co
- **Authentication:** Service role key for backend, anon key for frontend
- **Rate Limits:** Based on plan (Free: 500 concurrent connections, Pro: 5000)

**Key Endpoints Used:**
- `POST /auth/v1/token` - User authentication
- `POST /rest/v1/{table}` - Database operations via PostgREST
- `WebSocket /realtime/v1/websocket` - Realtime subscriptions
- `POST /storage/v1/object/{bucket}` - Media file storage

**Integration Notes:** Row Level Security policies enforce multi-tenancy. Realtime requires heartbeat every 30 seconds. Edge Functions available for complex database triggers.

### Saudi Prayer Times API
- **Purpose:** Accurate prayer times for message scheduling
- **Documentation:** https://aladhan.com/prayer-times-api
- **Base URL(s):** https://api.aladhan.com/v1
- **Authentication:** None required (public API)
- **Rate Limits:** 14000 requests/day

**Key Endpoints Used:**
- `GET /timingsByCity` - Get prayer times by Saudi city
- `GET /hijriCalendarByCity` - Get Hijri calendar for Ramadan detection

**Integration Notes:** Cache prayer times daily per city. Add 10-minute buffer before and after prayer times. Special handling for Ramadan schedule adjustments.

### Integration Architecture with OpenRouter

```mermaid
graph LR
    subgraph "CRM-RES Platform"
        GW[WhatsApp Gateway]
        AI[AI Processor]
        CORE[Core API]
        SCHED[Scheduler]
    end
    
    subgraph "External APIs"
        OR[OpenRouter API]
        WA[WhatsApp Cloud API]
        PRAYER[Prayer Times API]
        MAPS[Google Maps]
        EMAIL[SendGrid]
        POS[POS Systems]
    end
    
    subgraph "LLM Providers via OpenRouter"
        GEMINI[Gemini Flash]
        CLAUDE[Claude Haiku]
        GPT[GPT-4 Turbo]
        LLAMA[Llama 3.1]
    end
    
    GW <--> WA
    AI <--> OR
    OR --> GEMINI
    OR --> CLAUDE
    OR --> GPT
    OR --> LLAMA
    SCHED --> PRAYER
    CORE --> MAPS
    CORE --> EMAIL
    CORE <--> POS
```

## Core Workflows

### Customer Feedback Collection Workflow

```mermaid
sequenceDiagram
    participant C as WhatsApp Customer
    participant WA as WhatsApp API
    participant GW as Gateway Service
    participant AI as AI Processor
    participant OR as OpenRouter
    participant DB as Supabase
    participant DASH as Dashboard
    participant O as Restaurant Owner

    Note over C,O: 2-4 hours after restaurant visit
    
    GW->>DB: Check recent orders/visits
    GW->>WA: Send feedback request template
    WA->>C: "مرحباً! كيف كانت تجربتك معنا اليوم؟"
    
    C->>WA: "الأكل كان لذيذ بس الخدمة بطيئة شوي"
    WA->>GW: Webhook: New message
    GW->>DB: Create/update conversation
    GW->>AI: Process message
    
    AI->>OR: Analyze sentiment & generate response
    OR->>AI: Sentiment: Mixed, Response generated
    AI->>DB: Store sentiment analysis
    
    alt Negative sentiment detected
        AI->>DB: Flag for escalation
        DB-->>DASH: Realtime update
        DASH->>O: Push notification alert
    end
    
    AI->>GW: Response ready
    GW->>WA: Send response
    WA->>C: "نعتذر عن التأخير. هل يمكنك تقييم تجربتك من 1-5؟"
    
    C->>WA: "3"
    WA->>GW: Webhook: Rating received
    GW->>DB: Store feedback & rating
    DB-->>DASH: Realtime metrics update
    
    GW->>WA: Send thank you + offer
    WA->>C: "شكراً لك! إليك كود خصم 15% للزيارة القادمة"
```

### Order Placement Workflow

```mermaid
sequenceDiagram
    participant C as WhatsApp Customer
    participant WA as WhatsApp API
    participant GW as Gateway Service
    participant AI as AI Processor
    participant OR as OpenRouter
    participant DB as Supabase
    participant POS as POS System
    participant B as Branch Staff
    
    C->>WA: "ابغى اطلب برجر مع بطاطس"
    WA->>GW: Webhook: Order intent
    GW->>AI: Process order request
    
    AI->>OR: Extract order items
    OR->>AI: Items: [Burger, Fries]
    
    AI->>DB: Get menu items & prices
    DB->>AI: Menu data
    
    AI->>GW: Confirm order details
    GW->>WA: Send order summary
    WA->>C: "طلبك: برجر (35 ريال) + بطاطس (12 ريال) = 47 ريال"
    WA->>C: "للتأكيد اكتب نعم"
    
    C->>WA: "نعم"
    WA->>GW: Confirmation received
    
    GW->>DB: Create order record
    GW->>POS: Forward order
    POS->>GW: Order ID: #1234
    
    DB-->>B: Realtime order notification
    
    GW->>WA: Send confirmation
    WA->>C: "تم استلام طلبك #1234"
    WA->>C: "وقت التحضير: 20 دقيقة"
```

### Prayer Time Aware Scheduling

```mermaid
sequenceDiagram
    participant SCHED as Scheduler
    participant PT as Prayer Times API
    participant DB as Supabase
    participant GW as Gateway Service
    participant WA as WhatsApp API
    participant C as Customer
    
    Note over SCHED: Daily at midnight
    
    SCHED->>PT: Get prayer times for all cities
    PT->>SCHED: Prayer schedule
    SCHED->>DB: Store prayer times
    
    loop Every 5 minutes
        SCHED->>DB: Check scheduled messages
        DB->>SCHED: Pending messages
        
        SCHED->>DB: Get current prayer status
        
        alt During prayer time
            SCHED->>SCHED: Hold messages
        else Outside prayer time
            SCHED->>GW: Process message queue
            GW->>WA: Send messages
            WA->>C: Deliver messages
        end
    end
    
    Note over SCHED: Special Ramadan handling
    
    alt Ramadan period
        SCHED->>DB: Apply Iftar/Suhoor schedule
        SCHED->>GW: Schedule pre-Iftar promotions
        GW->>WA: Send at optimal time
    end
```

## Database Schema

### PostgreSQL Schema Definition

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

### Indexing Strategy

1. **Primary Keys** - UUID for all tables (globally unique, no collisions)
2. **Foreign Keys** - Indexed automatically for joins
3. **Phone Numbers** - Indexed for fast customer lookup
4. **Timestamps** - DESC indexes for recent data queries
5. **Status Fields** - Indexed for filtering active/pending items
6. **Spatial Index** - PostGIS for location-based branch queries
7. **Text Search** - pg_trgm for Arabic text searching

## Frontend Architecture

### Component Architecture

#### Component Organization
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

### State Management Architecture

#### State Structure
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

### Routing Architecture

#### Route Organization
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

### Frontend Services Layer

#### API Client Setup
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

## Backend Architecture

### Service Architecture

#### Container Organization
```text
services/
├── whatsapp-gateway/
│   ├── src/
│   │   ├── api/               # FastAPI routes
│   │   ├── handlers/          # Webhook handlers
│   │   ├── services/          # Business logic
│   │   ├── models/            # Pydantic models
│   │   ├── utils/             # Utilities
│   │   └── main.py            # FastAPI app entry
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
├── ai-processor/
│   ├── src/
│   │   ├── api/               # FastAPI routes
│   │   ├── agents/            # LangChain agents
│   │   ├── chains/            # Processing chains
│   │   ├── prompts/           # Prompt templates
│   │   ├── models/            # Pydantic models
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── core-api/
│   ├── src/
│   │   ├── api/               # REST endpoints
│   │   ├── services/          # Business logic
│   │   ├── repositories/      # Data access layer
│   │   ├── models/            # Pydantic models
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
└── analytics-service/
    ├── src/
    │   ├── api/
    │   ├── processors/        # Data processors
    │   ├── aggregators/       # Metric aggregators
    │   └── main.py
    ├── Dockerfile
    └── requirements.txt
```

### Authentication and Authorization

#### Auth Flow with Supabase
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Bearer token security
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Validate JWT token and get user"""
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
```

### Container Configuration

#### Dockerfile for Python Services
```dockerfile
# Multi-stage build for Python service
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/

# Set Python path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Unified Project Structure

```text
crm-res/
├── .github/                    # CI/CD workflows
│   └── workflows/
│       ├── ci.yaml            # Build and test
│       ├── deploy-staging.yaml
│       └── deploy-prod.yaml
├── apps/                       # Application packages
│   ├── dashboard/             # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/           # App Router pages
│   │   │   ├── components/    # React components
│   │   │   ├── hooks/         # Custom hooks
│   │   │   ├── lib/           # Utilities
│   │   │   ├── stores/        # Zustand stores
│   │   │   └── types/         # TypeScript types
│   │   ├── public/            # Static assets
│   │   ├── tests/             # Frontend tests
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── next.config.js
├── services/                  # Python microservices
│   ├── whatsapp-gateway/
│   │   ├── src/
│   │   │   ├── api/           # FastAPI routes
│   │   │   ├── handlers/      # Webhook handlers
│   │   │   ├── services/      # Business logic
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── ai-processor/
│   │   ├── src/
│   │   │   ├── agents/        # LangChain agents
│   │   │   ├── chains/        # Processing chains
│   │   │   ├── prompts/       # Arabic prompts
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── core-api/
│   │   ├── src/
│   │   │   ├── api/           # REST endpoints
│   │   │   ├── repositories/  # Data access
│   │   │   ├── services/      # Business logic
│   │   │   └── main.py
│   │   └── Dockerfile
│   └── analytics-service/
│       ├── src/
│       └── Dockerfile
├── packages/                  # Shared packages
│   ├── shared-types/          # TypeScript/Python types
│   │   ├── typescript/        # .ts interfaces
│   │   ├── python/            # Pydantic models
│   │   └── package.json
│   └── ui-components/         # Shared React components
│       ├── src/
│       └── package.json
├── infrastructure/            # Infrastructure as Code
│   ├── pulumi/               # Pulumi Python IaC
│   │   ├── aws/              # AWS resources
│   │   ├── supabase/         # Supabase config
│   │   └── __main__.py
│   ├── docker/               # Docker configurations
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.prod.yml
│   │   └── .env.example
│   └── kubernetes/           # K8s manifests (future)
├── scripts/                  # Build/deploy scripts
│   ├── build.sh             # Build all services
│   ├── test.sh              # Run all tests
│   ├── deploy.sh            # Deploy to environment
│   └── setup-dev.sh         # Local development setup
├── docs/                     # Documentation
│   ├── prd.md
│   ├── architecture.md      # This document
│   ├── api-docs/           # API documentation
│   └── deployment/         # Deployment guides
├── tests/                   # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── load/              # Load testing
├── .env.example            # Environment template
├── package.json            # Root package.json (Turborepo)
├── turbo.json             # Turborepo configuration
├── docker-compose.yml     # Local development
└── README.md
```

## Development Workflow

### Local Development Setup

#### Prerequisites
```bash
# Install required tools
node --version  # v20+
python --version # 3.12+
docker --version # 24+
docker-compose --version

# Install global dependencies
npm install -g turbo@latest
pip install poetry
```

#### Initial Setup
```bash
# Clone and setup
git clone <repository-url>
cd crm-res

# Install dependencies
npm install              # Install Turborepo and frontend deps
turbo run build --filter=shared-types  # Build shared types first

# Setup Python services
cd services/whatsapp-gateway
pip install -r requirements.txt
cd ../ai-processor  
pip install -r requirements.txt
# Repeat for all services

# Copy environment variables
cp .env.example .env
# Fill in actual values for Supabase, OpenRouter, WhatsApp API
```

#### Development Commands
```bash
# Start all services (Docker Compose)
docker-compose up -d

# Start frontend only
turbo run dev --filter=dashboard

# Start specific backend service
cd services/whatsapp-gateway
uvicorn src.main:app --reload --port 8001

# Run tests
turbo run test           # All frontend tests
pytest services/*/tests  # All backend tests
playwright test         # E2E tests

# Build for production
turbo run build         # All services
docker-compose -f docker-compose.prod.yml build
```

### Environment Configuration

#### Required Environment Variables
```bash
# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend (.env)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
OPENROUTER_API_KEY=your-openrouter-key
WHATSAPP_ACCESS_TOKEN=your-whatsapp-token
WHATSAPP_VERIFY_TOKEN=your-webhook-verify-token
REDIS_URL=redis://localhost:6379

# Shared
DATABASE_URL=postgresql://user:pass@localhost:5432/crm_res
```

## Deployment Architecture

### Deployment Strategy

**Frontend Deployment:**
- **Platform:** Vercel (optimized for Next.js)
- **Build Command:** `turbo run build --filter=dashboard`
- **Output Directory:** `apps/dashboard/out`
- **CDN/Edge:** Vercel Edge Network with global distribution

**Backend Deployment:**
- **Platform:** AWS ECS Fargate with Application Load Balancer
- **Build Command:** Docker multi-stage builds
- **Deployment Method:** Blue-green deployment via ECS service updates

### Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|-------------|-------------|---------|
| Development | http://localhost:3000 | http://localhost:8000 | Local development |
| Staging | https://staging.crm-res.com | https://api-staging.crm-res.com | Pre-production testing |
| Production | https://app.crm-res.com | https://api.crm-res.com | Live environment |

## Security and Performance

### Security Requirements

**Frontend Security:**
- CSP Headers: `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'`
- XSS Prevention: React's built-in escaping + Content Security Policy
- Secure Storage: Supabase handles JWT tokens securely, sensitive data in httpOnly cookies

**Backend Security:**
- Input Validation: Pydantic models with strict validation
- Rate Limiting: 1000 requests/hour per restaurant (configurable by tier)
- CORS Policy: Restricted to known frontend domains only

**Authentication Security:**
- Token Storage: JWTs in httpOnly cookies, refresh tokens in secure storage
- Session Management: Supabase Auth with automatic token refresh
- Password Policy: Enforced by Supabase (min 8 chars, complexity requirements)

### Performance Optimization

**Frontend Performance:**
- Bundle Size Target: <250KB initial JS bundle
- Loading Strategy: Route-based code splitting with Next.js
- Caching Strategy: Static assets cached 1 year, API responses 5 minutes

**Backend Performance:**
- Response Time Target: <200ms for 95% of API calls
- Database Optimization: Proper indexing, query optimization, connection pooling
- Caching Strategy: Redis for conversation state, PostgreSQL query cache

## Testing Strategy

### Testing Pyramid

```text
       E2E Tests (10%)
      /              \
   Integration Tests (20%)
   /                      \
Frontend Unit (35%)  Backend Unit (35%)
```

### Test Organization

#### Frontend Tests
```text
apps/dashboard/tests/
├── components/          # Component unit tests
├── hooks/              # Custom hook tests  
├── pages/              # Page integration tests
├── e2e/                # Playwright E2E tests
└── setup.ts            # Test configuration
```

#### Backend Tests
```text
services/*/tests/
├── unit/               # Unit tests
├── integration/        # API integration tests
├── fixtures/           # Test data
└── conftest.py         # Pytest configuration
```

## Coding Standards

### Critical Fullstack Rules
- **Type Sharing:** Always define types in packages/shared-types and import from there
- **API Calls:** Never make direct HTTP calls - use the service layer  
- **Environment Variables:** Access only through config objects, never process.env directly
- **Error Handling:** All API routes must use the standard error handler
- **State Updates:** Never mutate state directly - use proper state management patterns

### Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| Components | PascalCase | - | `UserProfile.tsx` |
| Hooks | camelCase with 'use' | - | `useAuth.ts` |
| API Routes | - | kebab-case | `/api/user-profile` |
| Database Tables | - | snake_case | `user_profiles` |

## Error Handling Strategy

### Error Response Format

```typescript
interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    timestamp: string;
    requestId: string;
  };
}
```

### Frontend Error Handling
```typescript
// Global error boundary for React components
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Send to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

### Backend Error Handling
```python
# Global exception handler for FastAPI
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        }
    )
```

## Monitoring and Observability

### Monitoring Stack
- **Frontend Monitoring:** Vercel Analytics + Sentry
- **Backend Monitoring:** DataDog APM + CloudWatch
- **Error Tracking:** Sentry for both frontend and backend
- **Performance Monitoring:** DataDog Real User Monitoring

### Key Metrics

**Frontend Metrics:**
- Core Web Vitals
- JavaScript errors
- API response times
- User interactions

**Backend Metrics:**
- Request rate
- Error rate
- Response time
- Database query performance

---

## Summary

This comprehensive fullstack architecture document provides the foundation for building CRM-RES, a culturally-intelligent WhatsApp automation platform for Saudi restaurants. The hybrid approach combines:

- **Python FastAPI microservices** for AI processing and Arabic language capabilities
- **Next.js TypeScript frontend** for a modern, responsive dashboard
- **Supabase** for managed PostgreSQL, authentication, and real-time features
- **OpenRouter** for flexible LLM access with cost optimization
- **Containerized deployment** on AWS ECS Fargate for scalability

The architecture supports the core requirements of sub-30 second response times, 100,000 concurrent conversations, prayer-time awareness, and progressive automation from feedback collection to full ordering capabilities.

All components are designed for AI-driven development with clear interfaces, comprehensive testing strategies, and production-ready deployment configurations.