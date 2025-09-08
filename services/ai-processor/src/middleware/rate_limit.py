from fastapi import HTTPException, Request
from typing import Dict, Any
import time
import asyncio
from collections import defaultdict

class RateLimitMiddleware:
    """Rate limiting middleware to prevent API abuse."""
    
    def __init__(self):
        # Store request counts per client
        self.clients: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "requests": 0,
            "window_start": time.time(),
            "blocked_until": 0
        })
        
        # Rate limits per endpoint
        self.rate_limits = {
            "/api/process-message": {"requests": 30, "window": 60},  # 30 requests per minute
            "/api/generate-response": {"requests": 20, "window": 60},  # 20 requests per minute
            "/api/analyze-sentiment": {"requests": 100, "window": 60},  # 100 requests per minute
            "/api/models": {"requests": 10, "window": 60},  # 10 requests per minute
            "default": {"requests": 50, "window": 60}  # Default: 50 requests per minute
        }
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use X-Forwarded-For if behind proxy, otherwise client IP
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Include API key in client ID if available
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            api_key_suffix = auth_header[-8:]  # Last 8 chars for identification
            return f"{client_ip}:{api_key_suffix}"
        
        return client_ip
    
    def _get_rate_limit_for_endpoint(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for specific endpoint."""
        return self.rate_limits.get(path, self.rate_limits["default"])
    
    async def check_rate_limit(self, request: Request) -> None:
        """Check if request should be rate limited."""
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Get rate limit for this endpoint
        rate_limit = self._get_rate_limit_for_endpoint(request.url.path)
        max_requests = rate_limit["requests"]
        window_seconds = rate_limit["window"]
        
        client_data = self.clients[client_id]
        
        # Check if client is currently blocked
        if client_data["blocked_until"] > current_time:
            remaining_block = int(client_data["blocked_until"] - current_time)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {remaining_block} seconds",
                headers={
                    "Retry-After": str(remaining_block),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(client_data["blocked_until"]))
                }
            )
        
        # Reset window if it's expired
        if current_time - client_data["window_start"] >= window_seconds:
            client_data["requests"] = 0
            client_data["window_start"] = current_time
            client_data["blocked_until"] = 0
        
        # Check if client has exceeded rate limit
        if client_data["requests"] >= max_requests:
            # Block client for the remaining window time
            window_remaining = window_seconds - (current_time - client_data["window_start"])
            block_time = max(window_remaining, 60)  # Block for at least 1 minute
            client_data["blocked_until"] = current_time + block_time
            
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds",
                headers={
                    "Retry-After": str(int(block_time)),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(client_data["blocked_until"]))
                }
            )
        
        # Increment request count
        client_data["requests"] += 1
        
        # Add rate limit headers
        remaining = max_requests - client_data["requests"]
        reset_time = int(client_data["window_start"] + window_seconds)
        
        # Store headers for response (FastAPI will handle adding them)
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }
    
    def cleanup_expired_clients(self) -> None:
        """Clean up expired client data to prevent memory leaks."""
        current_time = time.time()
        expired_clients = []
        
        for client_id, client_data in self.clients.items():
            # Remove clients that haven't made requests in the last hour
            if current_time - client_data["window_start"] > 3600:
                expired_clients.append(client_id)
        
        for client_id in expired_clients:
            del self.clients[client_id]
    
    async def start_cleanup_task(self):
        """Start periodic cleanup task."""
        while True:
            await asyncio.sleep(300)  # Clean up every 5 minutes
            self.cleanup_expired_clients()

# Global rate limit middleware instance
rate_limit_middleware = RateLimitMiddleware()