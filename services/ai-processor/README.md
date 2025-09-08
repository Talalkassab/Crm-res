# CRM-RES AI Processor Service

AI processing service for WhatsApp customer conversations with Arabic language support, cultural awareness, and prayer time intelligence.

## Features

- 🤖 **Gemini Flash 2.0 Integration** via OpenRouter API with model fallback
- 🇸🇦 **Arabic Language Support** with dialect detection (Saudi, Egyptian, Levantine)
- 🕌 **Prayer Time Intelligence** with automatic message scheduling
- 📊 **Sentiment Analysis** with escalation triggers for negative feedback
- 💬 **Conversation Context Management** for coherent multi-turn dialogues
- 🎭 **Personality Types** (Formal, Casual, Traditional, Modern)
- 📈 **Real-time Analytics** and performance monitoring

## Quick Start

### Prerequisites

- Python 3.12+
- OpenRouter API key
- Redis (for caching) - Optional
- PostgreSQL (for persistence) - Optional

### Installation

```bash
# Clone the repository
cd services/ai-processor

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### Required Configuration

Set your OpenRouter API key in `.env`:

```env
OPENROUTER_API_KEY=your-api-key-here
```

### Running the Service

```bash
# Development mode
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Production mode
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### Using Docker

```bash
# Build image
docker build -t crm-res-ai-processor .

# Run container
docker run -p 8001:8001 --env-file .env crm-res-ai-processor
```

## API Documentation

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "service": "ai-processor"
}
```

### Process Message

```bash
POST /api/process-message
```

Request:
```json
{
  "message": "هلا والله! وش عندكم اليوم من أكل طيب؟",
  "conversation_id": "conv-123",
  "customer_id": "cust-456",
  "context": {
    "restaurant_id": "rest-789",
    "language_preference": "ar-SA"
  }
}
```

Response:
```json
{
  "response": "هلا والله! نورت المطعم. عندنا اليوم طبخات سعودية أصيلة وطازجة",
  "sentiment": "positive",
  "confidence": 0.85,
  "suggested_actions": ["acknowledge_cultural_phrases"],
  "is_prayer_time": false,
  "should_escalate": false,
  "dialect_detected": "ar-SA",
  "cultural_phrases_used": ["هلا والله"]
}
```

### Prayer Time Status

```bash
GET /api/prayer-status?city=Riyadh
```

Response:
```json
{
  "is_prayer_time": false,
  "current_prayer": null,
  "next_prayer": {
    "prayer": "Dhuhr",
    "time": "12:30",
    "minutes_until": 45
  }
}
```

### Available Models

```bash
GET /api/models
```

### Switch Model

```bash
POST /api/switch-model
{
  "model_name": "anthropic/claude-3-haiku"
}
```

## Architecture

### Service Components

```
src/
├── agents/                 # AI agents and processors
│   ├── message_processor.py    # Main message processing orchestrator
│   └── conversation_agent.py   # Conversation context management
├── services/               # External service integrations
│   ├── openrouter_service.py   # OpenRouter API client
│   ├── sentiment_analyzer.py   # Arabic sentiment analysis
│   ├── prayer_time_service.py  # Prayer times API integration
│   └── arabic_processor.py     # Arabic text processing & dialect detection
├── prompts/                # System prompts and templates
│   └── arabic_prompts.py       # Arabic-optimized prompt management
├── models/                 # Database models and persistence
│   └── database.py            # Database operations
├── utils/                  # Utilities and configuration
│   ├── config.py              # Configuration management
│   └── cache.py               # Caching utilities
├── schemas.py              # Pydantic schemas
└── main.py                # FastAPI application
```

### Processing Flow

1. **Input Validation** - Validate incoming message request
2. **Prayer Time Check** - Check if message should be delayed
3. **Arabic Processing** - Detect dialect and cultural phrases
4. **Sentiment Analysis** - Analyze message sentiment and escalation needs
5. **Context Retrieval** - Get conversation history and context
6. **Prompt Generation** - Build culturally-aware system prompt
7. **AI Response** - Generate response via OpenRouter/Gemini Flash
8. **Cultural Formatting** - Format response with cultural awareness
9. **Context Update** - Update conversation context and history
10. **Response Delivery** - Return processed response with metadata

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key | - | Yes |
| `PRIMARY_AI_MODEL` | Primary AI model to use | `google/gemini-flash-1.5` | No |
| `AI_PROCESSOR_PORT` | Service port | `8001` | No |
| `PRAYER_BUFFER_MINUTES` | Prayer time buffer | `10` | No |
| `SENTIMENT_CONFIDENCE_THRESHOLD` | Sentiment confidence threshold | `0.7` | No |
| `ESCALATION_THRESHOLD` | Escalation threshold | `0.8` | No |

### Model Configuration

Supported AI models (with fallback):

1. **Primary**: `google/gemini-flash-1.5` - Fast, cost-effective for Arabic
2. **Fallback**: `anthropic/claude-3-haiku-20240307` - High quality backup
3. **Fallback**: `meta-llama/llama-3.1-70b-instruct` - Open source option

### Arabic Dialect Support

- **Saudi (ar-SA)**: Default dialect with local expressions
- **Egyptian (ar-EG)**: Egyptian dialect recognition and responses  
- **Levantine (ar-LV)**: Syrian/Lebanese/Palestinian variations
- **English (en)**: English with cultural awareness

### Personality Types

- **Formal**: Professional and respectful tone
- **Casual**: Friendly and approachable tone
- **Traditional**: Conservative with traditional values emphasis
- **Modern**: Contemporary and progressive tone

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m arabic           # Arabic-specific tests
pytest -m prayer_times     # Prayer time tests
pytest -m sentiment        # Sentiment analysis tests

# Run with coverage
pytest --cov=src --cov-report=html
```

