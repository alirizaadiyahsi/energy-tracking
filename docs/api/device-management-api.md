# Device Management API Documentation

## Overview

The Device Management API provides endpoints for managing IoT devices within the energy tracking system. All endpoints require authentication and implement role-based access control with organization isolation.

## Authentication

All device management endpoints require authentication via JWT token:

```
Authorization: Bearer <jwt_token>
```

## Base URL

```
/api/v1/devices
```

## Endpoints

### List Devices

Retrieve a paginated list of devices for the authenticated user's organization.

**Endpoint:** `GET /api/v1/devices`

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| skip | integer | No | 0 | Number of devices to skip (pagination) |
| limit | integer | No | 100 | Maximum number of devices to return |
| status | string | No | all | Filter by device status: `online`, `offline`, `maintenance` |
| type | string | No | all | Filter by device type: `sensor`, `meter`, `gateway`, etc. |

**Response:** `200 OK`

```json
{
  "devices": [
    {
      "id": "device-123",
      "name": "Main Building Sensor",
      "type": "sensor",
      "status": "online",
      "location": "Building A - Floor 1",
      "description": "Temperature and humidity sensor",
      "base_power": 5.0,
      "base_voltage": 240.0,
      "firmware_version": "1.2.3",
      "model": "TempSense Pro",
      "last_seen": "2025-01-10T14:30:00Z",
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-10T14:30:00Z",
      "metadata": {
        "building_id": "bldg-456",
        "room": "101"
      }
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

**Permissions Required:** `READ_DEVICE`

### Get Device by ID

Retrieve a specific device by its ID.

**Endpoint:** `GET /api/v1/devices/{device_id}`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| device_id | string | Yes | Unique device identifier |

**Response:** `200 OK`

```json
{
  "id": "device-123",
  "name": "Main Building Sensor",
  "type": "sensor",
  "status": "online",
  "location": "Building A - Floor 1",
  "description": "Temperature and humidity sensor",
  "base_power": 5.0,
  "base_voltage": 240.0,
  "firmware_version": "1.2.3",
  "model": "TempSense Pro",
  "last_seen": "2025-01-10T14:30:00Z",
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-10T14:30:00Z",
  "metadata": {
    "building_id": "bldg-456",
    "room": "101"
  }
}
```

**Error Responses:**

- `404 Not Found` - Device not found or not accessible
- `403 Forbidden` - Insufficient permissions

**Permissions Required:** `READ_DEVICE`

### Create Device

Create a new device in the system.

**Endpoint:** `POST /api/v1/devices`

**Request Body:**

```json
{
  "name": "New Energy Meter",
  "type": "meter",
  "location": "Building B - Basement",
  "description": "Primary electricity meter for Building B",
  "base_power": 10.0,
  "base_voltage": 480.0,
  "firmware_version": "2.1.0",
  "model": "PowerMeter 3000",
  "metadata": {
    "building_id": "bldg-789",
    "circuit": "main"
  }
}
```

**Response:** `201 Created`

```json
{
  "id": "device-456",
  "name": "New Energy Meter",
  "type": "meter",
  "status": "offline",
  "location": "Building B - Basement",
  "description": "Primary electricity meter for Building B",
  "base_power": 10.0,
  "base_voltage": 480.0,
  "firmware_version": "2.1.0",
  "model": "PowerMeter 3000",
  "last_seen": null,
  "created_at": "2025-01-10T15:00:00Z",
  "updated_at": "2025-01-10T15:00:00Z",
  "metadata": {
    "building_id": "bldg-789",
    "circuit": "main"
  }
}
```

**Validation Rules:**

- `name`: Required, 1-100 characters
- `type`: Required, must be one of: `sensor`, `meter`, `gateway`, `hvac`, `lighting`, `server`, `appliance`, `industrial`, `controller`
- `base_power`: Optional, must be positive number
- `base_voltage`: Optional, must be positive number
- `firmware_version`: Optional, semver format recommended
- `model`: Optional, 1-50 characters
- `metadata`: Optional, valid JSON object

**Error Responses:**

- `400 Bad Request` - Invalid request data
- `403 Forbidden` - Insufficient permissions
- `409 Conflict` - Device name already exists in organization

**Permissions Required:** `CREATE_DEVICE`

### Update Device

Update an existing device's information.

**Endpoint:** `PUT /api/v1/devices/{device_id}`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| device_id | string | Yes | Unique device identifier |

**Request Body:**

```json
{
  "name": "Updated Device Name",
  "type": "sensor",
  "location": "New Location",
  "description": "Updated description",
  "base_power": 7.5,
  "base_voltage": 240.0,
  "firmware_version": "1.3.0",
  "model": "TempSense Pro v2",
  "metadata": {
    "building_id": "bldg-456",
    "room": "102"
  }
}
```

**Response:** `200 OK`

```json
{
  "id": "device-123",
  "name": "Updated Device Name",
  "type": "sensor",
  "status": "online",
  "location": "New Location",
  "description": "Updated description",
  "base_power": 7.5,
  "base_voltage": 240.0,
  "firmware_version": "1.3.0",
  "model": "TempSense Pro v2",
  "last_seen": "2025-01-10T14:30:00Z",
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-10T15:15:00Z",
  "metadata": {
    "building_id": "bldg-456",
    "room": "102"
  }
}
```

**Error Responses:**

- `400 Bad Request` - Invalid request data
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Device not found or not accessible
- `409 Conflict` - Device name already exists in organization

**Permissions Required:** `UPDATE_DEVICE`

### Delete Device

Delete a device from the system.

**Endpoint:** `DELETE /api/v1/devices/{device_id}`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| device_id | string | Yes | Unique device identifier |

**Response:** `204 No Content`

**Error Responses:**

- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Device not found or not accessible
- `409 Conflict` - Device has active data or dependencies

**Permissions Required:** `DELETE_DEVICE`

## Device Types

The following device types are supported:

| Type | Description |
|------|-------------|
| `sensor` | Environmental sensors (temperature, humidity, etc.) |
| `meter` | Energy meters and measurement devices |
| `gateway` | Communication gateways and hubs |
| `hvac` | HVAC system controllers |
| `lighting` | Lighting control systems |
| `server` | Server and computing equipment |
| `appliance` | General appliances |
| `industrial` | Industrial equipment and machinery |
| `controller` | Generic control devices |

## Device Status

Devices can have the following status values:

| Status | Description |
|--------|-------------|
| `online` | Device is active and communicating |
| `offline` | Device is not responding |
| `maintenance` | Device is under maintenance |

## Security Features

### Rate Limiting

API endpoints are rate-limited per user:

- **Standard users:** 100 requests per minute
- **Admin users:** 500 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704902400
```

