"""
Data Ingestion Service
Handles IoT device data ingestion via MQTT and HTTP APIs
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import time

from core.config import settings
from core.database import init_db
from core.mqtt import MQTTClient
from core.influxdb import InfluxDBClient
from core.auth import get_current_user
from api.data import router as data_router
from services.ingestion import IngestionService

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.LOG_LEVEL == "INFO" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Data Ingestion Service...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize InfluxDB client
    app.state.influx_client = InfluxDBClient()
    await app.state.influx_client.connect()
    logger.info("InfluxDB client initialized")
    
    # Initialize MQTT client
    app.state.mqtt_client = MQTTClient()
    await app.state.mqtt_client.connect()
    logger.info("MQTT client connected")
    
    # Initialize ingestion service
    app.state.ingestion_service = IngestionService(
        influx_client=app.state.influx_client,
        mqtt_client=app.state.mqtt_client
    )
    
    # Start MQTT message handling
    asyncio.create_task(app.state.mqtt_client.start_consuming())
    
    yield
    
    # Cleanup
    await app.state.mqtt_client.disconnect()
    await app.state.influx_client.close()
    logger.info("Shutting down Data Ingestion Service...")

# Create FastAPI app
app = FastAPI(
    title="Energy Tracking Data Ingestion Service",
    description="IoT data ingestion service for energy tracking platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive for IoT devices
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(data_router, prefix="/api/v1", tags=["Data Ingestion"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Energy Tracking Data Ingestion Service",
        "version": "1.0.0",
        "status": "running",
        "mqtt_connected": app.state.mqtt_client.is_connected() if hasattr(app.state, 'mqtt_client') else False,
        "timestamp": time.time()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from core.database import get_db
        
        # Check database connection
        async for db in get_db():
            await db.execute("SELECT 1")
            break
        
        # Check InfluxDB connection
        influx_healthy = False
        if hasattr(app.state, 'influx_client'):
            influx_healthy = await app.state.influx_client.health_check()
        
        # Check MQTT connection
        mqtt_healthy = False
        if hasattr(app.state, 'mqtt_client'):
            mqtt_healthy = app.state.mqtt_client.is_connected()
        
        overall_status = "healthy" if influx_healthy and mqtt_healthy else "degraded"
        
        return {
            "status": overall_status,
            "database": "connected",
            "influxdb": "connected" if influx_healthy else "disconnected",
            "mqtt": "connected" if mqtt_healthy else "disconnected",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.get("/metrics")
async def metrics():
    """Service metrics endpoint"""
    return {
        "ingested_messages_total": 0,  # TODO: Implement metrics tracking
        "mqtt_messages_received": 0,
        "http_requests_received": 0,
        "processing_errors": 0,
        "active_devices": 0,
        "uptime_seconds": 0,
        "timestamp": time.time()
    }

@app.post("/ingest/batch")
async def ingest_batch_data(
    data_points: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user)
):
    """Batch data ingestion endpoint"""
    try:
        if not hasattr(app.state, 'ingestion_service'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ingestion service not available"
            )
        
        # Add to background processing
        background_tasks.add_task(
            app.state.ingestion_service.process_batch,
            data_points,
            current_user.get("user_id")
        )
        
        return {
            "message": f"Batch of {len(data_points)} data points queued for processing",
            "batch_size": len(data_points),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Batch ingestion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch ingestion failed"
        )

@app.get("/devices")
async def list_devices(current_user=Depends(get_current_user)):
    """List registered IoT devices"""
    return {
        "devices": [],  # TODO: Implement device management
        "total": 0,
        "timestamp": time.time()
    }

@app.get("/status")
async def ingestion_status():
    """Data ingestion service status"""
    try:
        mqtt_status = "connected" if hasattr(app.state, 'mqtt_client') and app.state.mqtt_client.is_connected() else "disconnected"
        influx_status = "connected" if hasattr(app.state, 'influx_client') else "disconnected"
        
        return {
            "service": "data-ingestion",
            "status": "operational",
            "components": {
                "mqtt_broker": mqtt_status,
                "influxdb": influx_status,
                "database": "connected"
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "service": "data-ingestion", 
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
