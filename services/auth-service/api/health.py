"""
Health check router for the authentication service
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from core.database import get_db
from core.cache import get_redis
from libs.common.health import (
    HealthChecker, 
    DatabaseHealthCheck, 
    RedisHealthCheck,
    SystemHealthCheck
)

router = APIRouter()

# Initialize health checker
health_checker = HealthChecker("auth-service")


async def get_health_checker():
    """Get configured health checker"""
    # Clear existing checks and reconfigure
    health_checker.checks.clear()
    
    # Add database health check
    async for db in get_db():
        health_checker.add_check(DatabaseHealthCheck(db))
        break
    
    # Add Redis health check
    redis = await get_redis()
    health_checker.add_check(RedisHealthCheck(redis))
    
    # Add system health check
    health_checker.add_check(SystemHealthCheck())
    
    return health_checker


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    checker = await get_health_checker()
    return await checker.run_all_checks()


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - simple check that service is running"""
    return {
        "status": "alive",
        "service": "auth-service",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - check if service is ready to serve traffic"""
    checker = await get_health_checker()
    result = await checker.run_all_checks()
    
    # Return 503 if not healthy
    if result["status"] != "healthy":
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=result)
    
    return result
