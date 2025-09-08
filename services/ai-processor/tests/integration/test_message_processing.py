import pytest
from unittest.mock import patch, AsyncMock
from src.agents.message_processor import MessageProcessor
from src.schemas import AIProcessingRequest

@pytest.mark.integration
@pytest.mark.arabic
class TestMessageProcessingIntegration:
    """Integration tests for complete message processing flow."""
    
    @pytest.fixture
    def message_processor(self):
        """Create message processor instance."""
        return MessageProcessor()
    
    @pytest.fixture
    def mock_external_services(self, mock_openrouter_response):
        """Mock all external service calls."""
        mocks = {}
        
        # Mock OpenRouter API
        mocks['openrouter'] = patch('src.services.openrouter_service.OpenRouterService._make_request_with_fallback')
        mocks['openrouter'].return_value = mock_openrouter_response
        
        # Mock Prayer Times API
        mocks['prayer'] = patch('src.services.prayer_time_service.PrayerTimeService.should_delay_message')
        mocks['prayer'].return_value = {"should_delay": False, "delay_minutes": 0}
        
        # Start all mocks
        for mock in mocks.values():
            mock.start()
        
        yield mocks
        
        # Stop all mocks
        for mock in mocks.values():
            mock.stop()
    
    @pytest.mark.asyncio
    async def test_complete_message_processing_flow(self, message_processor, sample_ai_processing_request, mock_external_services):
        """Test complete message processing from request to response."""
        request = AIProcessingRequest(**sample_ai_processing_request)
        
        with patch.object(message_processor.openrouter, '_make_request_with_fallback') as mock_openrouter:
            mock_openrouter.return_value = {
                "choices": [{"message": {"content": "مرحباً! كيف يمكنني مساعدتك اليوم؟"}}]
            }
            
            response = await message_processor.process_message(request)
            
            # Verify response structure
            assert response.response is not None
            assert response.sentiment in ["positive", "neutral", "negative"]
            assert 0.0 <= response.confidence <= 1.0
            assert isinstance(response.suggested_actions, list)
            assert isinstance(response.is_prayer_time, bool)
            assert isinstance(response.should_escalate, bool)
    
    @pytest.mark.asyncio
    async def test_arabic_dialect_detection_integration(self, message_processor, sample_arabic_messages):
        """Test Arabic dialect detection integration."""
        # Test Saudi dialect
        saudi_request = AIProcessingRequest(
            message=sample_arabic_messages["saudi_positive"],
            conversation_id="test-saudi-123",
            customer_id="test-customer-456"
        )
        
        with patch.object(message_processor.openrouter, '_make_request_with_fallback') as mock_openrouter:
            mock_openrouter.return_value = {
                "choices": [{"message": {"content": "هلا والله! نسعد بإعجابكم"}}]
            }
            
            response = await message_processor.process_message(saudi_request)
            
            assert response.dialect_detected == "ar-SA"
            assert any("هلا" in phrase for phrase in response.cultural_phrases_used)
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_integration(self, message_processor, sample_arabic_messages):
        """Test sentiment analysis integration with escalation."""
        # Test negative sentiment
        negative_request = AIProcessingRequest(
            message=sample_arabic_messages["complaint"],
            conversation_id="test-negative-123",
            customer_id="test-customer-456"
        )
        
        with patch.object(message_processor.openrouter, '_make_request_with_fallback') as mock_openrouter:
            mock_openrouter.return_value = {
                "choices": [{"message": {"content": "نعتذر بشدة عن هذه التجربة"}}]
            }
            
            response = await message_processor.process_message(negative_request)
            
            assert response.sentiment == "negative"
            assert "escalate_to_human" in response.suggested_actions
            # High confidence negative sentiment should trigger escalation
            if response.confidence > 0.8:
                assert response.should_escalate is True
    
    @pytest.mark.asyncio
    async def test_prayer_time_handling_integration(self, message_processor, sample_ai_processing_request):
        """Test prayer time handling integration."""
        request = AIProcessingRequest(**sample_ai_processing_request)
        
        # Mock prayer time as active
        with patch.object(message_processor, '_check_prayer_time_constraints') as mock_prayer:
            mock_prayer.return_value = {
                "should_delay": True,
                "delay_minutes": 10,
                "reason": "prayer_time_dhuhr"
            }
            
            response = await message_processor.process_message(request)
            
            assert response.is_prayer_time is True
            assert "صلاة" in response.response or "prayer" in response.response.lower()
            assert "delay_message" in response.suggested_actions
    
    @pytest.mark.asyncio
    async def test_conversation_context_persistence(self, message_processor):
        """Test conversation context is maintained across messages."""
        conversation_id = "test-context-persistence-123"
        customer_id = "test-customer-456"
        
        # First message
        first_request = AIProcessingRequest(
            message="السلام عليكم، أريد أن أحجز طاولة",
            conversation_id=conversation_id,
            customer_id=customer_id
        )
        
        with patch.object(message_processor.openrouter, '_make_request_with_fallback') as mock_openrouter:
            mock_openrouter.return_value = {
                "choices": [{"message": {"content": "وعليكم السلام، بكم شخص تريدون الحجز؟"}}]
            }
            
            first_response = await message_processor.process_message(first_request)
            
            # Second message in same conversation
            second_request = AIProcessingRequest(
                message="أربعة أشخاص",
                conversation_id=conversation_id,
                customer_id=customer_id
            )
            
            second_response = await message_processor.process_message(second_request)
            
            # Both responses should have same conversation context
            assert first_response.dialect_detected == second_response.dialect_detected
            # Conversation should have remembered the context
            assert "process_reservation" in first_response.suggested_actions
    
    @pytest.mark.asyncio
    async def test_cultural_phrase_handling_integration(self, message_processor):
        """Test cultural phrase handling integration."""
        # Message with Islamic greeting
        request = AIProcessingRequest(
            message="السلام عليكم، بارك الله فيكم على الخدمة الممتازة",
            conversation_id="test-cultural-123",
            customer_id="test-customer-456"
        )
        
        with patch.object(message_processor.openrouter, '_make_request_with_fallback') as mock_openrouter:
            mock_openrouter.return_value = {
                "choices": [{"message": {"content": "وعليكم السلام، وفيك بارك الله"}}]
            }
            
            response = await message_processor.process_message(request)
            
            # Should detect and respond to cultural phrases appropriately
            assert "السلام عليكم" in response.cultural_phrases_used or "بارك الله فيكم" in response.cultural_phrases_used
            assert "acknowledge_cultural_phrases" in response.suggested_actions
            # Response should contain appropriate cultural response
            assert "وعليكم السلام" in response.response or "وفيك بارك الله" in response.response
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, message_processor, sample_ai_processing_request):
        """Test error handling in complete processing flow."""
        request = AIProcessingRequest(**sample_ai_processing_request)
        
        # Mock OpenRouter service to raise an exception
        with patch.object(message_processor.openrouter, 'generate_response') as mock_openrouter:
            mock_openrouter.side_effect = Exception("OpenRouter API error")
            
            response = await message_processor.process_message(request)
            
            # Should return error response that escalates to human
            assert response.should_escalate is True
            assert "technical_issue" in response.suggested_actions
            assert "خطأ" in response.response or "error" in response.response.lower()
    
    @pytest.mark.asyncio
    async def test_batch_processing_integration(self, message_processor):
        """Test batch message processing."""
        requests = [
            AIProcessingRequest(
                message="مرحبا",
                conversation_id=f"test-batch-{i}",
                customer_id="test-customer-456"
            ) for i in range(3)
        ]
        
        with patch.object(message_processor.openrouter, '_make_request_with_fallback') as mock_openrouter:
            mock_openrouter.return_value = {
                "choices": [{"message": {"content": "مرحباً بك"}}]
            }
            
            responses = await message_processor.batch_process_messages(requests)
            
            assert len(responses) == 3
            for response in responses:
                assert response.response is not None
                assert response.confidence > 0
    
    @pytest.mark.asyncio
    async def test_processing_stats_integration(self, message_processor, sample_ai_processing_request):
        """Test processing statistics integration."""
        request = AIProcessingRequest(**sample_ai_processing_request)
        
        with patch.object(message_processor.openrouter, '_make_request_with_fallback') as mock_openrouter:
            mock_openrouter.return_value = {
                "choices": [{"message": {"content": "مرحباً"}}]
            }
            
            # Process a message first
            await message_processor.process_message(request)
            
            # Get stats
            stats = await message_processor.get_processing_stats(request.conversation_id)
            
            assert "conversation_id" in stats
            assert "total_messages" in stats
            assert "sentiment_distribution" in stats
            assert "dominant_dialect" in stats
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, message_processor):
        """Test health check integration."""
        health_status = await message_processor.health_check()
        
        assert "status" in health_status
        assert "components" in health_status
        
        # All components should be reported
        components = health_status["components"]
        expected_components = [
            "openrouter_service", "sentiment_analyzer", "prayer_service",
            "arabic_processor", "conversation_agent"
        ]
        
        for component in expected_components:
            assert component in components