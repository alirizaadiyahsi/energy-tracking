import logging
import os
import sys
import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.routes import router
from celery_app import celery_app
from core.config import settings
from core.database import init_db
from services.realtime_anomaly_detector import realtime_detector

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Energy Tracking - Analytics Service",
    description="Service for energy consumption analytics and reporting",
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
    return {"status": "healthy", "service": "analytics", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    logger.info("Starting Analytics Service...")
    await init_db()
    
    # Start real-time anomaly detection
    asyncio.create_task(realtime_detector.start_monitoring())
    logger.info("Real-time anomaly detection started")
    
    logger.info("Analytics Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks on shutdown"""
    logger.info("Shutting down Analytics Service...")
    realtime_detector.stop_monitoring()
    logger.info("Analytics Service stopped")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
