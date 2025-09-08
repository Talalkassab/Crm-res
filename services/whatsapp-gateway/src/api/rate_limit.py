from fastapi import APIRouter, HTTPException
from src.middleware.rate_limiter import rate_limiter_instance

router = APIRouter(prefix="/rate-limit", tags=["rate-limit"])

@router.get("/stats/{phone_number}")
async def get_rate_limit_stats(phone_number: str):
    stats = rate_limiter_instance.get_usage_stats(phone_number)
    
    if not stats:
        raise HTTPException(status_code=500, detail="Unable to retrieve rate limit stats")
    
    return stats

@router.get("/health")
async def rate_limiter_health():
    try:
        test_stats = rate_limiter_instance.get_usage_stats("health_check")
        return {
            "status": "healthy",
            "redis_connected": bool(test_stats),
            "business_limit": rate_limiter_instance.business_rate_limit,
            "user_limit": rate_limiter_instance.user_rate_limit,
            "window_seconds": rate_limiter_instance.window_seconds
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }