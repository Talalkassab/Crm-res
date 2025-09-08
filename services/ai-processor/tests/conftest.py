import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from main import app

# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)

@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response."""
    return {
        "id": "test-response-id",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "google/gemini-flash-1.5",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "مرحباً! كيف يمكنني مساعدتك اليوم؟"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70
        }
    }

@pytest.fixture
def sample_arabic_messages():
    """Sample Arabic messages for testing."""
    return {
        "saudi_positive": "هلا والله! الأكل كان ممتاز والخدمة رائعة، ما شاء الله عليكم",
        "saudi_negative": "والله الطعم مش طيب وكان في انتظار كثير",
        "egyptian_positive": "الأكل كان جامد أوي والناس لطاف خالص، ربنا يخليكم",
        "egyptian_negative": "الأكل مش حلو خالص والخدمة بطيئة جداً",
        "complaint": "عندي شكوى على الطعام، كان بارد ومالح كثير",
        "compliment": "بارك الله فيكم، الطعام لذيذ جداً والضيافة ممتازة"
    }

@pytest.fixture
def sample_ai_processing_request():
    """Sample AI processing request."""
    return {
        "message": "هلا والله! وش عندكم اليوم من أكل طيب؟",
        "conversation_id": "test-conversation-123",
        "customer_id": "test-customer-456",
        "context": {
            "restaurant_id": "test-restaurant-789",
            "language_preference": "ar-SA"
        }
    }

# Pytest markers
pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "arabic: mark test as Arabic language specific")