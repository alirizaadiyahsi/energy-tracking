from contextlib import asynccontextmanager

from api.routes import router as api_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.mqtt_client import mqtt_ingestion


# Create FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting MQTT client...")  # Debug print
    mqtt_ingestion.start()
    print("MQTT client started")  # Debug print
    yield
    # Shutdown
    print("Stopping MQTT client...")  # Debug print
    mqtt_ingestion.stop()
    print("MQTT client stopped")  # Debug print


app = FastAPI(
    title="Data Ingestion Service",
    description="Energy tracking data ingestion service",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Data Ingestion Service"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "data-ingestion"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
