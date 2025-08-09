# Dependency Management Guide

## Overview
This document explains how dependencies are managed across the Energy Tracking Platform's microservices.

## Dependency Strategy

### Service-Specific Requirements
Each service has its own `requirements.txt` file containing only the dependencies it actually uses:

- **auth-service/requirements.txt** - Authentication, JWT, database
- **data-ingestion/requirements.txt** - MQTT, InfluxDB, Redis, PostgreSQL
- **iot-mock/requirements.txt** - MQTT client for device simulation
- **analytics/requirements.txt** - Data analysis, HTTP client
- **api-gateway/requirements.txt** - HTTP routing, database
- **notification/requirements.txt** - Celery, email/SMS
- **data-processing/requirements.txt** - Background processing, Celery

### Docker Build Process
1. Each service's Dockerfile copies its specific `requirements.txt`
2. Dependencies are installed via `pip install -r requirements.txt`
3. Application code is copied after dependency installation for better layer caching

## Rebuilding From Scratch

### Option 1: Quick Rebuild
```powershell
# Rebuild specific service
docker-compose build --no-cache data-ingestion
docker-compose up -d data-ingestion

# Rebuild all services
docker-compose build --no-cache
docker-compose up -d
```

### Option 2: Complete Clean Rebuild
```powershell
# Use the provided script
.\scripts\rebuild-all.ps1
```

This script:
- Stops all containers
- Removes all project images
- Cleans Docker build cache
- Rebuilds everything from scratch
- Starts all services

### Option 3: Manual Clean Rebuild
```powershell
# Stop everything
docker-compose down

# Remove all project images
docker images | Select-String "energy-tracking" | ForEach-Object {
    $imageName = ($_ -split '\s+')[0] + ":" + ($_ -split '\s+')[1]
    docker rmi $imageName -f
}

# Clean build cache
docker builder prune -f

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d
```

## Dependency Auditing

### Check Dependencies
```powershell
# Run dependency audit
.\scripts\audit-dependencies.ps1
```

### Verify Service Dependencies
Each service should only include dependencies it actually uses:

**Core Dependencies (most services):**
- fastapi - Web framework
- uvicorn - ASGI server  
- pydantic - Data validation

**Database Dependencies:**
- sqlalchemy - ORM
- asyncpg - PostgreSQL async
- redis - Redis client

**MQTT Dependencies (data-ingestion, iot-mock only):**
- paho-mqtt - MQTT client

**Authentication (auth-service only):**
- python-jose - JWT handling
- PyJWT - Token management
- bcrypt - Password hashing

## Common Issues & Solutions

### Missing Dependencies
**Symptom:** ImportError when container starts
**Solution:** Add missing package to service's requirements.txt

### Cached Dependencies
**Symptom:** Changes to requirements.txt not reflected
**Solution:** Use `--no-cache` flag when building

### Unused Dependencies
**Symptom:** Large image sizes, security vulnerabilities
**Solution:** Remove unused packages from requirements.txt

## Best Practices

1. **Service Isolation** - Each service manages its own dependencies
2. **Minimal Dependencies** - Only include what's actually used
3. **Version Pinning** - Use exact versions (==) for reproducibility
4. **Regular Audits** - Review dependencies periodically
5. **Clean Rebuilds** - Test full rebuilds regularly

## Verification

After any dependency changes:

1. Rebuild affected services with `--no-cache`
2. Run full test suite
3. Verify all services start correctly
4. Check logs for import errors
