from fastapi import FastAPI
from contextlib import asynccontextmanager

# Create FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(
    title="Data Ingestion Service",
    description="Energy tracking data ingestion service",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Data Ingestion Service"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "data-ingestion"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
