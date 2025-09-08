import time
import logging
import redis
from typing import Optional, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.config import config

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(
        self,
        redis_url: str = None,
        business_rate_limit: int = 80,
        user_rate_limit: int = 1000,
        window_seconds: int = 1
    ):
        self.redis_url = redis_url or config.REDIS_URL
        self.redis_client = redis.from_url(self.redis_url)
        self.business_rate_limit = business_rate_limit
        self.user_rate_limit = user_rate_limit
        self.window_seconds = window_seconds
    
    def _get_key(self, identifier: str, message_type: str) -> str:
        timestamp = int(time.time() / self.window_seconds)
        return f"rate_limit:{message_type}:{identifier}:{timestamp}"
    
    def _get_limit(self, is_user_initiated: bool) -> int:
        return self.user_rate_limit if is_user_initiated else self.business_rate_limit
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        is_user_initiated: bool = False
    ) -> Tuple[bool, Optional[int]]:
        try:
            message_type = "user" if is_user_initiated else "business"
            key = self._get_key(identifier, message_type)
            limit = self._get_limit(is_user_initiated)
            
            pipeline = self.redis_client.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, self.window_seconds * 2)
            results = pipeline.execute()
            
            current_count = results[0]
            
            if current_count > limit:
                logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{limit} ({message_type})")
                return False, current_count
            
            return True, current_count
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True, None
    
    async def wait_if_needed(
        self, 
        identifier: str, 
        is_user_initiated: bool = False
    ) -> float:
        allowed, count = await self.check_rate_limit(identifier, is_user_initiated)
        
        if not allowed:
            wait_time = self.window_seconds
            logger.info(f"Rate limited - waiting {wait_time}s for {identifier}")
            time.sleep(wait_time)
            return wait_time
        
        return 0
    
    def get_usage_stats(self, identifier: str) -> dict:
        try:
            timestamp = int(time.time() / self.window_seconds)
            
            business_key = f"rate_limit:business:{identifier}:{timestamp}"
            user_key = f"rate_limit:user:{identifier}:{timestamp}"
            
            business_count = self.redis_client.get(business_key) or 0
            user_count = self.redis_client.get(user_key) or 0
            
            if isinstance(business_count, bytes):
                business_count = int(business_count)
            if isinstance(user_count, bytes):
                user_count = int(user_count)
            
            return {
                "business": {
                    "current": business_count,
                    "limit": self.business_rate_limit,
                    "remaining": max(0, self.business_rate_limit - business_count)
                },
                "user": {
                    "current": user_count,
                    "limit": self.user_rate_limit,
                    "remaining": max(0, self.user_rate_limit - user_count)
                },
                "window_seconds": self.window_seconds
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter: RateLimiter = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/webhook"):
            identifier = request.client.host if request.client else "unknown"
            
            is_user_initiated = request.method == "POST"
            
            allowed, count = await self.rate_limiter.check_rate_limit(
                identifier, 
                is_user_initiated
            )
            
            if not allowed:
                limit = self.rate_limiter._get_limit(is_user_initiated)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {count}/{limit} requests",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + self.rate_limiter.window_seconds)
                    }
                )
        
        response = await call_next(request)
        return response

rate_limiter_instance = RateLimiter()