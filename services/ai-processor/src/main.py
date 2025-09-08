from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from .services.openrouter_service import OpenRouterService
from .services.sentiment_analyzer import SentimentAnalyzer
from .services.prayer_time_service import PrayerTimeService
from .services.arabic_processor import ArabicProcessor
from .schemas import (
    AIProcessingRequest,
    AIProcessingResponse,
    WhatsAppWebhook,
    ConversationContext
)

# Global services
openrouter_service = OpenRouterService()
sentiment_analyzer = SentimentAnalyzer()
prayer_time_service = PrayerTimeService()
arabic_processor = ArabicProcessor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🤖 Starting CRM-RES AI Processor...")
    yield
    # Shutdown
    print("🛑 Shutting down CRM-RES AI Processor...")

app = FastAPI(
    title="CRM-RES AI Processor",
    description="AI processing service for WhatsApp conversations with Arabic support",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        # Check if it's prayer time
        is_prayer_time = await prayer_time_service.is_prayer_time("Riyadh")
        
        if is_prayer_time:
            return AIProcessingResponse(
                response="نعتذر، نحن متوقفون مؤقتاً أثناء أوقات الصلاة. سنعود قريباً!",
                sentiment="neutral",
                confidence=1.0,
                suggested_actions=["pause_conversation"],
                is_prayer_time=True,
                should_escalate=False
            )
        
        # Process Arabic text
        processed_text = arabic_processor.preprocess(request.message)
        
        # Analyze sentiment
        sentiment_result = await sentiment_analyzer.analyze(processed_text)
        
        # Generate response using OpenRouter
        response = await openrouter_service.generate_response(
            message=processed_text,
            context=request.context,
            sentiment=sentiment_result.get("sentiment"),
            language="ar"
        )
        
        # Determine if escalation is needed
        should_escalate = (
            sentiment_result.get("sentiment") == "negative" and 
            sentiment_result.get("confidence", 0) > 0.8
        )
        
        # Generate suggested actions
        suggested_actions = []
        if sentiment_result.get("sentiment") == "negative":
            suggested_actions.append("escalate_to_human")
        if "order" in processed_text.lower() or "طلب" in processed_text:
            suggested_actions.append("process_order")
        if "reservation" in processed_text.lower() or "حجز" in processed_text:
            suggested_actions.append("process_reservation")
        
        return AIProcessingResponse(
            response=response,
            sentiment=sentiment_result.get("sentiment"),
            confidence=sentiment_result.get("confidence"),
            suggested_actions=suggested_actions,
            is_prayer_time=False,
            should_escalate=should_escalate
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@app.post("/api/analyze-sentiment")
async def analyze_sentiment(text: str, language: str = "ar"):
    """
    Analyze sentiment of a given text
    """
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