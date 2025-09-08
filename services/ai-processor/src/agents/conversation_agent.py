import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..schemas import ConversationContext, PersonalityType, DialectType
from ..utils.cache import get_cache_manager
from ..utils.config import get_config

class ConversationAgent:
    """Agent for managing conversation context and memory."""
    
    def __init__(self):
        self.config = get_config()
        self.cache = get_cache_manager()
        self.context_limit = self.config.conversation_context_limit
        self.context_expiry = 3600  # 1 hour
    
    async def get_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Retrieve conversation context from cache or database."""
        try:
            # Try cache first
            cache_key = f"conversation_context_{conversation_id}"
            cached_context = await self.cache.get(cache_key)
            
            if cached_context:
                return ConversationContext(**cached_context)
            
            # If not in cache, would load from database here
            # For now, return default context
            return ConversationContext(
                conversation_id=conversation_id,
                personality=PersonalityType.formal,
                dialect=DialectType.saudi
            )
            
        except Exception as e:
            print(f"Error getting conversation context: {e}")
            return ConversationContext(conversation_id=conversation_id)
    
    async def update_conversation_context(
        self, 
        conversation_id: str, 
        message: str, 
        response: str,
        sentiment: str,
        cultural_phrases: List[str] = None,
        dialect_detected: Optional[str] = None
    ) -> ConversationContext:
        """Update conversation context with new message and response."""
        try:
            context = await self.get_conversation_context(conversation_id)
            
            # Update sentiment history
            context.sentiment_history.append(sentiment)
            if len(context.sentiment_history) > 10:  # Keep only last 10
                context.sentiment_history = context.sentiment_history[-10:]
            
            # Update topics discussed (simple keyword extraction)
            topics = self._extract_topics(message)
            for topic in topics:
                if topic not in context.topics_discussed:
                    context.topics_discussed.append(topic)
            
            # Keep only recent topics (last 20)
            if len(context.topics_discussed) > 20:
                context.topics_discussed = context.topics_discussed[-20:]
            
            # Update dialect if detected
            if dialect_detected:
                context.dialect = DialectType(dialect_detected)
            
            # Update cultural context
            if cultural_phrases:
                context.cultural_context["recent_phrases"] = cultural_phrases
                context.cultural_context["greeting_style"] = self._determine_greeting_style(cultural_phrases)
            
            # Add escalation triggers if negative sentiment persists
            recent_sentiment = context.sentiment_history[-3:] if len(context.sentiment_history) >= 3 else context.sentiment_history
            if all(s == "negative" for s in recent_sentiment) and len(recent_sentiment) >= 2:
                if "repeated_negative_feedback" not in context.escalation_triggers:
                    context.escalation_triggers.append("repeated_negative_feedback")
            
            # Update conversation context
            context.cultural_context["last_updated"] = datetime.now().isoformat()
            
            # Cache the updated context
            cache_key = f"conversation_context_{conversation_id}"
            await self.cache.set(cache_key, context.dict(), expire=self.context_expiry)
            
            return context
            
        except Exception as e:
            print(f"Error updating conversation context: {e}")
            return await self.get_conversation_context(conversation_id)
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract topics from message using simple keyword matching."""
        topics = []
        
        # Food-related topics
        food_keywords = {
            'طعام': 'food',
            'أكل': 'food', 
            'وجبة': 'meal',
            'طبق': 'dish',
            'مقبلات': 'appetizers',
            'حلا': 'dessert',
            'حلويات': 'desserts',
            'مشروب': 'drinks',
            'عصير': 'juice',
            'قهوة': 'coffee',
            'شاي': 'tea'
        }
        
        # Service-related topics
        service_keywords = {
            'خدمة': 'service',
            'موظف': 'staff',
            'سرعة': 'speed',
            'انتظار': 'waiting',
            'حجز': 'reservation',
            'طلب': 'order',
            'تسليم': 'delivery',
            'فاتورة': 'bill',
            'دفع': 'payment'
        }
        
        # Quality-related topics
        quality_keywords = {
            'جودة': 'quality',
            'طازج': 'fresh',
            'بارد': 'cold',
            'حار': 'hot',
            'طعم': 'taste',
            'رائحة': 'smell',
            'شكل': 'appearance',
            'كمية': 'quantity',
            'سعر': 'price'
        }
        
        all_keywords = {**food_keywords, **service_keywords, **quality_keywords}
        
        for arabic_word, topic in all_keywords.items():
            if arabic_word in message:
                topics.append(topic)
        
        return list(set(topics))  # Remove duplicates
    
    def _determine_greeting_style(self, cultural_phrases: List[str]) -> str:
        """Determine greeting style from cultural phrases used."""
        if not cultural_phrases:
            return "neutral"
        
        formal_indicators = ['السلام عليكم', 'بارك الله فيك', 'جزاك الله خير']
        casual_indicators = ['هلا', 'أهلين', 'وش أخبارك']
        
        formal_count = sum(1 for phrase in cultural_phrases if phrase in formal_indicators)
        casual_count = sum(1 for phrase in cultural_phrases if phrase in casual_indicators)
        
        if formal_count > casual_count:
            return "formal"
        elif casual_count > formal_count:
            return "casual"
        else:
            return "neutral"
    
    async def get_conversation_history(self, conversation_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get conversation history for context."""
        try:
            if limit is None:
                limit = self.context_limit
            
            cache_key = f"conversation_history_{conversation_id}"
            history = await self.cache.get(cache_key)
            
            if history:
                return history[-limit:] if len(history) > limit else history
            
            # Would load from database here
            return []
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    async def add_to_conversation_history(
        self, 
        conversation_id: str, 
        message: str, 
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add message and response to conversation history."""
        try:
            history = await self.get_conversation_history(conversation_id, limit=100)  # Get more for storage
            
            new_entry = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "response": response,
                "metadata": metadata or {}
            }
            
            history.append(new_entry)
            
            # Keep only recent history
            if len(history) > self.context_limit * 2:
                history = history[-self.context_limit * 2:]
            
            cache_key = f"conversation_history_{conversation_id}"
            await self.cache.set(cache_key, history, expire=self.context_expiry)
            
        except Exception as e:
            print(f"Error adding to conversation history: {e}")
    
    async def should_escalate_conversation(self, context: ConversationContext) -> Dict[str, Any]:
        """Determine if conversation should be escalated to human."""
        escalation_score = 0
        reasons = []
        
        # Check escalation triggers
        if context.escalation_triggers:
            escalation_score += len(context.escalation_triggers) * 20
            reasons.extend(context.escalation_triggers)
        
        # Check recent sentiment
        if len(context.sentiment_history) >= 3:
            recent_sentiment = context.sentiment_history[-3:]
            negative_count = sum(1 for s in recent_sentiment if s == "negative")
            
            if negative_count >= 2:
                escalation_score += 30
                reasons.append("persistent_negative_sentiment")
        
        # Check conversation length (might indicate complex issue)
        topic_count = len(context.topics_discussed)
        if topic_count > 8:
            escalation_score += 15
            reasons.append("complex_multi_topic_conversation")
        
        # Specific escalation keywords in topics
        escalation_topics = ["complaint", "manager", "refund", "health", "allergy"]
        for topic in context.topics_discussed:
            if topic in escalation_topics:
                escalation_score += 25
                reasons.append(f"escalation_topic_{topic}")
        
        should_escalate = escalation_score >= 50
        
        return {
            "should_escalate": should_escalate,
            "escalation_score": escalation_score,
            "reasons": reasons,
            "urgency": "high" if escalation_score >= 70 else "medium" if escalation_score >= 50 else "low"
        }
    
    async def get_personalized_prompt_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get personalized context for prompt generation."""
        try:
            context = await self.get_conversation_context(conversation_id)
            history = await self.get_conversation_history(conversation_id, limit=5)
            
            return {
                "personality": context.personality,
                "dialect": context.dialect,
                "recent_sentiment": context.sentiment_history[-3:] if context.sentiment_history else [],
                "topics_discussed": context.topics_discussed[-10:] if context.topics_discussed else [],
                "greeting_style": context.cultural_context.get("greeting_style", "formal"),
                "conversation_history": history,
                "escalation_indicators": context.escalation_triggers,
                "cultural_phrases": context.cultural_context.get("recent_phrases", [])
            }
            
        except Exception as e:
            print(f"Error getting personalized context: {e}")
            return {
                "personality": PersonalityType.formal,
                "dialect": DialectType.saudi,
                "recent_sentiment": [],
                "topics_discussed": [],
                "greeting_style": "formal",
                "conversation_history": [],
                "escalation_indicators": [],
                "cultural_phrases": []
            }
    
    async def reset_conversation_context(self, conversation_id: str) -> None:
        """Reset conversation context (for new conversations or escalations)."""
        try:
            cache_key_context = f"conversation_context_{conversation_id}"
            cache_key_history = f"conversation_history_{conversation_id}"
            
            await self.cache.delete(cache_key_context)
            await self.cache.delete(cache_key_history)
            
        except Exception as e:
            print(f"Error resetting conversation context: {e}")
    
    async def get_context_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation context for monitoring."""
        try:
            context = await self.get_conversation_context(conversation_id)
            history = await self.get_conversation_history(conversation_id)
            
            return {
                "conversation_id": conversation_id,
                "personality": context.personality,
                "dialect": context.dialect,
                "message_count": len(history),
                "sentiment_distribution": self._get_sentiment_distribution(context.sentiment_history),
                "topics_count": len(context.topics_discussed),
                "escalation_triggers": len(context.escalation_triggers),
                "last_updated": context.cultural_context.get("last_updated"),
                "needs_attention": len(context.escalation_triggers) > 0
            }
            
        except Exception as e:
            print(f"Error getting context summary: {e}")
            return {"conversation_id": conversation_id, "error": str(e)}
    
    def _get_sentiment_distribution(self, sentiment_history: List[str]) -> Dict[str, int]:
        """Get distribution of sentiments in conversation."""
        distribution = {"positive": 0, "neutral": 0, "negative": 0}
        
        for sentiment in sentiment_history:
            if sentiment in distribution:
                distribution[sentiment] += 1
        
        return distribution