from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv
from src.api import webhook, monitoring, rate_limit
from src.middleware.rate_limiter import RateLimitMiddleware
from src.utils.error_handler import global_exception_handler
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WhatsApp Gateway service starting up...")
    yield
    logger.info("WhatsApp Gateway service shutting down...")

app = FastAPI(
    title="WhatsApp Gateway Service",
    description="Service for handling WhatsApp Business API integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "whatsapp-gateway",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "WhatsApp Gateway Service"}

app.include_router(webhook.router)
app.include_router(monitoring.router)
app.include_router(rate_limit.router)

app.add_exception_handler(Exception, global_exception_handler)