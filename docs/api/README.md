# Energy Tracking IoT Platform - API Documentation

This directory contains the aggregated API documentation for all microservices in the Energy Tracking IoT Platform.

## Services Overview

| Service | Port | Base URL | Health Check | Documentation |
|---------|------|----------|--------------|---------------|
| Auth Service | 8005 | http://localhost:8005 | `/health` | [OpenAPI](./auth-service.json) |
| API Gateway | 8000 | http://localhost:8000 | `/health` | [OpenAPI](./api-gateway.json) |
| Data Ingestion | 8001 | http://localhost:8001 | `/health` | [OpenAPI](./data-ingestion.json) |
| Data Processing | 8002 | http://localhost:8002 | `/health` | [OpenAPI](./data-processing.json) |
| Analytics | 8003 | http://localhost:8003 | `/health` | [OpenAPI](./analytics.json) |
| Notification | 8004 | http://localhost:8004 | `/health` | [OpenAPI](./notification.json) |

## API Standards

### Authentication
All services (except auth service itself) require JWT authentication via the `Authorization: Bearer <token>` header.

### Response Format
All APIs follow a consistent response format:

```json
{
  "success": true,
  "data": {},
  "message": "Optional message",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "uuid-v4"
}
```

### Error Format
Error responses follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "uuid-v4"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (resource already exists)
- `422` - Unprocessable Entity (business logic errors)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error
- `503` - Service Unavailable

## Health Checks

All services implement standardized health check endpoints:

- `/health` - Overall health status
- `/health/live` - Liveness probe (for Kubernetes)
- `/health/ready` - Readiness probe (for Kubernetes)

### Health Check Response Format

```json
{
  "service": "service-name",
  "status": "healthy|unhealthy|degraded",
  "timestamp": "2024-01-01T00:00:00Z",
  "uptime_seconds": 3600,
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "duration_ms": 45.2,
      "details": {}
    },
    "redis": {
      "status": "healthy", 
      "duration_ms": 12.1,
      "details": {}
    }
  }
}
```

## Rate Limiting

All APIs implement rate limiting with the following headers:

- `X-RateLimit-Limit` - Request limit per window
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Unix timestamp when limit resets

## Pagination

List endpoints support pagination with these parameters:

- `page` - Page number (default: 1)
- `limit` - Items per page (default: 10, max: 100)
- `sort` - Sort field
- `order` - Sort order (asc|desc)

Pagination response includes:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

## Filtering and Search

List endpoints support filtering:

- `filter[field]=value` - Exact match filter
- `search=term` - Full-text search
- `created_after=2024-01-01` - Date range filters
- `created_before=2024-12-31` - Date range filters

## Documentation Generation

To generate/update API documentation:

```bash
# Generate OpenAPI specs for all services
make docs-generate

# Serve aggregated documentation
make docs-serve

# Export to Postman collection
make docs-export-postman
```

## Interactive Documentation

When services are running in development mode:

- Auth Service: http://localhost:8005/docs
- API Gateway: http://localhost:8000/docs
- Data Ingestion: http://localhost:8001/docs
- Data Processing: http://localhost:8002/docs
- Analytics: http://localhost:8003/docs
- Notification: http://localhost:8004/docs
