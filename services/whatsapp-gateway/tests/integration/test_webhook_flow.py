import pytest
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_complete_message_flow(sample_webhook_payload, mock_supabase):
    secret = "test_secret"
    
    payload_bytes = json.dumps(sample_webhook_payload).encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    with patch('src.api.webhook.config.WHATSAPP_WEBHOOK_SECRET', secret):
        with patch('src.api.webhook.process_incoming_message.delay') as mock_queue:
            response = client.post(
                "/webhook",
                json=sample_webhook_payload,
                headers={"X-Hub-Signature-256": f"sha256={signature}"}
            )
            
            assert response.status_code == 200
            assert response.json() == {"status": "received"}
            
            mock_queue.assert_called_once()
            args = mock_queue.call_args[0][0]
            assert args['from'] == '1234567890'
            assert args['type'] == 'text'

@pytest.mark.asyncio
async def test_status_update_flow(mock_supabase):
    secret = "test_secret"
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "123456"},
                    "statuses": [{
                        'id': 'msg_123',
                        'status': 'delivered',
                        'timestamp': '1234567890',
                        'recipient_id': '9876543210'
                    }]
                }
            }]
        }]
    }
    
    payload_bytes = json.dumps(payload).encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    with patch('src.api.webhook.config.WHATSAPP_WEBHOOK_SECRET', secret):
        with patch('src.api.webhook.process_status_update.delay') as mock_queue:
            response = client.post(
                "/webhook",
                json=payload,
                headers={"X-Hub-Signature-256": f"sha256={signature}"}
            )
            
            assert response.status_code == 200
            mock_queue.assert_called_once()

def test_webhook_verification():
    with patch('src.api.webhook.config.WHATSAPP_VERIFY_TOKEN', 'verify_token'):
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "verify_token",
                "hub.challenge": "challenge_value"
            }
        )
        
        assert response.status_code == 200
        assert response.text == "challenge_value"

def test_rate_limiting_middleware():
    with patch('src.middleware.rate_limiter.RateLimiter.check_rate_limit') as mock_check:
        mock_check.return_value = (False, 100)
        
        response = client.post(
            "/webhook",
            json={"test": "data"}
        )
        
        assert response.status_code == 429

def test_queue_health_endpoint():
    with patch('src.services.queue.celery_app.control.inspect') as mock_inspect:
        mock_instance = MagicMock()
        mock_instance.stats.return_value = {'worker1': {'status': 'ok'}}
        mock_instance.active.return_value = {'worker1': []}
        mock_instance.reserved.return_value = {'worker1': []}
        mock_inspect.return_value = mock_instance
        
        response = client.get("/monitoring/queue/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'

def test_rate_limit_stats_endpoint():
    with patch('src.middleware.rate_limiter.rate_limiter_instance.get_usage_stats') as mock_stats:
        mock_stats.return_value = {
            "business": {"current": 50, "limit": 80, "remaining": 30},
            "user": {"current": 100, "limit": 1000, "remaining": 900}
        }
        
        response = client.get("/rate-limit/stats/1234567890")
        
        assert response.status_code == 200
        data = response.json()
        assert data['business']['current'] == 50
        assert data['user']['remaining'] == 900