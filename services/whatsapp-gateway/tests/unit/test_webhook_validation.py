import pytest
import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.main import app
from src.utils.security import verify_webhook_signature

client = TestClient(app)

def test_webhook_verification_success():
    with patch('src.api.webhook.config.WHATSAPP_VERIFY_TOKEN', 'test_token'):
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_token",
                "hub.challenge": "challenge_123"
            }
        )
        assert response.status_code == 200
        assert response.text == "challenge_123"

def test_webhook_verification_invalid_token():
    with patch('src.api.webhook.config.WHATSAPP_VERIFY_TOKEN', 'test_token'):
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_123"
            }
        )
        assert response.status_code == 403

def test_webhook_verification_invalid_mode():
    with patch('src.api.webhook.config.WHATSAPP_VERIFY_TOKEN', 'test_token'):
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "unsubscribe",
                "hub.verify_token": "test_token",
                "hub.challenge": "challenge_123"
            }
        )
        assert response.status_code == 403

def test_verify_webhook_signature_valid():
    secret = "test_secret"
    payload = b'{"test": "data"}'
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    signature = f"sha256={expected_signature}"
    
    assert verify_webhook_signature(payload, signature, secret) is True

def test_verify_webhook_signature_invalid():
    secret = "test_secret"
    payload = b'{"test": "data"}'
    signature = "sha256=invalid_signature"
    
    assert verify_webhook_signature(payload, signature, secret) is False

def test_verify_webhook_signature_none():
    assert verify_webhook_signature(b'test', None, "secret") is False
    assert verify_webhook_signature(b'test', "signature", "") is False

def test_webhook_post_with_valid_signature():
    secret = "test_secret"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "123456"}
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
        response = client.post(
            "/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "received"}

def test_webhook_post_with_invalid_signature():
    with patch('src.api.webhook.config.WHATSAPP_WEBHOOK_SECRET', 'test_secret'):
        payload = {
            "object": "whatsapp_business_account",
            "entry": []
        }
        response = client.post(
            "/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=invalid"}
        )
        assert response.status_code == 401