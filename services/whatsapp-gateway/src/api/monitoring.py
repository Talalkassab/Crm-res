from fastapi import APIRouter
from src.services.queue import get_queue_health

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/queue/health")
async def queue_health():
    return get_queue_health()