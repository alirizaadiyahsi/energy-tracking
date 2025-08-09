# Shared Libraries for Energy Tracking IoT Platform

This directory contains shared libraries and utilities used across all microservices in the Energy Tracking IoT Platform.

## Structure

```
libs/
├── common/                     # Common utilities and shared functionality
│   ├── exceptions/            # Standardized exception classes
│   ├── middleware/            # Reusable middleware (CORS, logging, security)
│   ├── auth/                  # Authentication utilities (JWT, permissions)
│   ├── utils/                 # Common utility functions
│   ├── health/                # Health check framework
│   ├── http_client.py         # HTTP client for inter-service communication
│   ├── database.py           # Database utilities and repository pattern
│   ├── responses.py          # Standardized API response formatting
│   └── cache.py              # Redis cache utilities
├── monitoring/               # Observability and metrics
│   ├── metrics.py           # Metrics collection and monitoring
│   └── tracing.py           # Distributed tracing utilities
└── messaging/               # Inter-service communication
    ├── mqtt.py             # MQTT client for IoT device communication
    └── __init__.py         # Event bus and message queue implementations
```

## Installation

To install the shared libraries in a microservice:

```bash
# From the libs directory
pip install -e .

# Or install specific requirements
pip install -r requirements.txt
```

## Usage Examples

### Exception Handling

```python
from libs.common.exceptions import ValidationError, ResourceNotFoundError

# Raise standardized exceptions
raise ValidationError("Invalid email format", {"field": "email"})
raise ResourceNotFoundError("User", user_id)
```

### HTTP Client for Inter-Service Communication

```python
from libs.common.http_client import ServiceClient

async with ServiceClient("http://auth-service:8005") as client:
    user_data = await client.get("/users/123")
    result = await client.post("/users", {"name": "John", "email": "john@example.com"})
```

### Database Repository Pattern

```python
from libs.common.database import BaseRepository

class UserRepository(BaseRepository[User]):
    async def find_by_email(self, email: str) -> Optional[User]:
        return await self.find_one_by(email=email)

# Usage
user_repo = UserRepository(db_session, User)
user = await user_repo.create(name="John", email="john@example.com")
```

### Standardized API Responses

```python
from libs.common.responses import APIResponse, ErrorResponse

# Success response
return APIResponse.success(data=user_data, message="User retrieved successfully")

# Error response
return ErrorResponse.not_found("User", user_id)

# Paginated response
return APIResponse.paginated(users, page=1, limit=10, total=100)
```

### Cache Management

```python
from libs.common.cache import CacheManager

cache = CacheManager(redis_client, key_prefix="users")

# Set and get values
await cache.set("user:123", user_data, expire=3600)
user_data = await cache.get("user:123")

# Rate limiting
rate_limit_cache = RateLimitCache(redis_client)
result = await rate_limit_cache.check_rate_limit("user:123", limit=100, window_seconds=3600)
```

### Health Checks

```python
from libs.common.health import HealthChecker, DatabaseHealthCheck, RedisHealthCheck

# Setup health checker
health_checker = HealthChecker("my-service")
health_checker.add_check(DatabaseHealthCheck(db_connection))
health_checker.add_check(RedisHealthCheck(redis_client))

# Run checks
result = await health_checker.run_all_checks()
```

### Metrics Collection

```python
from libs.monitoring.metrics import increment_counter, set_gauge, time_it

# Increment counters
increment_counter("api.requests", tags={"endpoint": "/users", "method": "GET"})

# Set gauge values
set_gauge("active_connections", 45)

# Time function execution
@time_it("database.query")
async def get_user(user_id: str):
    # Database query here
    pass
```

### Distributed Tracing

```python
from libs.monitoring.tracing import get_tracer, trace

tracer = get_tracer("my-service")

# Manual span creation
with tracer.start_span("database_query") as span:
    span.set_tag("query", "SELECT * FROM users")
    result = await db.execute(query)

# Decorator tracing
@trace("user_service.get_user")
async def get_user(user_id: str):
    # Function implementation
    pass
```

### MQTT Device Communication

```python
from libs.messaging.mqtt import MQTTManager, DeviceManager

# Setup MQTT
mqtt = MQTTManager("localhost", 1883, username="user", password="pass")
await mqtt.connect()

# Device management
device_manager = DeviceManager(mqtt)
await device_manager.register_device(
    device_id="sensor001", 
    device_type="temperature_sensor",
    topics=["devices/sensor001/data"]
)

# Send commands to devices
await device_manager.send_command("sensor001", "read_temperature")
```

### Authentication Utilities

```python
from libs.common.auth import TokenManager, PermissionChecker

# Token management
token_manager = TokenManager("your-secret-key")
token = token_manager.create_access_token({"user_id": "123", "role": "admin"})
payload = token_manager.verify_token(token)

# Permission checking
has_perm = PermissionChecker.has_permission(user_permissions, "users:read")
has_role = PermissionChecker.has_role(user_roles, "admin")
```

### Structured Logging

```python
from infrastructure.logging import setup_logging, ServiceLogger

# Setup logging for service
setup_logging("my-service", log_level="INFO")

# Use service logger
logger = ServiceLogger("my-service")
logger.log_api_call("GET", "/users", 200, 0.145)
logger.log_database_operation("SELECT", "users", 0.023)
```

## Configuration

Each shared library can be configured through environment variables or configuration objects:

```python
# Example configuration
REDIS_URL = "redis://localhost:6379/0"
JWT_SECRET_KEY = "your-secret-key"
LOG_LEVEL = "INFO"
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
```

## Testing

The shared libraries include test utilities and fixtures:

```python
# Test with shared utilities
from libs.common.exceptions import ValidationError
import pytest

def test_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("Invalid data", {"field": "email"})
    
    assert exc_info.value.error_code == "VALIDATION_ERROR"
    assert exc_info.value.status_code == 400
```

## Dependencies

All dependencies are managed in `requirements.txt`:

- **FastAPI/Starlette**: HTTP framework and middleware
- **SQLAlchemy**: Database ORM and utilities
- **Redis**: Caching and session management
- **httpx**: HTTP client for inter-service communication
- **paho-mqtt**: MQTT client for IoT devices
- **psutil**: System monitoring
- **PyJWT**: JWT token handling
- **passlib**: Password hashing

## Best Practices

1. **Import Shared Libraries**: Always import from `libs.` prefix in your services
2. **Use Standardized Exceptions**: Use the exception classes for consistent error handling
3. **Implement Health Checks**: Add appropriate health checks for your service dependencies
4. **Use Structured Logging**: Use the service logger for consistent log formatting
5. **Add Metrics**: Instrument your code with metrics for observability
6. **Handle Errors Gracefully**: Use the shared error response utilities

## Contributing

When adding new shared utilities:

1. Place them in the appropriate subdirectory
2. Add proper type hints and documentation
3. Include usage examples in docstrings
4. Add tests for new functionality
5. Update this README with usage examples
