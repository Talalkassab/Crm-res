import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.WHATSAPP_WEBHOOK_SECRET = os.getenv("WHATSAPP_WEBHOOK_SECRET", "")
        self.WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
        self.WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v19.0")
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Validate critical configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate critical configuration values on startup"""
        missing_vars: List[str] = []
        
        if not self.WHATSAPP_WEBHOOK_SECRET:
            missing_vars.append("WHATSAPP_WEBHOOK_SECRET")
        if not self.WHATSAPP_ACCESS_TOKEN:
            missing_vars.append("WHATSAPP_ACCESS_TOKEN")
        if not self.WHATSAPP_PHONE_NUMBER_ID:
            missing_vars.append("WHATSAPP_PHONE_NUMBER_ID")
        if not self.SUPABASE_URL:
            missing_vars.append("SUPABASE_URL")
        if not self.SUPABASE_ANON_KEY:
            missing_vars.append("SUPABASE_ANON_KEY")
            
        if missing_vars:
            logger.warning(f"Missing critical environment variables: {', '.join(missing_vars)}")
            logger.warning("Service may not function properly without these variables")
        
    @property
    def whatsapp_api_url(self) -> str:
        return f"https://graph.facebook.com/{self.WHATSAPP_API_VERSION}/{self.WHATSAPP_PHONE_NUMBER_ID}"
    
    @property
    def is_production_ready(self) -> bool:
        """Check if all required configuration is present for production"""
        return all([
            self.WHATSAPP_WEBHOOK_SECRET,
            self.WHATSAPP_ACCESS_TOKEN,
            self.WHATSAPP_PHONE_NUMBER_ID,
            self.SUPABASE_URL,
            self.SUPABASE_ANON_KEY
        ])

config = Config()