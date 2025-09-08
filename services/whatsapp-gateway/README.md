# WhatsApp Gateway Service

Service for handling WhatsApp Business API integration for the CRM-RES platform.

## Features

- ✅ Webhook endpoint with signature validation
- ✅ Asynchronous message processing with Celery/Redis
- ✅ Basic echo response system (temporary)
- ✅ Outbound message sending with templates
- ✅ Rate limiting (80 msg/sec business, 1000 msg/sec user)
- ✅ Exponential backoff and circuit breaker patterns
- ✅ Database integration for message tracking
- ✅ Structured logging with correlation IDs

## Phone Number Provisioning Process

### Prerequisites
1. Facebook Business Manager account
2. WhatsApp Business API access approved
3. Verified business entity

### Step-by-Step Process

#### 1. Access Meta Business Suite
- Go to https://business.facebook.com
- Select your business account
- Navigate to WhatsApp Manager

#### 2. Add Phone Number
- Click "Add phone number"
- Enter the restaurant's phone number
- Verify via SMS or voice call
- Complete 2-factor authentication setup

#### 3. Configure Webhook
- In WhatsApp Manager, go to Configuration
- Set webhook URL: `https://your-domain.com/webhook`
- Set verify token (must match WHATSAPP_VERIFY_TOKEN)
- Subscribe to messages and message_status fields

#### 4. Generate Access Token
- Go to System Users in Business Settings
- Create new system user with admin role
- Generate system user access token
- Grant whatsapp_business_messaging and whatsapp_business_management permissions

#### 5. Get Phone Number ID
- In WhatsApp Manager, select the phone number
- Copy the Phone Number ID from the API settings
- This will be used as WHATSAPP_PHONE_NUMBER_ID

#### 6. Configure Environment
- Copy `.env.example` to `.env`
- Fill in all WhatsApp configuration values:
  - WHATSAPP_WEBHOOK_SECRET (from webhook config)
  - WHATSAPP_VERIFY_TOKEN (your chosen token)
  - WHATSAPP_ACCESS_TOKEN (system user token)
  - WHATSAPP_PHONE_NUMBER_ID (from step 5)

#### 7. Test Connection
- Send test message via API
- Verify webhook receives messages
- Check message delivery status updates

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Run Redis (required for queue and rate limiting)
docker run -d -p 6379:6379 redis:latest

# Start Celery worker
celery -A src.services.queue worker --loglevel=info

# Start the service
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Docker Deployment

```bash
# Build the image
docker build -t whatsapp-gateway .

# Run the container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name whatsapp-gateway \
  whatsapp-gateway
```

## API Endpoints

### Health Check
```
GET /health
```

### Webhook Verification
```
GET /webhook?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE
```

### Webhook Handler
```
POST /webhook
Headers: X-Hub-Signature-256
Body: WhatsApp webhook payload
```

### Queue Health
```
GET /monitoring/queue/health
```

### Rate Limit Stats
```
GET /rate-limit/stats/{phone_number}
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_webhook_validation.py -v
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| WHATSAPP_WEBHOOK_SECRET | Secret for webhook signature validation | Yes |
| WHATSAPP_VERIFY_TOKEN | Token for webhook verification | Yes |
| WHATSAPP_ACCESS_TOKEN | System user access token | Yes |
| WHATSAPP_PHONE_NUMBER_ID | WhatsApp phone number ID | Yes |
| WHATSAPP_API_VERSION | API version (default: v19.0) | No |
| REDIS_URL | Redis connection URL | Yes |
| SUPABASE_URL | Supabase project URL | Yes |
| SUPABASE_ANON_KEY | Supabase anonymous key | Yes |
| LOG_LEVEL | Logging level (default: INFO) | No |

## Monitoring

The service provides several monitoring endpoints:

- `/health` - Basic health check
- `/monitoring/queue/health` - Celery queue status
- `/rate-limit/health` - Rate limiter status
- `/rate-limit/stats/{phone}` - Per-number rate limit usage

## Rate Limits

- Business-initiated messages: 80 messages/second
- User-initiated messages: 1000 messages/second
- Window: 1 second sliding window
- Backed by Redis for distributed rate limiting

## Error Handling

- Exponential backoff with jitter for retries
- Circuit breaker pattern for external API calls
- Structured logging with correlation IDs
- Dead letter queue for failed messages
- All errors logged to database for analysis

## Security

- HMAC SHA-256 webhook signature validation
- Environment-based configuration (no hardcoded secrets)
- Non-root Docker user
- CORS middleware configured
- Rate limiting to prevent abuse