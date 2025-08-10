"""
IoT Mock Service for Energy Tracking Platform

This service simulates IoT devices and provides:
1. Device registration and management
2. Continuous data streaming to MQTT broker
3. REST API for device control
4. Realistic energy consumption patterns
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from core.config import settings
from services.device_simulator import DeviceSimulator
from services.mock_device_manager import MockDeviceManager
from services.device_event_listener import DeviceEventListener

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global variables for service management
device_simulator: DeviceSimulator = None
device_manager: MockDeviceManager = None
device_event_listener: DeviceEventListener = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global device_simulator, device_manager, device_event_listener
    
    try:
        # Startup
        logger.info("Starting IoT Mock Service...")
        
        # Initialize device manager
        device_manager = MockDeviceManager()
        await device_manager.initialize()
        
        # Initialize device simulator
        device_simulator = DeviceSimulator(device_manager)
        await device_simulator.start()
        
        # Initialize device event listener
        device_event_listener = DeviceEventListener(device_manager)
        
        # Add default devices
        await device_manager.add_default_devices()
        
        # Set service references for API routes
        from api.routes import set_services
        set_services(device_manager, device_simulator)
        
        logger.info("IoT Mock Service started successfully")
        logger.info("Device event listener is now listening for real device events")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down IoT Mock Service...")
        
        if device_event_listener:
            device_event_listener.cleanup()
        
        if device_simulator:
            await device_simulator.stop()
        
        if device_manager:
            await device_manager.cleanup()
        
        logger.info("IoT Mock Service stopped")


# Create FastAPI app
app = FastAPI(
    title="IoT Mock Service",
    description="IoT mock device service for energy tracking platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IoT Mock Service",
        "version": "1.0.0",
        "description": "IoT mock device service for energy tracking platform"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global device_simulator, device_manager
    
    status = {
        "status": "healthy",
        "service": "iot-mock",
        "device_manager": "initialized" if device_manager else "not_initialized",
        "device_simulator": "running" if device_simulator and device_simulator.is_running else "stopped",
        "active_devices": len(device_manager.devices) if device_manager else 0
    }
    
    return status


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    sys.exit(0)


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    import uvicorn
    
    logger.info(f"Starting IoT Mock Service on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
