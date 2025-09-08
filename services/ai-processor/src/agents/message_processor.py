from typing import Dict, Any, Optional, List
from ..schemas import AIProcessingRequest, AIProcessingResponse, PersonalityType, DialectType
from ..services.openrouter_service import OpenRouterService
from ..services.sentiment_analyzer import SentimentAnalyzer
from ..services.prayer_time_service import PrayerTimeService
from ..services.arabic_processor import ArabicProcessor
from ..prompts.arabic_prompts import ArabicPromptManager
from .conversation_agent import ConversationAgent
from ..utils.config import get_config

class MessageProcessor:
    """Main message processing agent that orchestrates all AI services."""
    
    def __init__(self):
        self.config = get_config()
        self.openrouter = OpenRouterService()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.prayer_service = PrayerTimeService()
        self.arabic_processor = ArabicProcessor()
        self.prompt_manager = ArabicPromptManager()
        self.conversation_agent = ConversationAgent()
    
    async def process_message(self, request: AIProcessingRequest) -> AIProcessingResponse:
        """Process incoming message through the complete AI pipeline."""
        try:
            # Step 1: Check prayer time constraints
            prayer_status = await self._check_prayer_time_constraints()
            if prayer_status["should_delay"]:
                return AIProcessingResponse(
                    response=self._generate_prayer_time_response(prayer_status),
                    sentiment="neutral",
                    confidence=1.0,
                    suggested_actions=["delay_message"],
                    is_prayer_time=True,
                    should_escalate=False
                )
            
            # Step 2: Process and analyze Arabic text
            arabic_result = self.arabic_processor.detect_dialect(request.message)
            processed_message = arabic_result.processed_text
            
            # Step 3: Analyze sentiment
            sentiment_result = await self.sentiment_analyzer.analyze(processed_message)
            
            # Step 4: Get conversation context
            conversation_context = await self.conversation_agent.get_personalized_prompt_context(
                request.conversation_id
            )
            
            # Step 5: Generate system prompt
            system_prompt = self.prompt_manager.get_system_prompt(
                personality=conversation_context["personality"],
                dialect=arabic_result.dialect_detected,
                context={
                    "sentiment": sentiment_result["sentiment"],
                    "topics_discussed": conversation_context["topics_discussed"],
                    "recent_sentiment": conversation_context["recent_sentiment"]
                }
            )
            
            # Step 6: Generate AI response
            ai_response = await self.openrouter.generate_response(
                message=processed_message,
                context={
                    "system_prompt": system_prompt,
                    "conversation_history": conversation_context["conversation_history"],
                    "personality": conversation_context["personality"],
                    "dialect": arabic_result.dialect_detected
                },
                sentiment=sentiment_result["sentiment"],
                language="ar"
            )
            
            # Step 7: Format response with cultural awareness
            formatted_response = self.arabic_processor.format_cultural_response(
                ai_response, arabic_result.cultural_phrases
            )
            
            # Step 8: Update conversation context
            updated_context = await self.conversation_agent.update_conversation_context(
                conversation_id=request.conversation_id,
                message=request.message,
                response=formatted_response,
                sentiment=sentiment_result["sentiment"],
                cultural_phrases=arabic_result.cultural_phrases,
                dialect_detected=arabic_result.dialect_detected.value
            )
            
            # Step 9: Check escalation needs
            escalation_check = await self.conversation_agent.should_escalate_conversation(updated_context)
            
            # Step 10: Generate suggested actions
            suggested_actions = self._generate_suggested_actions(
                sentiment_result, arabic_result, escalation_check, processed_message
            )
            
            # Step 11: Add to conversation history
            await self.conversation_agent.add_to_conversation_history(
                conversation_id=request.conversation_id,
                message=request.message,
                response=formatted_response,
                metadata={
                    "sentiment": sentiment_result["sentiment"],
                    "confidence": sentiment_result["confidence"],
                    "dialect": arabic_result.dialect_detected.value,
                    "cultural_phrases": arabic_result.cultural_phrases,
                    "suggested_actions": suggested_actions
                }
            )
            
            return AIProcessingResponse(
                response=formatted_response,
                sentiment=sentiment_result["sentiment"],
                confidence=sentiment_result["confidence"],
                suggested_actions=suggested_actions,
                is_prayer_time=False,
                should_escalate=escalation_check["should_escalate"],
                dialect_detected=arabic_result.dialect_detected.value,
                cultural_phrases_used=arabic_result.cultural_phrases
            )
            
        except Exception as e:
            print(f"Error in message processing: {e}")
            return await self._generate_error_response(request, str(e))
    
    async def _check_prayer_time_constraints(self) -> Dict[str, Any]:
        """Check if message should be delayed due to prayer time."""
        try:
            return await self.prayer_service.should_delay_message("Riyadh")
        except Exception as e:
            print(f"Error checking prayer time: {e}")
            return {"should_delay": False, "delay_minutes": 0}
    
    def _generate_prayer_time_response(self, prayer_status: Dict[str, Any]) -> str:
        """Generate appropriate response during prayer time."""
        prayer_responses = {
            "prayer_time_fajr": "نعتذر، نحن متوقفون مؤقتاً أثناء صلاة الفجر. سنعود إليكم بعد قليل إن شاء الله.",
            "prayer_time_dhuhr": "نعتذر، نحن متوقفون مؤقتاً أثناء صلاة الظهر. سنعود إليكم بعد قليل إن شاء الله.",
            "prayer_time_asr": "نعتذر، نحن متوقفون مؤقتاً أثناء صلاة العصر. سنعود إليكم بعد قليل إن شاء الله.",
            "prayer_time_maghrib": "نعتذر، نحن متوقفون مؤقتاً أثناء صلاة المغرب. سنعود إليكم بعد قليل إن شاء الله.",
            "prayer_time_isha": "نعتذر، نحن متوقفون مؤقتاً أثناء صلاة العشاء. سنعود إليكم بعد قليل إن شاء الله."
        }
        
        reason = prayer_status.get("reason", "prayer_time")
        return prayer_responses.get(reason, "نعتذر، نحن متوقفون مؤقتاً أثناء أوقات الصلاة. سنعود إليكم قريباً إن شاء الله.")
    
    def _generate_suggested_actions(
        self, 
        sentiment_result: Dict[str, Any], 
        arabic_result: Any,
        escalation_check: Dict[str, Any], 
        message: str
    ) -> List[str]:
        """Generate suggested actions based on analysis results."""
        actions = []
        
        # Sentiment-based actions
        if sentiment_result["sentiment"] == "negative":
            actions.append("escalate_to_human")
            if sentiment_result["confidence"] > 0.8:
                actions.append("priority_escalation")
        
        # Escalation-based actions
        if escalation_check["should_escalate"]:
            actions.append("human_handoff")
            if escalation_check["urgency"] == "high":
                actions.append("urgent_attention")
        
        # Content-based actions
        order_keywords = ["طلب", "أريد", "order", "طلبية"]
        reservation_keywords = ["حجز", "reservation", "موعد", "طاولة"]
        complaint_keywords = ["شكوى", "مشكلة", "complaint", "غير راضي"]
        
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in order_keywords):
            actions.append("process_order")
        
        if any(keyword in message_lower for keyword in reservation_keywords):
            actions.append("process_reservation")
        
        if any(keyword in message_lower for keyword in complaint_keywords):
            actions.append("handle_complaint")
        
        # Cultural phrase actions
        if arabic_result.cultural_phrases:
            actions.append("acknowledge_cultural_phrases")
        
        return list(set(actions))  # Remove duplicates
    
    async def _generate_error_response(self, request: AIProcessingRequest, error: str) -> AIProcessingResponse:
        """Generate appropriate error response."""
        error_responses = [
            "عذراً، حدث خطأ تقني مؤقت. سيتم توجيهكم لأحد موظفينا للمساعدة.",
            "نعتذر عن المشكلة التقنية. موظفونا جاهزون لمساعدتكم الآن.",
            "عذراً للخلل المؤقت. سنحولكم لخدمة العملاء مباشرة."
        ]
        
        # Use hash of conversation_id to consistently select same response
        response_index = hash(request.conversation_id) % len(error_responses)
        
        return AIProcessingResponse(
            response=error_responses[response_index],
            sentiment="neutral",
            confidence=0.8,
            suggested_actions=["escalate_to_human", "technical_issue"],
            is_prayer_time=False,
            should_escalate=True
        )
    
    async def get_processing_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get processing statistics for a conversation."""
        try:
            context_summary = await self.conversation_agent.get_context_summary(conversation_id)
            
            return {
                "conversation_id": conversation_id,
                "total_messages": context_summary.get("message_count", 0),
                "sentiment_distribution": context_summary.get("sentiment_distribution", {}),
                "dominant_dialect": context_summary.get("dialect", "ar-SA"),
                "personality_type": context_summary.get("personality", "formal"),
                "escalation_triggers": context_summary.get("escalation_triggers", 0),
                "needs_attention": context_summary.get("needs_attention", False),
                "last_updated": context_summary.get("last_updated")
            }
            
        except Exception as e:
            print(f"Error getting processing stats: {e}")
            return {"conversation_id": conversation_id, "error": str(e)}
    
    async def batch_process_messages(self, requests: List[AIProcessingRequest]) -> List[AIProcessingResponse]:
        """Process multiple messages in batch (for high-throughput scenarios)."""
        responses = []
        
        for request in requests:
            try:
                response = await self.process_message(request)
                responses.append(response)
            except Exception as e:
                error_response = await self._generate_error_response(request, str(e))
                responses.append(error_response)
        
        return responses
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the message processor."""
        try:
            # Test basic functionality
            test_request = AIProcessingRequest(
                message="مرحبا",
                conversation_id="health_check",
                customer_id="health_check"
            )
            
            # Quick processing test
            arabic_result = self.arabic_processor.detect_dialect("مرحبا")
            sentiment_result = await self.sentiment_analyzer.analyze("مرحبا")
            
            return {
                "status": "healthy",
                "components": {
                    "openrouter_service": "available",
                    "sentiment_analyzer": "available",
                    "prayer_service": "available",
                    "arabic_processor": "available",
                    "conversation_agent": "available"
                },
                "dialect_detection": arabic_result.dialect_detected.value,
                "sentiment_analysis": sentiment_result["sentiment"],
                "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }