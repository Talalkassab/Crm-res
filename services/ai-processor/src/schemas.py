from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class SentimentType(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

class PersonalityType(str, Enum):
    formal = "formal"
    casual = "casual"
    traditional = "traditional"
    modern = "modern"

class DialectType(str, Enum):
    saudi = "ar-SA"
    egyptian = "ar-EG"
    levantine = "ar-LV"
    english = "en"

class ConversationContext(BaseModel):
    personality: PersonalityType = PersonalityType.formal
    dialect: DialectType = DialectType.saudi
    sentiment_history: List[str] = Field(default_factory=list)
    topics_discussed: List[str] = Field(default_factory=list)
    escalation_triggers: List[str] = Field(default_factory=list)
    cultural_context: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str] = None
    customer_id: Optional[str] = None

class AIProcessingRequest(BaseModel):
    message: str = Field(..., description="The message to process")
    conversation_id: str = Field(..., description="Conversation ID")
    customer_id: str = Field(..., description="Customer ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    restaurant_id: Optional[str] = None
    language_preference: Optional[str] = "ar-SA"

class AIProcessingResponse(BaseModel):
    response: str = Field(..., description="Generated response")
    sentiment: str = Field(..., description="Detected sentiment")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    suggested_actions: List[str] = Field(default_factory=list)
    is_prayer_time: bool = False
    should_escalate: bool = False
    dialect_detected: Optional[str] = None
    cultural_phrases_used: List[str] = Field(default_factory=list)

class WhatsAppWebhook(BaseModel):
    object: str
    entry: List[Dict[str, Any]]

class SentimentAnalysisResult(BaseModel):
    sentiment: SentimentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    negative_indicators: List[str] = Field(default_factory=list)
    positive_indicators: List[str] = Field(default_factory=list)
    escalation_needed: bool = False

class PrayerTimeStatus(BaseModel):
    is_prayer_time: bool
    current_prayer: Optional[str] = None
    next_prayer: Optional[str] = None
    time_until_next: Optional[int] = None  # minutes
    city: str = "Riyadh"

class OpenRouterRequest(BaseModel):
    model: str = "google/gemini-flash-1.5"
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: Optional[int] = 1000
    stream: bool = False

class OpenRouterResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class ArabicProcessingResult(BaseModel):
    original_text: str
    processed_text: str
    dialect_detected: DialectType
    cultural_phrases: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)