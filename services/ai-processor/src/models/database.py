from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from ..schemas import ConversationContext
from ..utils.config import get_config

class DatabaseManager:
    """Database manager for AI processor persistence."""
    
    def __init__(self):
        self.config = get_config()
        # In a real implementation, this would connect to Supabase
        # For now, this is a placeholder for the database integration
        
    async def save_conversation_context(self, conversation_id: str, context: ConversationContext) -> bool:
        """Save conversation context to database."""
        try:
            # In real implementation, this would update the conversations table
            # UPDATE conversations 
            # SET conversation_context = %s, ai_confidence = %s 
            # WHERE id = %s
            
            context_data = {
                "personality": context.personality,
                "dialect": context.dialect,
                "sentiment_history": context.sentiment_history,
                "topics_discussed": context.topics_discussed,
                "escalation_triggers": context.escalation_triggers,
                "cultural_context": context.cultural_context,
                "last_updated": datetime.now().isoformat()
            }
            
            # Placeholder for actual database save
            print(f"Saving context for conversation {conversation_id}: {context_data}")
            return True
            
        except Exception as e:
            print(f"Error saving conversation context: {e}")
            return False
    
    async def load_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Load conversation context from database."""
        try:
            # In real implementation:
            # SELECT conversation_context FROM conversations WHERE id = %s
            
            # Placeholder return
            return None
            
        except Exception as e:
            print(f"Error loading conversation context: {e}")
            return None
    
    async def save_message_processing_result(
        self, 
        conversation_id: str,
        customer_id: str,
        message: str,
        response: str,
        sentiment: str,
        confidence: float,
        metadata: Dict[str, Any]
    ) -> bool:
        """Save message processing result to database."""
        try:
            # In real implementation, this would insert into conversations.messages JSONB
            message_data = {
                "timestamp": datetime.now().isoformat(),
                "customer_message": message,
                "ai_response": response,
                "sentiment": sentiment,
                "confidence": confidence,
                "dialect": metadata.get("dialect"),
                "cultural_phrases": metadata.get("cultural_phrases", []),
                "suggested_actions": metadata.get("suggested_actions", []),
                "escalation_needed": metadata.get("should_escalate", False)
            }
            
            # UPDATE conversations 
            # SET messages = messages || %s::jsonb,
            #     ai_confidence = %s,
            #     status = CASE WHEN %s THEN 'needs_human' ELSE status END
            # WHERE id = %s
            
            print(f"Saving message result for conversation {conversation_id}: {message_data}")
            return True
            
        except Exception as e:
            print(f"Error saving message result: {e}")
            return False
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from conversation."""
        try:
            # In real implementation:
            # SELECT messages FROM conversations WHERE id = %s
            # Then extract last N messages from JSONB array
            
            # Placeholder return
            return []
            
        except Exception as e:
            print(f"Error getting conversation messages: {e}")
            return []
    
    async def update_conversation_ai_confidence(self, conversation_id: str, confidence: float) -> bool:
        """Update AI confidence score for conversation."""
        try:
            # UPDATE conversations SET ai_confidence = %s WHERE id = %s
            print(f"Updating AI confidence for conversation {conversation_id}: {confidence}")
            return True
            
        except Exception as e:
            print(f"Error updating AI confidence: {e}")
            return False
    
    async def get_customer_language_preference(self, customer_id: str) -> Optional[str]:
        """Get customer's language preference."""
        try:
            # SELECT language_preference FROM customers WHERE id = %s
            # Return default Saudi dialect if not found
            return "ar-SA"
            
        except Exception as e:
            print(f"Error getting language preference: {e}")
            return "ar-SA"
    
    async def get_restaurant_personality_type(self, restaurant_id: str) -> Optional[str]:
        """Get restaurant's personality type configuration."""
        try:
            # SELECT personality_type FROM restaurants WHERE id = %s
            return "formal"
            
        except Exception as e:
            print(f"Error getting restaurant personality: {e}")
            return "formal"
    
    async def create_escalation_alert(
        self, 
        conversation_id: str,
        customer_id: str, 
        restaurant_id: str,
        reason: str,
        urgency: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Create escalation alert for human attention."""
        try:
            alert_data = {
                "conversation_id": conversation_id,
                "customer_id": customer_id,
                "restaurant_id": restaurant_id,
                "reason": reason,
                "urgency": urgency,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "metadata": metadata
            }
            
            # INSERT INTO escalation_alerts (...) VALUES (...)
            print(f"Creating escalation alert: {alert_data}")
            return True
            
        except Exception as e:
            print(f"Error creating escalation alert: {e}")
            return False
    
    async def get_ai_processing_stats(self, time_period: str = "24h") -> Dict[str, Any]:
        """Get AI processing statistics."""
        try:
            # Complex query to get stats from conversations and escalation_alerts tables
            stats = {
                "total_conversations": 150,
                "total_messages": 450,
                "sentiment_distribution": {
                    "positive": 60,
                    "neutral": 30, 
                    "negative": 10
                },
                "escalation_rate": 8.5,
                "average_confidence": 0.82,
                "dialect_distribution": {
                    "ar-SA": 70,
                    "ar-EG": 15,
                    "ar-LV": 10,
                    "en": 5
                },
                "time_period": time_period
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting AI stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_contexts(self, days_old: int = 7) -> int:
        """Clean up old conversation contexts."""
        try:
            # DELETE FROM conversations WHERE last_updated < NOW() - INTERVAL %s DAY
            # AND status = 'completed'
            
            print(f"Cleaning up contexts older than {days_old} days")
            return 25  # Placeholder count
            
        except Exception as e:
            print(f"Error cleaning up old contexts: {e}")
            return 0

# Global database instance
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager