import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.whatsapp_client import WhatsAppClient

@pytest.mark.asyncio
async def test_send_text_message_success():
    client = WhatsAppClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "messages": [{"id": "msg_sent_123"}]
    }
    
    with patch('src.services.whatsapp_client.rate_limiter_instance.wait_if_needed', new_callable=AsyncMock):
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await client.send_text_message("1234567890", "Test message")
            
            assert result["success"] is True
            assert result["message_id"] == "msg_sent_123"
            assert result["to"] == "1234567890"

@pytest.mark.asyncio
async def test_send_text_message_failure():
    client = WhatsAppClient()
    
    with patch('src.services.whatsapp_client.rate_limiter_instance.wait_if_needed', new_callable=AsyncMock):
        with patch.object(client.client, 'post', new_callable=AsyncMock, side_effect=Exception("Network error")):
            with patch('src.services.whatsapp_client.webhook_circuit_breaker.call', new_callable=AsyncMock, side_effect=Exception("Network error")):
                result = await client.send_text_message("1234567890", "Test message")
                
                assert result["success"] is False
                assert "Network error" in result["error"]

@pytest.mark.asyncio
async def test_send_template_message():
    client = WhatsAppClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "messages": [{"id": "template_123"}]
    }
    
    with patch('src.services.whatsapp_client.rate_limiter_instance.wait_if_needed', new_callable=AsyncMock):
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await client.send_template_message(
                to="1234567890",
                template_name="feedback_request",
                language_code="en",
                components=[{"type": "body", "parameters": []}]
            )
            
            assert result["success"] is True
            assert result["message_id"] == "template_123"
            assert result["template"] == "feedback_request"

@pytest.mark.asyncio
async def test_send_feedback_request():
    client = WhatsAppClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "messages": [{"id": "feedback_123"}]
    }
    
    with patch('src.services.whatsapp_client.rate_limiter_instance.wait_if_needed', new_callable=AsyncMock):
        with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await client.send_feedback_request(
                to="1234567890",
                restaurant_name="Test Restaurant",
                order_id="ORDER123"
            )
            
            assert result["success"] is True
            assert result["message_id"] == "feedback_123"

@pytest.mark.asyncio
async def test_mark_message_as_read():
    client = WhatsAppClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(client.client, 'post', new_callable=AsyncMock, return_value=mock_response):
        result = await client.mark_message_as_read("msg_123")
        
        assert result["success"] is True
        assert result["message_id"] == "msg_123"

@pytest.mark.asyncio
async def test_get_media_url():
    client = WhatsAppClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "url": "https://example.com/media/123"
    }
    
    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response):
        url = await client.get_media_url("media_123")
        
        assert url == "https://example.com/media/123"

@pytest.mark.asyncio
async def test_download_media():
    client = WhatsAppClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b"media_content"
    
    with patch.object(client.client, 'get', new_callable=AsyncMock, return_value=mock_response):
        content = await client.download_media("https://example.com/media/123")
        
        assert content == b"media_content"