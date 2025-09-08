# Backend Architecture

## Service Architecture

### Container Organization
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

## Authentication and Authorization

### Auth Flow with Supabase
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

## Container Configuration

### Dockerfile for Python Services
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
