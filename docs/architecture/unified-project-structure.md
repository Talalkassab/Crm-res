# Unified Project Structure

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
