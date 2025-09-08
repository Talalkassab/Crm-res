# Tech Stack

This is the **DEFINITIVE** technology selection for the entire CRM-RES platform. All development must use these exact versions.

## Technology Stack Table

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
