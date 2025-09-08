import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from src.services.openrouter_service import OpenRouterService
from src.utils.config import AIProcessorConfig

@pytest.mark.unit
@pytest.mark.openrouter
class TestOpenRouterService:
    """Test suite for OpenRouter service."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return AIProcessorConfig(
            openrouter_api_key="test-api-key",
            openrouter_base_url="https://openrouter.ai/api/v1",
            primary_model="google/gemini-flash-1.5"
        )
    
    @pytest.fixture
    def openrouter_service(self, mock_config):
        """Create OpenRouter service instance."""
        with patch('src.services.openrouter_service.get_config', return_value=mock_config):
            return OpenRouterService()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, openrouter_service, mock_openrouter_response):
        """Test successful response generation."""
        with patch.object(openrouter_service, '_make_request_with_fallback') as mock_request:
            mock_request.return_value = mock_openrouter_response
            
            response = await openrouter_service.generate_response(
                message="مرحبا",
                context={"personality": "formal"},
                sentiment="neutral",
                language="ar"
            )
            
            assert response == "مرحباً! كيف يمكنني مساعدتك اليوم؟"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, openrouter_service, mock_openrouter_response):
        """Test response generation with conversation context."""
        conversation_history = [
            {"role": "user", "content": "السلام عليكم"},
            {"role": "assistant", "content": "وعليكم السلام ورحمة الله وبركاته"}
        ]
        
        with patch.object(openrouter_service, '_make_request_with_fallback') as mock_request:
            mock_request.return_value = mock_openrouter_response
            
            response = await openrouter_service.generate_response(
                message="كيف حالك؟",
                context={"conversation_history": conversation_history},
                language="ar"
            )
            
            assert response is not None
            # Verify that conversation history was included in the request
            call_args = mock_request.call_args[0][0]  # Get messages parameter
            assert len(call_args) > 2  # System prompt + history + current message
    
    @pytest.mark.asyncio
    async def test_build_system_prompt_formal(self, openrouter_service):
        """Test system prompt building for formal personality."""
        prompt = await openrouter_service._build_system_prompt(
            context={"personality": "formal", "dialect": "ar-SA"},
            sentiment="neutral",
            language="ar"
        )
        
        assert "رسمياً ومهذباً" in prompt or "formal" in prompt.lower()
        assert "العربية السعودية" in prompt or "saudi" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_build_system_prompt_negative_sentiment(self, openrouter_service):
        """Test system prompt for negative sentiment handling."""
        prompt = await openrouter_service._build_system_prompt(
            context={"personality": "casual"},
            sentiment="negative",
            language="ar"
        )
        
        assert any(word in prompt for word in ["مستاءً", "اعتذاراً", "حلولاً"])
    
    @pytest.mark.asyncio
    async def test_make_request_with_fallback_success(self, openrouter_service, mock_openrouter_response):
        """Test successful API request."""
        messages = [{"role": "user", "content": "test"}]
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_openrouter_response
        mock_response.raise_for_status.return_value = None
        
        with patch.object(openrouter_service.client, 'post', return_value=mock_response):
            result = await openrouter_service._make_request_with_fallback(messages)
            
            assert result == mock_openrouter_response
            assert openrouter_service.current_model == "google/gemini-flash-1.5"
    
    @pytest.mark.asyncio
    async def test_make_request_with_fallback_model_failure(self, openrouter_service, mock_openrouter_response):
        """Test model fallback on primary model failure."""
        messages = [{"role": "user", "content": "test"}]
        
        # Mock first call to fail, second to succeed
        mock_response_fail = AsyncMock()
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=MagicMock(status_code=500)
        )
        
        mock_response_success = AsyncMock()
        mock_response_success.json.return_value = mock_openrouter_response
        mock_response_success.raise_for_status.return_value = None
        
        with patch.object(openrouter_service.client, 'post', side_effect=[mock_response_fail, mock_response_success]):
            result = await openrouter_service._make_request_with_fallback(messages)
            
            assert result == mock_openrouter_response
            # Should have switched to fallback model
            assert openrouter_service.current_model in openrouter_service.fallback_models
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_retry(self, openrouter_service):
        """Test rate limit handling with retry."""
        messages = [{"role": "user", "content": "test"}]
        
        mock_response_rate_limit = AsyncMock()
        mock_response_rate_limit.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=MagicMock(status_code=429)
        )
        
        with patch.object(openrouter_service.client, 'post', return_value=mock_response_rate_limit):
            with patch('asyncio.sleep') as mock_sleep:
                result = await openrouter_service._make_request_with_fallback(messages)
                
                assert result is None  # Should eventually fail
                mock_sleep.assert_called()  # Should have attempted retry with sleep
    
    @pytest.mark.asyncio
    async def test_get_available_models_success(self, openrouter_service):
        """Test getting available models."""
        mock_models_response = {
            "data": [
                {"id": "google/gemini-flash-1.5"},
                {"id": "anthropic/claude-3-haiku"},
                {"id": "meta-llama/llama-3.1-70b-instruct"}
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_models_response
        mock_response.raise_for_status.return_value = None
        
        with patch.object(openrouter_service.client, 'get', return_value=mock_response):
            models = await openrouter_service.get_available_models()
            
            expected_models = [
                "google/gemini-flash-1.5",
                "anthropic/claude-3-haiku", 
                "meta-llama/llama-3.1-70b-instruct"
            ]
            assert models == expected_models
    
    @pytest.mark.asyncio
    async def test_get_available_models_failure(self, openrouter_service):
        """Test fallback when getting models fails."""
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=MagicMock(status_code=500)
        )
        
        with patch.object(openrouter_service.client, 'get', return_value=mock_response):
            models = await openrouter_service.get_available_models()
            
            # Should return default models
            expected_default = [openrouter_service.primary_model] + openrouter_service.fallback_models
            assert models == expected_default
    
    @pytest.mark.asyncio
    async def test_switch_model_success(self, openrouter_service):
        """Test successful model switching."""
        available_models = ["google/gemini-flash-1.5", "anthropic/claude-3-haiku"]
        target_model = "anthropic/claude-3-haiku"
        
        with patch.object(openrouter_service, 'get_available_models', return_value=available_models):
            result = await openrouter_service.switch_model(target_model)
            
            assert result is True
            assert openrouter_service.current_model == target_model
    
    @pytest.mark.asyncio
    async def test_switch_model_unavailable(self, openrouter_service):
        """Test switching to unavailable model."""
        available_models = ["google/gemini-flash-1.5"]
        target_model = "nonexistent/model"
        
        with patch.object(openrouter_service, 'get_available_models', return_value=available_models):
            result = await openrouter_service.switch_model(target_model)
            
            assert result is False
            assert openrouter_service.current_model != target_model
    
    @pytest.mark.asyncio
    async def test_context_manager_usage(self, openrouter_service):
        """Test using service as async context manager."""
        async with openrouter_service:
            # Service should be usable within context
            assert openrouter_service.client is not None
        
        # After context exit, client should be closed (in real implementation)
        # This test verifies the context manager protocol works