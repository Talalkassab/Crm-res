from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from typing import List, Optional
from datetime import datetime, timedelta

from .database import get_db
from .models import Conversation, Customer, Message, PrayerTime
from .schemas import (
    ConversationResponse,
    CustomerResponse,
    MessageResponse,
    PrayerTimeResponse,
    ConversationCreate,
    MessageCreate,
    CustomerCreate
)
from .services.prayer_service import PrayerTimeService
from .services.conversation_service import ConversationService
from .services.customer_service import CustomerService

# Global services
prayer_service = PrayerTimeService()
conversation_service = ConversationService()
customer_service = CustomerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting CRM-RES Core API...")
    yield
    # Shutdown
    print("🛑 Shutting down CRM-RES Core API...")

app = FastAPI(
    title="CRM-RES Core API",
    description="Core API service for restaurant CRM with WhatsApp integration",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app"]
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "core-api"
    }

# Prayer Times endpoints
@app.get("/api/prayer-times", response_model=List[PrayerTimeResponse])
async def get_prayer_times(city: str = "Riyadh"):
    """Get prayer times for a specific city"""
    try:
        prayer_times = await prayer_service.get_prayer_times(city)
        return prayer_times
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prayer times: {str(e)}")

@app.get("/api/prayer-times/current")
async def get_current_prayer_time(city: str = "Riyadh"):
    """Get current prayer time and next prayer"""
    try:
        current_prayer = await prayer_service.get_current_prayer(city)
        next_prayer = await prayer_service.get_next_prayer(city)
        return {
            "current": current_prayer,
            "next": next_prayer,
            "is_prayer_time": await prayer_service.is_prayer_time(city)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current prayer time: {str(e)}")

# Conversations endpoints
@app.get("/api/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db=Depends(get_db)
):
    """Get all conversations with optional filtering"""
    try:
        conversations = await conversation_service.get_conversations(
            db, skip=skip, limit=limit, status=status
        )
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, db=Depends(get_db)):
    """Get a specific conversation by ID"""
    try:
        conversation = await conversation_service.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@app.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db=Depends(get_db)
):
    """Create a new conversation"""
    try:
        new_conversation = await conversation_service.create_conversation(db, conversation)
        return new_conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

# Messages endpoints
@app.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """Get messages for a specific conversation"""
    try:
        messages = await conversation_service.get_messages(
            db, conversation_id, skip=skip, limit=limit
        )
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@app.post("/api/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(
    conversation_id: str,
    message: MessageCreate,
    db=Depends(get_db)
):
    """Create a new message in a conversation"""
    try:
        new_message = await conversation_service.create_message(db, conversation_id, message)
        return new_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")

# Customers endpoints
@app.get("/api/customers", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """Get all customers"""
    try:
        customers = await customer_service.get_customers(db, skip=skip, limit=limit)
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customers: {str(e)}")

@app.get("/api/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, db=Depends(get_db)):
    """Get a specific customer by ID"""
    try:
        customer = await customer_service.get_customer(db, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")

@app.post("/api/customers", response_model=CustomerResponse)
async def create_customer(
    customer: CustomerCreate,
    db=Depends(get_db)
):
    """Create a new customer"""
    try:
        new_customer = await customer_service.create_customer(db, customer)
        return new_customer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")

# Analytics endpoints
@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics(db=Depends(get_db)):
    """Get dashboard analytics data"""
    try:
        analytics = await conversation_service.get_dashboard_analytics(db)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@app.get("/api/analytics/conversations")
async def get_conversation_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db=Depends(get_db)
):
    """Get conversation analytics for a date range"""
    try:
        analytics = await conversation_service.get_conversation_analytics(
            db, start_date, end_date
        )
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation analytics: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )