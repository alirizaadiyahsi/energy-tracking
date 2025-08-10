"""
Main API routes for the gateway
"""

from core.auth import get_current_user, get_optional_user
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Energy Tracking API Gateway",
        "version": "1.0.0",
        "description": "Central API gateway for IoT energy tracking platform",
        "endpoints": {
            "auth": "/api/v1/auth/*",
            "data-ingestion": "/api/v1/data-ingestion/*",
            "data-processing": "/api/v1/data-processing/*",
            "analytics": "/api/v1/analytics/*",
            "notification": "/api/v1/notification/*",
        },
        "legacy_endpoints": {
            "data": "/api/v1/data/* (deprecated - use /api/v1/data-ingestion/)",
            "notifications": "/api/v1/notifications/* (deprecated - use /api/v1/notification/)",
        },
    }


@router.get("/status")
async def gateway_status(current_user=Depends(get_optional_user)):
    """Gateway status with optional user context"""
    return {
        "status": "operational",
        "authenticated": current_user is not None,
        "user": current_user.get("email") if current_user else None,
    }


@router.get("/protected")
async def protected_endpoint(current_user=Depends(get_current_user)):
    """Protected endpoint requiring authentication"""
    return {
        "message": "Access granted to protected resource",
        "user": current_user.get("email"),
        "user_id": current_user.get("user_id"),
    }
