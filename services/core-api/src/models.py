from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    language_preference = Column(String(10), default="ar")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contact = Column(DateTime, nullable=True)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)  # in cents
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="customer")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    whatsapp_id = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), default="active")  # active, waiting, resolved, closed
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    assigned_to = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    tags = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    whatsapp_message_id = Column(String(255), unique=True, nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # inbound, outbound
    message_type = Column(String(20), default="text")  # text, image, audio, document, etc.
    content = Column(Text, nullable=False)
    media_url = Column(String(500), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    is_ai_generated = Column(Boolean, default=False)
    sentiment = Column(String(20), nullable=True)  # positive, neutral, negative
    confidence = Column(Integer, nullable=True)  # AI confidence score
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class PrayerTime(Base):
    __tablename__ = "prayer_times"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    fajr = Column(DateTime, nullable=False)
    sunrise = Column(DateTime, nullable=False)
    dhuhr = Column(DateTime, nullable=False)
    asr = Column(DateTime, nullable=False)
    maghrib = Column(DateTime, nullable=False)
    isha = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for efficient queries
    __table_args__ = (
        {"extend_existing": True}
    )

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=False)
    timezone = Column(String(50), default="Asia/Riyadh")
    language = Column(String(10), default="ar")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)

class Branch(Base):
    __tablename__ = "branches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    restaurant = relationship("Restaurant")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), default="pending")  # pending, confirmed, preparing, ready, delivered, cancelled
    total_amount = Column(Integer, nullable=False)  # in cents
    items = Column(JSON, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation")
    customer = relationship("Customer")
    branch = relationship("Branch")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Integer, nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant")
    branch = relationship("Branch")