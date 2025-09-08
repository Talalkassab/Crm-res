# Development Workflow

## Local Development Setup

### Prerequisites
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

### Initial Setup
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

### Development Commands
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

## Environment Configuration

### Required Environment Variables
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
