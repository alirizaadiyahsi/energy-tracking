"""
API Gateway Service
Central entry point for all API requests with routing, authentication, and rate limiting
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import httpx
from api.routes import router as api_router
from core.auth import get_current_user, verify_token
from core.config import settings
from core.database import init_db
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from middleware.logging import LoggingMiddleware
from middleware.rate_limit import RateLimitMiddleware
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.LOG_LEVEL == "INFO" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting API Gateway...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize HTTP client for service communication
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("HTTP client initialized")

    yield

    # Cleanup
    await app.state.http_client.aclose()
    logger.info("Shutting down API Gateway...")


# Create FastAPI app
app = FastAPI(
    title="Energy Tracking API Gateway",
    description="Central API gateway for the Energy Tracking IoT platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=settings.RATE_LIMIT_PER_MINUTE, period=60)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Energy Tracking API Gateway",
        "version": "1.0.0",
        "status": "running",
        "timestamp": time.time(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from core.database import get_db

        # Check database connection
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            break

        # Check auth service connectivity
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/health", timeout=5.0
            )
            auth_healthy = auth_response.status_code == 200

        return {
            "status": "healthy" if auth_healthy else "degraded",
            "database": "connected",
            "auth_service": "connected" if auth_healthy else "disconnected",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        )


@app.get("/services")
async def service_status():
    """Check status of all backend services"""
    services = {
        "auth": f"{settings.AUTH_SERVICE_URL}/health",
        "data-ingestion": "http://data-ingestion:8001/health",
        "data-processing": "http://data-processing:8002/health",
        "analytics": "http://analytics:8003/health",
        "notification": "http://notification:8004/health",
    }

    status_results = {}

    async with httpx.AsyncClient() as client:
        for service_name, health_url in services.items():
            try:
                response = await client.get(health_url, timeout=5.0)
                status_results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "last_check": time.time(),
                }
            except Exception as e:
                status_results[service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "last_check": time.time(),
                }

    return {
        "gateway_status": "healthy",
        "services": status_results,
        "timestamp": time.time(),
    }


# Service proxy endpoints
@app.api_route(
    "/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_auth(request: Request, path: str):
    """Proxy requests to auth service"""
    return await proxy_request(request, settings.AUTH_SERVICE_URL, f"/auth/{path}")


@app.api_route(
    "/api/v1/data/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_data(
    request: Request, path: str, current_user=Depends(get_current_user)
):
    """Proxy requests to data ingestion service (authenticated)"""
    return await proxy_request(request, "http://data-ingestion:8001", f"/api/v1/{path}")


@app.api_route(
    "/api/v1/analytics/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_analytics(
    request: Request, path: str, current_user=Depends(get_current_user)
):
    """Proxy requests to analytics service (authenticated)"""
    return await proxy_request(request, "http://analytics:8003", f"/api/v1/{path}")


@app.api_route(
    "/api/v1/notifications/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def proxy_notifications(
    request: Request, path: str, current_user=Depends(get_current_user)
):
    """Proxy requests to notification service (authenticated)"""
    return await proxy_request(request, "http://notification:8004", f"/api/v1/{path}")


async def proxy_request(request: Request, target_url: str, path: str):
    """Generic request proxy function"""
    try:
        # Prepare request data
        url = f"{target_url}{path}"
        headers = dict(request.headers)

        # Remove hop-by-hop headers
        headers.pop("host", None)
        headers.pop("content-length", None)

        # Get request body
        body = await request.body()

        # Make request to target service
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=30.0,
            )

            # Return response
            return JSONResponse(
                content=(
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else response.text
                ),
                status_code=response.status_code,
                headers=dict(response.headers),
            )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail="Proxy error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
