"""
Conversation Models for Feedback Collection
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain.memory import ConversationBufferWindowMemory
from enum import Enum


class FeedbackStage(str, Enum):
    """Stages of feedback collection conversation"""
    GREETING = "greeting"
    REQUESTING_RATING = "requesting_rating"
    PROBING_ISSUES = "probing_issues"
    CELEBRATING_POSITIVE = "celebrating_positive"
    UNDERSTANDING_NEUTRAL = "understanding_neutral"
    WRAPPING_UP = "wrapping_up"
    COMPLETE = "complete"


class ConversationTemplate(str, Enum):
    """Available conversation templates"""
    DEFAULT = "default"
    FORMAL = "formal"
    CASUAL = "casual"
    VIP = "vip"


@dataclass
class FeedbackConversation:
    """Model for feedback collection conversation state"""
    
    id: str
    customer_phone: str
    visit_timestamp: datetime
    stage: FeedbackStage = FeedbackStage.GREETING
    template: ConversationTemplate = ConversationTemplate.DEFAULT
    memory: ConversationBufferWindowMemory = field(default_factory=lambda: ConversationBufferWindowMemory(
        k=10,
        return_messages=True,
        input_key="customer_input",
        output_key="ai_response"
    ))
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default context if empty"""
        if not self.context:
            self.context = {
                "time_since_visit": "",
                "ratings_collected": {},
                "topics_discussed": [],
                "sentiment_scores": [],
                "message_count": 0,
                "last_rating": None,
                "customer_responses": [],
                "ai_responses": []
            }
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
        self.context["message_count"] = self.context.get("message_count", 0) + 1
    
    def add_rating(self, aspect: str, rating: int):
        """Add a rating for a specific aspect"""
        if "ratings_collected" not in self.context:
            self.context["ratings_collected"] = {}
        
        self.context["ratings_collected"][aspect] = rating
        self.context["last_rating"] = rating
        self.update_activity()
    
    def add_topic(self, topic: str):
        """Add a discussed topic"""
        if "topics_discussed" not in self.context:
            self.context["topics_discussed"] = []
        
        if topic not in self.context["topics_discussed"]:
            self.context["topics_discussed"].append(topic)
        
        self.update_activity()
    
    def add_sentiment(self, sentiment_score: float):
        """Add sentiment score from latest interaction"""
        if "sentiment_scores" not in self.context:
            self.context["sentiment_scores"] = []
        
        self.context["sentiment_scores"].append({
            "score": sentiment_score,
            "timestamp": datetime.now().isoformat()
        })
        
        self.update_activity()
    
    def get_average_sentiment(self) -> float:
        """Calculate average sentiment throughout conversation"""
        scores = self.context.get("sentiment_scores", [])
        if not scores:
            return 0.0
        
        return sum(s["score"] for s in scores) / len(scores)
    
    def get_conversation_duration(self) -> int:
        """Get conversation duration in minutes"""
        duration = self.last_activity - self.started_at
        return int(duration.total_seconds() / 60)
    
    def is_timeout(self, timeout_minutes: int = 30) -> bool:
        """Check if conversation has timed out"""
        duration = datetime.now() - self.last_activity
        return duration.total_seconds() > (timeout_minutes * 60)
    
    def get_overall_rating(self) -> Optional[int]:
        """Get the overall rating if provided"""
        return self.context.get("ratings_collected", {}).get("overall")
    
    def has_sufficient_feedback(self) -> bool:
        """Check if we have collected sufficient feedback"""
        ratings = self.context.get("ratings_collected", {})
        topics = self.context.get("topics_discussed", [])
        messages = self.context.get("message_count", 0)
        
        # Consider sufficient if:
        # 1. Has overall rating AND at least 2 topics OR
        # 2. Has detailed conversation (5+ messages) with topics OR  
        # 3. Has multiple aspect ratings
        
        return (
            (ratings.get("overall") is not None and len(topics) >= 2) or
            (messages >= 5 and len(topics) >= 1) or
            len(ratings) >= 3
        )
    
    def should_continue_conversation(self) -> bool:
        """Determine if conversation should continue"""
        if not self.is_active:
            return False
        
        if self.is_timeout():
            return False
        
        if self.stage == FeedbackStage.COMPLETE:
            return False
        
        # Don't continue if we have enough feedback and it's been going long
        if self.has_sufficient_feedback() and self.context.get("message_count", 0) >= 8:
            return False
        
        return True
    
    def get_next_questions(self) -> List[str]:
        """Get suggested next questions based on current state"""
        overall_rating = self.get_overall_rating()
        topics = self.context.get("topics_discussed", [])
        
        if not overall_rating:
            return ["كيف تقيم تجربتك معنا من 1 إلى 5؟"]
        
        # Questions based on rating
        if overall_rating <= 2:
            questions = [
                "ما هي المشكلة الرئيسية التي واجهتها؟",
                "هل كان هناك خطأ في طلبك؟",
                "كيف يمكننا تحسين تجربتك؟"
            ]
        elif overall_rating == 3:
            questions = [
                "ما الذي كان جيداً في تجربتك؟",
                "ما الذي تتمنى أن نحسنه؟",
                "هل لديك اقتراحات للتطوير؟"
            ]
        else:  # 4-5
            questions = [
                "ما الذي أعجبك أكثر شيء؟",
                "أي الأطباق كانت الأفضل؟",
                "هل ستوصي أصدقاءك بالمطعم؟"
            ]
        
        # Filter out topics already discussed
        discussed_lower = [t.lower() for t in topics]
        
        # Add specific follow-ups if topics haven't been covered
        if "food" not in discussed_lower and "طعام" not in discussed_lower:
            questions.append("كيف وجدت جودة الطعام؟")
        
        if "service" not in discussed_lower and "خدمة" not in discussed_lower:
            questions.append("كيف كانت تجربة الخدمة؟")
        
        if "cleanliness" not in discussed_lower and "نظافة" not in discussed_lower:
            questions.append("ما رأيك في نظافة المكان؟")
        
        return questions[:3]  # Return max 3 questions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary for serialization"""
        return {
            "id": self.id,
            "customer_phone": self.customer_phone,
            "visit_timestamp": self.visit_timestamp.isoformat(),
            "stage": self.stage.value,
            "template": self.template.value,
            "context": self.context,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active,
            "metadata": self.metadata,
            "conversation_history": [
                {
                    "role": "human" if i % 2 == 0 else "ai",
                    "content": msg.content,
                    "timestamp": self.started_at.isoformat()  # Simplified
                }
                for i, msg in enumerate(self.memory.chat_memory.messages)
            ] if hasattr(self, 'memory') and self.memory else []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackConversation':
        """Create conversation from dictionary"""
        conversation = cls(
            id=data["id"],
            customer_phone=data["customer_phone"],
            visit_timestamp=datetime.fromisoformat(data["visit_timestamp"]),
            stage=FeedbackStage(data["stage"]),
            template=ConversationTemplate(data["template"]),
            context=data.get("context", {}),
            started_at=datetime.fromisoformat(data["started_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            is_active=data.get("is_active", True),
            metadata=data.get("metadata", {})
        )
        
        # Restore conversation history if available
        history = data.get("conversation_history", [])
        for msg in history:
            if msg["role"] == "human":
                conversation.memory.chat_memory.add_user_message(msg["content"])
            else:
                conversation.memory.chat_memory.add_ai_message(msg["content"])
        
        return conversation


@dataclass
class FeedbackExtractionResult:
    """Result of structured feedback extraction"""
    
    conversation_id: str
    customer_phone: str
    overall_rating: Optional[int] = None
    aspect_ratings: Dict[str, int] = field(default_factory=dict)
    topics_mentioned: List[str] = field(default_factory=list)
    specific_items: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0
    key_feedback: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    would_recommend: Optional[bool] = None
    conversation_length: int = 0
    template_used: str = "default"
    extracted_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "conversation_id": self.conversation_id,
            "customer_phone": self.customer_phone,
            "overall_rating": self.overall_rating,
            "aspect_ratings": self.aspect_ratings,
            "topics_mentioned": self.topics_mentioned,
            "specific_items": self.specific_items,
            "sentiment_score": self.sentiment_score,
            "key_feedback": self.key_feedback,
            "improvement_suggestions": self.improvement_suggestions,
            "would_recommend": self.would_recommend,
            "conversation_length": self.conversation_length,
            "template_used": self.template_used,
            "extracted_at": self.extracted_at.isoformat(),
            "confidence_score": self.confidence_score
        }
    
    def is_negative_feedback(self) -> bool:
        """Check if this represents negative feedback requiring attention"""
        return (
            (self.overall_rating is not None and self.overall_rating <= 2) or
            self.sentiment_score <= -0.5 or
            any("complaint" in item.lower() or "problem" in item.lower() 
                for item in self.key_feedback)
        )
    
    def get_priority_level(self) -> str:
        """Get priority level for alerts"""
        if self.overall_rating is not None and self.overall_rating <= 1:
            return "immediate"
        elif self.sentiment_score <= -0.7:
            return "high"
        elif self.overall_rating is not None and self.overall_rating <= 2:
            return "high"
        elif self.overall_rating == 3 or self.sentiment_score <= -0.3:
            return "medium"
        else:
            return "low"