"""
Analytics Service
Generates reports and insights from feedback data
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from datetime import datetime
import logging

from .api.reports import router as reports_router
from .processors.feedback_aggregator import FeedbackAggregator
from .generators.insight_generator import InsightGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Analytics Service starting up...")
    
    # Initialize services
    app.state.feedback_aggregator = FeedbackAggregator()
    app.state.insight_generator = InsightGenerator()
    
    yield
    
    logger.info("Analytics Service shutting down...")


app = FastAPI(
    title="CRM Analytics Service",
    description="Analytics and reporting service for feedback data",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reports_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CRM Analytics Service",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "feedback_aggregator": "operational",
            "insight_generator": "operational"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    )