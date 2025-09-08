"""
Rate limiting middleware for API endpoints
Prevents abuse and ensures fair usage
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import time
import redis
import json
from datetime import datetime, timedelta
import hashlib

class RateLimiter:
    """Redis-based rate limiter with configurable limits per endpoint"""
    
    def __init__(self, redis_url: str = "redis://redis:6379/1"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Rate limit configurations per endpoint pattern
        self.limits = {
            # CSV upload endpoints - more restrictive
            "/api/feedback-campaigns/upload": {
                "requests": 5,
                "window": 3600,  # 5 uploads per hour
                "burst": 2,      # Allow 2 rapid uploads
                "burst_window": 300  # within 5 minutes
            },
            
            # Campaign management - moderate limits
            "/api/feedback-campaigns": {
                "requests": 100,
                "window": 3600,  # 100 requests per hour
                "burst": 20,
                "burst_window": 60
            },
            
            # Campaign scheduling - more restrictive
            "/api/feedback-campaigns/*/schedule": {
                "requests": 10,
                "window": 3600,  # 10 schedules per hour
                "burst": 3,
                "burst_window": 300
            },
            
            # Default limits for other endpoints
            "default": {
                "requests": 1000,
                "window": 3600,  # 1000 requests per hour
                "burst": 100,
                "burst_window": 60
            }
        }
    
    def get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for client (user_id or IP)"""
        # Try to get authenticated user ID first
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host
        
        return f"ip:{client_ip}"
    
    def get_endpoint_pattern(self, path: str) -> str:
        """Match request path to configured endpoint pattern"""
        # Direct match first
        if path in self.limits:
            return path
        
        # Pattern matching for parameterized routes
        for pattern in self.limits:
            if "*" in pattern:
                # Simple wildcard matching
                pattern_parts = pattern.split("*")
                if len(pattern_parts) == 2:
                    prefix, suffix = pattern_parts
                    if path.startswith(prefix) and path.endswith(suffix):
                        return pattern
        
        return "default"
    
    def check_rate_limit(self, request: Request) -> Optional[Dict]:
        """
        Check if request should be rate limited
        Returns None if allowed, error info if limited
        """
        client_id = self.get_client_identifier(request)
        endpoint_pattern = self.get_endpoint_pattern(request.url.path)
        limits = self.limits[endpoint_pattern]
        
        current_time = int(time.time())
        
        # Check main rate limit
        main_key = f"rate_limit:{endpoint_pattern}:{client_id}"
        main_count = self._check_window(main_key, limits["requests"], limits["window"], current_time)
        
        if main_count > limits["requests"]:
            reset_time = current_time + limits["window"]
            return {
                "error": "Rate limit exceeded",
                "limit": limits["requests"],
                "window": limits["window"],
                "current": main_count,
                "reset_time": reset_time,
                "retry_after": limits["window"]
            }
        
        # Check burst limit
        burst_key = f"burst_limit:{endpoint_pattern}:{client_id}"
        burst_count = self._check_window(burst_key, limits["burst"], limits["burst_window"], current_time)
        
        if burst_count > limits["burst"]:
            reset_time = current_time + limits["burst_window"]
            return {
                "error": "Burst limit exceeded",
                "limit": limits["burst"],
                "window": limits["burst_window"],
                "current": burst_count,
                "reset_time": reset_time,
                "retry_after": limits["burst_window"]
            }
        
        # Request is allowed
        return None
    
    def _check_window(self, key: str, limit: int, window: int, current_time: int) -> int:
        """Check and update sliding window counter"""
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            expire_time = current_time - window
            pipe.zremrangebyscore(key, 0, expire_time)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Count requests in window
            pipe.zcard(key)
            
            # Set expiry on key
            pipe.expire(key, window + 60)  # Extra buffer for cleanup
            
            results = pipe.execute()
            return results[2]  # Count from zcard
            
        except redis.RedisError as e:
            # If Redis fails, allow the request but log the error
            print(f"Rate limiter Redis error: {e}")
            return 0
    
    def get_rate_limit_headers(self, request: Request) -> Dict[str, str]:
        """Get rate limit headers for response"""
        client_id = self.get_client_identifier(request)
        endpoint_pattern = self.get_endpoint_pattern(request.url.path)
        limits = self.limits[endpoint_pattern]
        
        current_time = int(time.time())
        main_key = f"rate_limit:{endpoint_pattern}:{client_id}"
        
        try:
            current_count = self.redis_client.zcard(main_key)
            remaining = max(0, limits["requests"] - current_count)
            reset_time = current_time + limits["window"]
            
            return {
                "X-RateLimit-Limit": str(limits["requests"]),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "X-RateLimit-Window": str(limits["window"])
            }
        except redis.RedisError:
            # Return default headers if Redis fails
            return {
                "X-RateLimit-Limit": str(limits["requests"]),
                "X-RateLimit-Remaining": str(limits["requests"]),
                "X-RateLimit-Reset": str(current_time + limits["window"]),
                "X-RateLimit-Window": str(limits["window"])
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    
    # Skip rate limiting for health checks and internal calls
    if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
        response = await call_next(request)
        return response
    
    # Check rate limit
    limit_info = rate_limiter.check_rate_limit(request)
    
    if limit_info:
        # Rate limit exceeded
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": limit_info["error"],
                "limit": limit_info["limit"],
                "window_seconds": limit_info["window"],
                "current_usage": limit_info["current"],
                "retry_after_seconds": limit_info["retry_after"],
                "reset_time": datetime.fromtimestamp(limit_info["reset_time"]).isoformat()
            },
            headers={
                "Retry-After": str(limit_info["retry_after"]),
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(limit_info["reset_time"])
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to response
    headers = rate_limiter.get_rate_limit_headers(request)
    for key, value in headers.items():
        response.headers[key] = value
    
    return response

def create_rate_limit_decorator(requests: int, window: int):
    """Decorator for applying custom rate limits to specific endpoints"""
    def decorator(func):
        func._rate_limit = {"requests": requests, "window": window}
        return func
    return decorator

# Decorators for common use cases
strict_rate_limit = create_rate_limit_decorator(5, 3600)      # 5 per hour
moderate_rate_limit = create_rate_limit_decorator(100, 3600)  # 100 per hour
loose_rate_limit = create_rate_limit_decorator(1000, 3600)    # 1000 per hour