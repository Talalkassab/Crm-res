import os
from typing import Optional
from pydantic import BaseModel

class AIProcessorConfig(BaseModel):
    """Configuration for AI Processor service."""
    
    # OpenRouter API Configuration
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    primary_model: str = "google/gemini-flash-1.5"
    fallback_models: list = [
        "anthropic/claude-3-haiku-20240307",
        "meta-llama/llama-3.1-70b-instruct"
    ]
    
    # Prayer Times API Configuration
    prayer_times_base_url: str = "https://api.aladhan.com/v1"
    prayer_buffer_minutes: int = 10
    
    # Redis Configuration (for caching)
    redis_url: Optional[str] = None
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # Service Configuration
    service_port: int = 8001
    log_level: str = "INFO"
    environment: str = "development"
    
    # AI Processing Configuration
    default_temperature: float = 0.7
    max_tokens: int = 1000
    conversation_context_limit: int = 10  # Number of previous messages to include
    
    # Sentiment Analysis Configuration
    sentiment_confidence_threshold: float = 0.7
    escalation_threshold: float = 0.8
    
    class Config:
        env_prefix = "AI_PROCESSOR_"

def get_config() -> AIProcessorConfig:
    """Get configuration from environment variables."""
    
    # Required environment variables
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    
    return AIProcessorConfig(
        # OpenRouter Configuration
        openrouter_api_key=openrouter_api_key,
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        primary_model=os.getenv("PRIMARY_AI_MODEL", "google/gemini-flash-1.5"),
        
        # Service Configuration  
        service_port=int(os.getenv("AI_PROCESSOR_PORT", "8001")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        environment=os.getenv("ENVIRONMENT", "development"),
        
        # Database Configuration
        database_url=os.getenv("DATABASE_URL"),
        redis_url=os.getenv("REDIS_URL"),
        
        # Prayer Times Configuration
        prayer_buffer_minutes=int(os.getenv("PRAYER_BUFFER_MINUTES", "10")),
        
        # AI Processing Configuration
        default_temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("AI_MAX_TOKENS", "1000")),
        conversation_context_limit=int(os.getenv("CONVERSATION_CONTEXT_LIMIT", "10")),
        
        # Sentiment Analysis Configuration
        sentiment_confidence_threshold=float(os.getenv("SENTIMENT_CONFIDENCE_THRESHOLD", "0.7")),
        escalation_threshold=float(os.getenv("ESCALATION_THRESHOLD", "0.8"))
    )