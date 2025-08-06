"""
Energy Tracking Authentication Service
Centralized authentication and authorization microservice with RBAC support
"""
import logging
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from core.config import settings
from core.database import init_db
from api.auth import router as auth_router
from api.users import router as users_router
from api.roles import router as roles_router
from api.permissions import router as permissions_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.LOG_LEVEL == "INFO" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Authentication Service...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Redis connection
    from core.cache import init_redis
    await init_redis()
    logger.info("Redis connection initialized")
    
    yield
    
    logger.info("Shutting down Authentication Service...")

# Create FastAPI app
app = FastAPI(
    title="Energy Tracking Authentication Service",
    description="Centralized authentication and authorization service with RBAC",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(roles_router, prefix="/roles", tags=["Roles"])
app.include_router(permissions_router, prefix="/permissions", tags=["Permissions"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Energy Tracking Authentication Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from core.database import get_db
    from core.cache import get_redis
    
    try:
        # Check database connection
        async for db in get_db():
            await db.execute("SELECT 1")
            break
        
        # Check Redis connection
        redis = await get_redis()
        await redis.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "cache": "connected",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    return {
        "active_sessions": 0,  # TODO: Implement session counting
        "total_users": 0,      # TODO: Implement user counting
        "uptime": "0h 0m 0s"   # TODO: Implement uptime tracking
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
