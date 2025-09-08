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
    print("Core API service starting up...")
    yield
    # Shutdown
    print("Core API service shutting down...")

app = FastAPI(
    title="CRM-RES Core API",
    description="Core API service for restaurant CRM system",
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
    return {"service": "Core API", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "core-api",
        "version": "1.0.0"
    }

@app.get("/api/v1/restaurants")
async def get_restaurants():
    # Future implementation for restaurants
    return {"restaurants": []}

@app.get("/api/v1/conversations")
async def get_conversations():
    # Future implementation for conversations
    return {"conversations": []}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )