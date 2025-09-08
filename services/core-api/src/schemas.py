from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

# Enums
class ConversationStatus(str, Enum):
    ACTIVE = "active"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    VIDEO = "video"

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

# Customer schemas
class CustomerBase(BaseSchema):
    phone_number: str = Field(..., min_length=10, max_length=20)
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    language_preference: str = Field("ar", max_length=10)
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    language_preference: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_contact: Optional[datetime] = None
    total_orders: int = 0
    total_spent: int = 0

# Conversation schemas
class ConversationBase(BaseSchema):
    whatsapp_id: str = Field(..., max_length=255)
    status: ConversationStatus = ConversationStatus.ACTIVE
    priority: str = Field("normal", max_length=20)
    assigned_to: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationCreate(ConversationBase):
    customer_id: UUID

class ConversationUpdate(BaseSchema):
    status: Optional[ConversationStatus] = None
    priority: Optional[str] = Field(None, max_length=20)
    assigned_to: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationResponse(ConversationBase):
    id: UUID
    customer_id: UUID
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    customer: Optional[CustomerResponse] = None
    message_count: Optional[int] = 0

# Message schemas
class MessageBase(BaseSchema):
    whatsapp_message_id: str = Field(..., max_length=255)
    direction: MessageDirection
    message_type: MessageType = MessageType.TEXT
    content: str
    media_url: Optional[str] = Field(None, max_length=500)
    timestamp: datetime
    is_read: bool = False
    is_ai_generated: bool = False
    sentiment: Optional[Sentiment] = None
    confidence: Optional[int] = Field(None, ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    conversation_id: UUID

class MessageUpdate(BaseSchema):
    is_read: Optional[bool] = None
    sentiment: Optional[Sentiment] = None
    confidence: Optional[int] = Field(None, ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(MessageBase):
    id: UUID
    conversation_id: UUID
    created_at: datetime

# Prayer Time schemas
class PrayerTimeBase(BaseSchema):
    city: str = Field(..., max_length=100)
    date: datetime
    fajr: datetime
    sunrise: datetime
    dhuhr: datetime
    asr: datetime
    maghrib: datetime
    isha: datetime

class PrayerTimeCreate(PrayerTimeBase):
    pass

class PrayerTimeResponse(PrayerTimeBase):
    id: UUID
    created_at: datetime

class CurrentPrayerResponse(BaseSchema):
    current: Optional[PrayerTimeResponse] = None
    next: Optional[PrayerTimeResponse] = None
    is_prayer_time: bool = False

# Order schemas
class OrderItem(BaseSchema):
    name: str
    quantity: int = Field(..., ge=1)
    price: int = Field(..., ge=0)  # in cents
    notes: Optional[str] = None

class OrderBase(BaseSchema):
    order_number: str = Field(..., max_length=50)
    status: OrderStatus = OrderStatus.PENDING
    total_amount: int = Field(..., ge=0)  # in cents
    items: List[OrderItem]
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class OrderCreate(OrderBase):
    conversation_id: UUID
    customer_id: UUID
    branch_id: Optional[UUID] = None

class OrderUpdate(BaseSchema):
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class OrderResponse(OrderBase):
    id: UUID
    conversation_id: UUID
    customer_id: UUID
    branch_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

# Restaurant schemas
class RestaurantBase(BaseSchema):
    name: str = Field(..., max_length=255)
    phone_number: str = Field(..., min_length=10, max_length=20)
    address: Optional[str] = None
    city: str = Field(..., max_length=100)
    timezone: str = Field("Asia/Riyadh", max_length=50)
    language: str = Field("ar", max_length=10)
    is_active: bool = True
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class RestaurantResponse(RestaurantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# Branch schemas
class BranchBase(BaseSchema):
    name: str = Field(..., max_length=255)
    phone_number: str = Field(..., min_length=10, max_length=20)
    address: Optional[str] = None
    city: str = Field(..., max_length=100)
    is_active: bool = True
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class BranchCreate(BranchBase):
    restaurant_id: UUID

class BranchUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class BranchResponse(BranchBase):
    id: UUID
    restaurant_id: UUID
    created_at: datetime
    updated_at: datetime

# Analytics schemas
class AnalyticsBase(BaseSchema):
    date: datetime
    metric_name: str = Field(..., max_length=100)
    metric_value: int
    restaurant_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None

class AnalyticsCreate(AnalyticsBase):
    pass

class AnalyticsResponse(AnalyticsBase):
    id: UUID
    created_at: datetime

class DashboardAnalytics(BaseSchema):
    total_conversations: int
    active_conversations: int
    resolved_conversations: int
    total_customers: int
    total_orders: int
    total_revenue: int
    average_response_time: float
    satisfaction_score: float
    prayer_time_active: bool

class ConversationAnalytics(BaseSchema):
    period: str
    total_conversations: int
    conversations_by_status: Dict[str, int]
    conversations_by_hour: Dict[str, int]
    average_response_time: float
    satisfaction_trend: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]

# WhatsApp webhook schemas
class WhatsAppWebhookMessage(BaseSchema):
    id: str
    from: str
    timestamp: str
    type: str
    text: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    audio: Optional[Dict[str, str]] = None
    document: Optional[Dict[str, str]] = None
    video: Optional[Dict[str, str]] = None

class WhatsAppWebhookEntry(BaseSchema):
    id: str
    changes: List[Dict[str, Any]]

class WhatsAppWebhook(BaseSchema):
    object: str
    entry: List[WhatsAppWebhookEntry]

# AI Processing schemas
class AIProcessingRequest(BaseSchema):
    message: str
    conversation_id: UUID
    customer_id: UUID
    context: Optional[Dict[str, Any]] = None

class AIProcessingResponse(BaseSchema):
    response: str
    sentiment: Optional[Sentiment] = None
    confidence: Optional[float] = None
    suggested_actions: Optional[List[str]] = None
    is_prayer_time: bool = False
    should_escalate: bool = False

# Feedback Campaign schemas
class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELETED = "deleted"

class RecipientStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    RESPONDED = "responded"
    FAILED = "failed"

class MessageStatus(str, Enum):
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RESPONDED = "responded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CampaignBase(BaseSchema):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    restaurant_id: UUID
    status: CampaignStatus = CampaignStatus.DRAFT
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None

class CampaignResponse(CampaignBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    metrics: Optional[Dict[str, Any]] = None
    recipient_count: Optional[int] = 0

class CampaignMetrics(BaseSchema):
    campaign_id: UUID
    total_recipients: int
    messages_sent: int
    responses_received: int
    response_rate: float
    average_rating: float
    sentiment_distribution: Dict[str, int]
    completion_rate: float
    status_breakdown: Dict[str, int]

class ScheduleParameters(BaseSchema):
    start_time: datetime
    end_time: datetime
    template: Optional[str] = "default"
    batch_size: Optional[int] = Field(100, ge=1, le=1000)
    delay_minutes: Optional[int] = Field(180, ge=120, le=240)  # 2-4 hours

class ExperimentVariant(BaseSchema):
    id: str = Field(..., max_length=50)
    weight: float = Field(..., ge=0, le=1)
    template: str = Field(..., max_length=50)
    parameters: Optional[Dict[str, Any]] = None

class ExperimentConfig(BaseSchema):
    name: str = Field(..., max_length=255)
    variants: List[ExperimentVariant]
    metrics: List[str]
    min_sample_size: int = Field(100, ge=10)

class FeedbackData(BaseSchema):
    campaign_id: Optional[UUID] = None
    campaign_recipient_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    conversation_id: UUID
    customer_phone: str
    restaurant_id: UUID
    rating: Optional[int] = Field(None, ge=1, le=5)
    message: str
    sentiment_score: float = Field(..., ge=-1, le=1)
    topics: List[str] = []
    is_repeated_issue: bool = False
    metadata: Optional[Dict[str, Any]] = None