### Test Structure

```
tests/
├── conftest.py                    # Test configuration and fixtures
├── unit/                          # Unit tests
│   ├── test_openrouter_client.py
│   ├── test_arabic_prompts.py
│   ├── test_sentiment_analysis.py
│   └── test_prayer_times.py
└── integration/                   # Integration tests
    └── test_message_processing.py
```

## Cultural Considerations

### Islamic Awareness

- **Prayer Times**: Automatic detection and message delays during prayers
- **Ramadan Support**: Special handling during Ramadan month
- **Religious Phrases**: Proper responses to Islamic greetings and phrases
- **Halal Compliance**: No references to non-halal items

### Cultural Phrases Handling

| Customer Input | AI Response |
|----------------|-------------|
| "السلام عليكم" | "وعليكم السلام ورحمة الله وبركاته" |
| "بارك الله فيك" | "وفيك بارك الله" |
| "جزاك الله خير" | "وإياك، أهلاً وسهلاً" |
| "إن شاء الله" | Incorporated naturally in responses |

### Dialect-Specific Responses

**Saudi Dialect Example:**
```
Customer: "وش رايك في الطعام؟"
AI: "والله الطعام طيب وطازج، ما شاء الله عليكم"
```

**Egyptian Dialect Example:**
```
Customer: "الأكل ايه النهارده؟"
AI: "النهارده عندنا أكل مصري أصيل وجامد أوي"
```

## Monitoring and Analytics

### Key Metrics

- **Response Time**: Average AI processing time
- **Sentiment Distribution**: Positive/Neutral/Negative ratios
- **Escalation Rate**: Percentage of conversations escalated
- **Dialect Accuracy**: Dialect detection success rate
- **Cultural Sensitivity**: Cultural phrase handling success
- **Prayer Time Compliance**: Messages properly delayed during prayers

### Health Checks

The service provides comprehensive health checks:

- OpenRouter API connectivity
- Prayer Times API availability
- Arabic processing functionality
- Sentiment analysis accuracy
- Cache and database connectivity

## Troubleshooting

### Common Issues

**OpenRouter API Errors:**
```bash
# Check API key
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models
```

**Prayer Times API Errors:**
```bash
# Test prayer times endpoint
curl "https://api.aladhan.com/v1/timingsByCity?city=Riyadh&country=Saudi Arabia"
```

**Arabic Text Issues:**
- Ensure UTF-8 encoding
- Check for proper Arabic character support
- Verify dialect detection accuracy

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python -m uvicorn src.main:app
```

## Contributing

1. Follow Arabic language testing guidelines
2. Test cultural sensitivity thoroughly
3. Validate prayer time handling
4. Ensure proper dialect detection
5. Maintain 80%+ test coverage for AI processing logic

## License

Part of the CRM-RES project. See main project LICENSE for details.