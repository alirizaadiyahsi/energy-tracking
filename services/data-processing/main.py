import logging
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.routes import router
from celery_app import celery_app
from core.config import settings
from core.database import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Energy Tracking - Data Processing Service",
    description="Service for processing and analyzing energy data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-processing", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    logger.info("Starting Data Processing Service...")
    await init_db()
    logger.info("Data Processing Service started successfully")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