### Audit Logging

All device operations are logged for security and compliance:

- User ID and organization
- Operation type (CREATE, READ, UPDATE, DELETE)
- Device ID and affected fields
- Timestamp and source IP
- Success/failure status

### Organization Isolation

- Users can only access devices within their organization
- Device queries automatically filter by organization
- Cross-organization access is prevented at the database level

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device not found or access denied",
    "details": {
      "device_id": "device-123"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_REQUEST` | Request validation failed |
| `DEVICE_NOT_FOUND` | Device not found or inaccessible |
| `PERMISSION_DENIED` | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `DEVICE_NAME_EXISTS` | Device name already in use |
| `AUTHENTICATION_REQUIRED` | Valid JWT token required |

## Examples

### Create a New Sensor

```bash
curl -X POST "https://api.energy-tracking.com/api/v1/devices" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Temperature Sensor Room 101",
    "type": "sensor",
    "location": "Building A - Room 101",
    "description": "Digital temperature sensor",
    "base_power": 2.5,
    "base_voltage": 12.0,
    "firmware_version": "1.0.0",
    "model": "TempSense Basic",
    "metadata": {
      "room_id": "room-101",
      "sensor_type": "temperature"
    }
  }'
```

### List All Online Devices

```bash
curl -X GET "https://api.energy-tracking.com/api/v1/devices?status=online&limit=50" \
  -H "Authorization: Bearer <jwt_token>"
```

### Update Device Location

```bash
curl -X PUT "https://api.energy-tracking.com/api/v1/devices/device-123" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Building A - Room 205"
  }'
```

## Best Practices

1. **Always include proper error handling** for API responses
2. **Use pagination** for large device lists
3. **Implement proper retry logic** with exponential backoff
4. **Cache device data** appropriately to reduce API calls
5. **Validate input data** before sending requests
6. **Monitor rate limits** and implement throttling
7. **Use meaningful device names** and descriptions
8. **Keep metadata structured** and documented
9. **Handle organization boundaries** properly in multi-tenant scenarios
10. **Implement proper logging** for debugging and monitoring
