import pytest
import asyncio
from typing import Generator
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_supabase():
    with patch('src.services.database.create_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_redis():
    with patch('redis.from_url') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_httpx():
    with patch('httpx.AsyncClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

@pytest.fixture
def sample_text_message():
    return {
        'from': '1234567890',
        'id': 'msg_123',
        'timestamp': '1234567890',
        'type': 'text',
        'text': {'body': 'Hello, world!'}
    }

@pytest.fixture
def sample_media_message():
    return {
        'from': '0987654321',
        'id': 'msg_456',
        'timestamp': '1234567890',
        'type': 'image',
        'image': {
            'id': 'media_123',
            'mime_type': 'image/jpeg',
            'sha256': 'abc123',
            'caption': 'Test image'
        }
    }

@pytest.fixture
def sample_status_update():
    return {
        'id': 'msg_789',
        'status': 'delivered',
        'timestamp': '1234567890',
        'recipient_id': '1234567890'
    }

@pytest.fixture
def sample_webhook_payload():
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "123456"},
                    "messages": [{
                        'from': '1234567890',
                        'id': 'msg_123',
                        'timestamp': '1234567890',
                        'type': 'text',
                        'text': {'body': 'Hello!'}
                    }]
                }
            }]
        }]
    }