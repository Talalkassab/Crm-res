# Technical Assumptions

## Repository Structure: Monorepo
Utilizing a monorepo structure to maintain all platform components (frontend dashboard, backend services, AI processors, WhatsApp integrations) in a single repository. This enables atomic commits across the full stack, simplified dependency management, and consistent deployment workflows. Packages will be organized as: `/apps/dashboard`, `/apps/api`, `/services/ai`, `/services/whatsapp`, `/packages/shared`.

## Service Architecture
**Microservices within Monorepo** - The platform will use containerized microservices for separation of concerns while maintaining monorepo benefits:
- **WhatsApp Gateway Service** - Handles all WhatsApp API interactions, message queuing, rate limiting
- **AI Processing Service** - Manages Gemini Flash conversations, sentiment analysis, personality matching  
- **Analytics Service** - Real-time metrics processing, dashboard data aggregation
- **Core API** - Restaurant management, branch routing, user authentication
- **Notification Service** - Alert escalation, owner notifications, monitoring
All services communicate through event-driven architecture using message queues for resilience.

## Testing Requirements
**Full Testing Pyramid with Arabic Language Coverage**:
- **Unit Tests** - 80% code coverage for business logic, Arabic text processing validation
- **Integration Tests** - API endpoint testing, WhatsApp webhook simulation, database transactions
- **E2E Tests** - Critical user journeys including Arabic conversation flows
- **Manual Testing Convenience** - Debug dashboard for conversation replay, test phone number provisioning
- **Performance Tests** - Load testing for 100K concurrent conversations, Arabic NLP processing speed

## Additional Technical Assumptions and Requests
- **Frontend Framework:** Next.js 14+ with App Router for dashboard, React Server Components for performance
- **Styling:** Tailwind CSS with RTL support, Shadcn/ui component library for consistency
- **Backend Language:** Python FastAPI for AI services (better ML library support), Node.js/TypeScript for real-time operations
- **Database:** Supabase (PostgreSQL with real-time subscriptions) for primary data, Redis for caching and session management
- **AI/ML Stack:** Gemini Flash 2.0 for conversations, OpenAI embeddings for semantic search, Langchain for conversation management
- **Message Queue:** BullMQ for reliable job processing and WhatsApp message queuing
- **Hosting:** Vercel for frontend, Railway for backend services, Cloudflare R2 for media storage
- **Monitoring:** Sentry for error tracking, PostHog for product analytics, custom Arabic conversation quality metrics
- **Authentication:** Supabase Auth with WhatsApp number verification for restaurant owners
- **API Design:** RESTful APIs with OpenAPI documentation, GraphQL for complex dashboard queries
- **Development Tools:** Turborepo for monorepo management, Docker for local development environment
- **CI/CD:** GitHub Actions for testing and deployment, preview environments for each PR
- **Security:** JWT tokens with refresh rotation, API rate limiting per restaurant, webhook signature verification
