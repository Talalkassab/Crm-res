# High Level Architecture

## Technical Summary

The CRM-RES platform employs a containerized microservices architecture orchestrated on AWS ECS Fargate, utilizing Next.js for the restaurant dashboard and Python microservices in Docker containers for backend services. The system integrates directly with WhatsApp Cloud API for messaging, OpenRouter for AI-powered conversations, and maintains real-time state through Supabase (PostgreSQL) with realtime subscriptions for service orchestration. This architecture achieves sub-30 second response times through Application Load Balancer with CloudFront distribution, while supporting 100,000 concurrent conversations through auto-scaling container tasks and service mesh communication.

## Platform and Infrastructure Choice

**Platform:** AWS with Container Orchestration  
**Key Services:** ECS Fargate, ECR, ALB, Supabase, EventBridge, SQS, CloudFront, Cognito  
**Deployment Regions:** Primary: me-south-1 (Bahrain), Secondary: eu-west-1 (Ireland)  
**Container Orchestration:** ECS Fargate (serverless containers without managing EC2 instances)  
**Service Mesh:** AWS App Mesh for inter-service communication and observability

## Repository Structure

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

## High Level Architecture Diagram

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

## Architectural Patterns

- **Containerized Microservices:** Docker containers on ECS Fargate for consistent deployment and local development parity - *Rationale:* Ensures "works on my machine" equals production behavior
- **Service Mesh Pattern:** AWS App Mesh for service discovery, load balancing, and observability - *Rationale:* Simplifies inter-service communication and provides detailed metrics
- **Event-Driven Architecture:** EventBridge for service decoupling and async processing - *Rationale:* Enables real-time message processing without tight coupling
- **Sidecar Pattern:** Envoy proxy sidecars for service mesh communication - *Rationale:* Handles retries, circuit breaking, and distributed tracing transparently
- **Repository Pattern:** Abstract database access for testability - *Rationale:* Enables database migration flexibility
- **API Gateway Pattern:** ALB with path-based routing to different services - *Rationale:* Centralized entry point with health checks and auto-scaling
- **Circuit Breaker Pattern:** Built into service mesh for resilient external API calls - *Rationale:* Prevents cascade failures automatically
- **Blue-Green Deployment:** ECS service updates with automated rollback - *Rationale:* Zero-downtime deployments with instant rollback capability
