"""
Energy Tracking Authentication Service
Centralized authentication and authorization microservice with RBAC support
"""

import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager

# Add libs to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'libs'))

from api.auth import router as auth_router
from api.permissions import router as permissions_router
from api.roles import router as roles_router
from api.users import router as users_router
from api.health import router as health_router
from core.config import settings
from core.database import init_db
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Import shared libraries
try:
    from common.security import SecurityMiddleware, SecurityConfig, create_security_config
    from common.threat_detection import create_threat_intelligence
    from common.cache import CacheManager
    from common.middleware import add_cors_middleware, add_logging_middleware
    from common.exceptions import setup_exception_handlers
except ImportError:
    # Fallback for development - libs not in path
    from libs.common.security import SecurityMiddleware, SecurityConfig, create_security_config
    from libs.common.threat_detection import create_threat_intelligence
    from libs.common.cache import CacheManager
    from libs.common.middleware import add_cors_middleware, add_logging_middleware
    # Simple exception handler setup
    def setup_exception_handlers(app):
        pass
from libs.monitoring.metrics import MetricsCollector, setup_metrics_endpoint
from libs.monitoring.tracing import setup_tracing
from infrastructure.logging import setup_logging, ServiceLogger

# Setup centralized logging
setup_logging("auth-service", log_level=settings.LOG_LEVEL)
logger = ServiceLogger("auth-service")

# Initialize metrics collector
metrics = MetricsCollector("auth-service")

# Initialize cache manager (will be setup in lifespan)
cache_manager = None

# Global threat intelligence system
threat_intelligence = None

security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global threat_intelligence, cache_manager
    
    logger.info("Starting Authentication Service...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize Redis connection
    from core.cache import init_redis, get_redis

    await init_redis()
    logger.info("Redis connection initialized")
    
    # Initialize cache manager with Redis client
    redis_client = await get_redis()
    cache_manager = CacheManager(redis_client, key_prefix="auth-service")
    logger.info("Cache manager initialized")

    # Initialize threat intelligence
    threat_intelligence = await create_threat_intelligence(cache_manager)
    logger.info("Threat intelligence system initialized")

    # Run database seeding
    try:
        from core.seeder import run_seeds

        await run_seeds()
        logger.info("Database seeding completed")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        # Don't fail startup if seeding fails, just log the error

    yield

    logger.info("Shutting down Authentication Service...")
    if cache_manager:
        await cache_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Energy Tracking Authentication Service",
    description="Centralized authentication and authorization service with RBAC",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Setup middleware from shared libraries
add_cors_middleware(app, settings.ALLOWED_ORIGINS)

# Setup distributed tracing
setup_tracing(app, "auth-service")

# Add comprehensive security middleware
security_config = create_security_config(
    rate_limit_per_minute=60,  # 60 requests per minute for auth service
    rate_limit_per_hour=500,   # 500 requests per hour
    audit_endpoints=["/auth/login", "/auth/register", "/users", "/auth/logout"]
)
app.add_middleware(SecurityMiddleware, cache_manager=cache_manager, config=security_config)

add_logging_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)

# Setup metrics endpoint
setup_metrics_endpoint(app, metrics)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(roles_router, prefix="/roles", tags=["Roles"])
app.include_router(permissions_router, prefix="/permissions", tags=["Permissions"])
app.include_router(health_router, tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint"""
    with metrics.time_operation("root_request"):
        logger.log_api_call("GET", "/", 200, 0)
        return {
            "service": "Energy Tracking Authentication Service",
            "version": "1.0.0",
            "status": "running",
            "environment": settings.ENVIRONMENT,
            "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled"
        }


@app.get("/metrics")
async def get_metrics():
    """Enhanced metrics endpoint with shared libraries"""
    try:
        # Get basic metrics from shared library
        basic_metrics = metrics.get_metrics()
        
        # Add service-specific metrics
        service_metrics = {
            "active_sessions": 0,  # TODO: Implement session counting
            "total_users": 0,  # TODO: Implement user counting
        }
        
        # Combine metrics
        all_metrics = {**basic_metrics, **service_metrics}
        
        logger.log_api_call("GET", "/metrics", 200, 0)
        return all_metrics
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": "Unable to retrieve metrics"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
