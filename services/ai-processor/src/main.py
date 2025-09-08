from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("AI Processor service starting up...")
    yield
    # Shutdown
    print("AI Processor service shutting down...")

app = FastAPI(
    title="CRM-RES AI Processor",
    description="AI processing service for restaurant CRM system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"service": "AI Processor", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-processor",
        "version": "1.0.0"
    }

@app.get("/api/v1/process")
async def process_message():
    # Future implementation for message processing
    return {"message": "AI processing endpoint - coming soon"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        reload=True
    )