from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from .agents.message_processor import MessageProcessor
from .services.sentiment_analyzer import SentimentAnalyzer
from .services.prayer_time_service import PrayerTimeService
from .services.arabic_processor import ArabicProcessor
from .services.openrouter_service import OpenRouterService
from .middleware.auth import auth_middleware
from .middleware.rate_limit import rate_limit_middleware
from .schemas import (
    AIProcessingRequest,
    AIProcessingResponse,
    WhatsAppWebhook,
    ConversationContext
)

# Global service instances (initialized during startup)
message_processor = None
sentiment_analyzer = None
prayer_time_service = None
arabic_processor = None
openrouter_service = None

async def initialize_services():
    """Initialize all services with proper error handling."""
    global message_processor, sentiment_analyzer, prayer_time_service, arabic_processor, openrouter_service
    
    try:
        print("🔧 Initializing AI processing services...")
        
        # Initialize core services
        sentiment_analyzer = SentimentAnalyzer()
        prayer_time_service = PrayerTimeService()
        arabic_processor = ArabicProcessor()
        openrouter_service = OpenRouterService()
        
        # Initialize main message processor (depends on other services)
        message_processor = MessageProcessor()
        
        # Start background tasks
        asyncio.create_task(rate_limit_middleware.start_cleanup_task())
        
        print("✅ All services initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🤖 Starting CRM-RES AI Processor...")
    
    # Initialize services
    if not await initialize_services():
        print("💥 Service initialization failed - shutting down")
        exit(1)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down CRM-RES AI Processor...")
    
    # Clean up async clients
    if openrouter_service and hasattr(openrouter_service, 'client'):
        await openrouter_service.client.aclose()
    if prayer_time_service and hasattr(prayer_time_service, 'client'):
        await prayer_time_service.client.aclose()

app = FastAPI(
    title="CRM-RES AI Processor",
    description="AI processing service for WhatsApp conversations with Arabic support",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Add rate limiting and authentication middleware
@app.middleware("http")
async def rate_limit_and_auth_middleware(request: Request, call_next):
    """Combined middleware for rate limiting and authentication."""
    
    # Apply rate limiting
    await rate_limit_middleware.check_rate_limit(request)
    
    # Apply authentication (skip for public endpoints)
    if request.url.path not in {"/health", "/docs", "/redoc", "/openapi.json"}:
        await auth_middleware.verify_api_key(request)
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers if available
    if hasattr(request.state, "rate_limit_headers"):
        for header, value in request.state.rate_limit_headers.items():
            response.headers[header] = value
    
    return response

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai-processor"
    }

@app.post("/api/process-message", response_model=AIProcessingResponse)
async def process_message(request: AIProcessingRequest):
    """
    Process an incoming WhatsApp message and generate an appropriate response
    """
    if not message_processor:
        raise HTTPException(status_code=503, detail="Message processor not initialized")
    
    try:
        return await message_processor.process_message(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@app.post("/api/analyze-sentiment")
async def analyze_sentiment(text: str, language: str = "ar"):
    """
    Analyze sentiment of a given text
    """
    if not sentiment_analyzer or not arabic_processor:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        processed_text = arabic_processor.preprocess(text)
        result = await sentiment_analyzer.analyze(processed_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze sentiment: {str(e)}")

@app.post("/api/translate")
async def translate_text(text: str, target_language: str = "ar"):
    """
    Translate text to target language
    """
    if not arabic_processor:
        raise HTTPException(status_code=503, detail="Arabic processor not initialized")
    
    try:
        result = await arabic_processor.translate(text, target_language)
        return {"translated_text": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to translate text: {str(e)}")

@app.post("/api/generate-response")
async def generate_response(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    language: str = "ar"
):
    """
    Generate a response for a given message
    """
    if not arabic_processor or not openrouter_service:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        processed_message = arabic_processor.preprocess(message)
        response = await openrouter_service.generate_response(
            message=processed_message,
            context=context,
            language=language
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

@app.get("/api/prayer-status")
async def get_prayer_status(city: str = "Riyadh"):
    """
    Check if it's currently prayer time
    """
    if not prayer_time_service:
        raise HTTPException(status_code=503, detail="Prayer time service not initialized")
    
    try:
        is_prayer_time = await prayer_time_service.is_prayer_time(city)
        current_prayer = await prayer_time_service.get_current_prayer(city)
        next_prayer = await prayer_time_service.get_next_prayer(city)
        
        return {
            "is_prayer_time": is_prayer_time,
            "current_prayer": current_prayer,
            "next_prayer": next_prayer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prayer status: {str(e)}")

@app.post("/api/process-whatsapp-webhook")
async def process_whatsapp_webhook(webhook: WhatsAppWebhook):
    """
    Process incoming WhatsApp webhook
    """
    try:
        # Extract message from webhook
        for entry in webhook.entry:
            for change in entry.get("changes", []):
                if change.get("field") == "messages":
                    messages = change.get("value", {}).get("messages", [])
                    
                    for message in messages:
                        # Process each message
                        message_text = message.get("text", {}).get("body", "")
                        from_number = message.get("from", "")
                        message_id = message.get("id", "")
                        
                        if message_text:
                            # Process the message
                            result = await process_message(AIProcessingRequest(
                                message=message_text,
                                conversation_id="",  # Will be set by core API
                                customer_id="",  # Will be set by core API
                                context={"from": from_number, "message_id": message_id}
                            ))
                            
                            return {
                                "processed": True,
                                "response": result.response,
                                "sentiment": result.sentiment,
                                "should_escalate": result.should_escalate
                            }
        
        return {"processed": False, "message": "No messages found in webhook"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")

@app.get("/api/models")
async def get_available_models():
    """
    Get list of available AI models
    """
    if not openrouter_service:
        raise HTTPException(status_code=503, detail="OpenRouter service not initialized")
    
    try:
        models = await openrouter_service.get_available_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/api/switch-model")
async def switch_model(model_name: str):
    """
    Switch to a different AI model
    """
    if not openrouter_service:
        raise HTTPException(status_code=503, detail="OpenRouter service not initialized")
    
    try:
        success = await openrouter_service.switch_model(model_name)
        if success:
            return {"message": f"Switched to model: {model_name}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to switch model")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )