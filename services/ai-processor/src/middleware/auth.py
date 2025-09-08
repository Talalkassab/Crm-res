from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

security = HTTPBearer()

class AuthMiddleware:
    """Authentication middleware for AI processor endpoints."""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.public_endpoints = {"/health", "/docs", "/redoc", "/openapi.json"}
    
    def _load_api_keys(self) -> set:
        """Load API keys from environment."""
        api_keys_str = os.getenv("AI_PROCESSOR_API_KEYS", "")
        if not api_keys_str:
            # For development, use a default key
            return {"dev-api-key-change-in-production"}
        
        return set(key.strip() for key in api_keys_str.split(",") if key.strip())
    
    async def verify_api_key(
        self, 
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
    ) -> str:
        """Verify API key from request."""
        
        # Skip authentication for public endpoints
        if request.url.path in self.public_endpoints:
            return "public"
        
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        api_key = credentials.credentials
        
        if api_key not in self.api_keys:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return api_key

# Global auth middleware instance
auth_middleware = AuthMiddleware()