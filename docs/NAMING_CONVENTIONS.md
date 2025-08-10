# Service Naming Conventions

This document establishes consistent naming conventions for the Energy Tracking Platform services.

## Established Conventions

### Service Directory and Docker Names
- Use lowercase with hyphens: `iot-mock`, `data-ingestion`, `auth-service`
- Docker container names: `energy-{service-name}` (e.g., `energy-iot-mock`)
- Docker compose service names: `{service-name}` (e.g., `iot-mock`)

### Display Names (User-Facing)
- Use proper capitalization: `IoT Mock Service`, `Data Ingestion Service`, `Auth Service`
- Consistent in API documentation, logs, and user interfaces

### Code and Documentation
- Class names: `IoTMockTester`, `DeviceManager` (PascalCase)
- File names: `iot_mock.py`, `device_manager.py` (snake_case for Python)
- Variable names: `iot_mock_service`, `device_manager` (snake_case)
- API endpoints: `/api/v1/iot-mock/devices` (kebab-case)

## Service Name Standards

| Service | Directory | Docker Service | Container Name | Display Name |
|---------|-----------|----------------|----------------|--------------|
| IoT Mock | `iot-mock` | `iot-mock` | `energy-iot-mock` | `IoT Mock Service` |
| Data Ingestion | `data-ingestion` | `data-ingestion` | `energy-data-ingestion` | `Data Ingestion Service` |
| Auth Service | `auth-service` | `auth-service` | `energy-auth-service` | `Auth Service` |
| API Gateway | `api-gateway` | `api-gateway` | `energy-api-gateway` | `API Gateway Service` |
| Analytics | `analytics` | `analytics` | `energy-analytics` | `Analytics Service` |
| Notification | `notification` | `notification` | `energy-notification` | `Notification Service` |

## Examples

### ✅ Correct Usage
```yaml
# docker-compose.yml
services:
  iot-mock:
    container_name: energy-iot-mock
    build:
      context: ./services/iot-mock
```

```python
# Python class
class IoTMockManager:
    """Manages IoT mock devices"""
    
# Variable names
iot_mock_service = IoTMockManager()
```

```python
# API documentation
app = FastAPI(
    title="IoT Mock Service",
    description="IoT mock device service for energy tracking platform"
)
```

### ❌ Incorrect Usage
```yaml
# Don't use inconsistent naming
services:
  mock-iot:  # Wrong - should be iot-mock
  mockIoT:   # Wrong - should be iot-mock
```

```python
# Don't use inconsistent display names
title="Mock IoT Service"  # Wrong - should be "IoT Mock Service"
title="IOT Mock Service"  # Wrong - should be "IoT Mock Service"
```

## Guidelines

1. **Be Consistent**: Once established, use the same naming pattern throughout
2. **Context Matters**: Use appropriate case for the context (kebab-case for URLs, PascalCase for classes, etc.)
3. **User-Facing vs Internal**: Display names should be user-friendly, internal names should be developer-friendly
4. **Avoid Abbreviations**: Use full words when possible (`iot-mock` not `im`)
5. **Follow Language Conventions**: Python uses snake_case, JavaScript uses camelCase, etc.

## Migration Checklist

When renaming services:
- [ ] Update directory names
- [ ] Update docker-compose.yml service names
- [ ] Update container names
- [ ] Update API titles and descriptions
- [ ] Update documentation
- [ ] Update log messages
- [ ] Update environment variable references
- [ ] Update script references
- [ ] Update README files
- [ ] Update test files
