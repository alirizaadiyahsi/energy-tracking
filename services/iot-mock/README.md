# IoT Mock Service

A comprehensive IoT mock service that simulates energy monitoring devices for the Energy Tracking Platform. This service provides realistic device data streams and device management capabilities.

## Features

### Core Capabilities
- **Device Simulation**: Simulates multiple IoT devices with realistic energy consumption patterns
- **MQTT Integration**: Publishes data to MQTT broker using standard energy tracking topics
- **Device Management**: Full CRUD operations for mock devices via REST API
- **Real-time Data**: Continuous data streaming with configurable intervals
- **Device Control**: Remote device commands and status management

### Device Types Supported
- **HVAC Systems**: Heating, ventilation, and air conditioning units
- **Lighting**: LED lighting systems and smart bulbs
- **Servers**: Data center and server room equipment
- **Industrial**: Manufacturing and production equipment
- **Appliances**: Kitchen and office appliances

### Data Simulation
- **Realistic Patterns**: Power consumption varies realistically over time
- **Multiple Metrics**: Power, voltage, current, and cumulative energy readings
- **Status Simulation**: Online/offline and enabled/disabled states
- **Error Conditions**: Simulates device errors and communication issues

## Quick Start

### Using Docker (Recommended)

1. **Build the service**:
```bash
docker build -t iot-mock-service .
```

2. **Run with docker-compose** (from project root):
```bash
docker-compose up iot-mock
```

### Manual Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Run the service**:
```bash
python main.py
```

The service will start on `http://localhost:8090`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Service host address |
| `PORT` | `8090` | Service port |
| `MQTT_BROKER_HOST` | `localhost` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` | `iot_user` | MQTT authentication username |
| `MQTT_PASSWORD` | `iot123` | MQTT authentication password |
| `SIMULATION_INTERVAL` | `5.0` | Seconds between data transmissions |
| `DATA_VARIATION_PERCENT` | `0.1` | Percentage variation in readings |

### MQTT Topics

The service publishes to the following MQTT topics:

- **Data**: `energy/devices/{device_id}/data`
- **Status**: `energy/devices/{device_id}/status` 
- **Commands**: `energy/devices/{device_id}/commands` (subscribed)

## API Endpoints

### Device Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/devices` | List all devices |
| `GET` | `/api/v1/devices/{id}` | Get device details |
| `POST` | `/api/v1/devices` | Create new device |
| `PUT` | `/api/v1/devices/{id}` | Update device |
| `DELETE` | `/api/v1/devices/{id}` | Delete device |

### Device Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/devices/{id}/readings` | Get current readings |
| `POST` | `/api/v1/devices/{id}/command` | Send device command |
| `POST` | `/api/v1/devices/{id}/simulate` | Trigger data simulation |

### Simulation Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/simulation/status` | Get simulation status |
| `POST` | `/api/v1/simulation/start` | Start simulation |
| `POST` | `/api/v1/simulation/stop` | Stop simulation |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/device-types` | Get available device types |
| `GET` | `/health` | Health check |

## Usage Examples

### Create a New Device

```bash
curl -X POST http://localhost:8090/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_type": "hvac",
    "name": "Main Building HVAC",
    "location": "Building A - Roof",
    "base_power": 25.0,
    "base_voltage": 240.0
  }'
```

### Get Device Readings

```bash
curl http://localhost:8090/api/v1/devices/mock-hvac-001/readings
```

### Send Device Command

```bash
curl -X POST http://localhost:8090/api/v1/devices/mock-hvac-001/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "set_power",
    "parameters": {"power": 30.0}
  }'
```

### Control Simulation

```bash
# Start simulation
curl -X POST http://localhost:8090/api/v1/simulation/start

# Check status
curl http://localhost:8090/api/v1/simulation/status

# Stop simulation
curl -X POST http://localhost:8090/api/v1/simulation/stop
```

## Data Format

### Device Data Message
```json
{
  "device_id": "mock-hvac-001",
  "timestamp": "2025-08-09T16:30:00Z",
  "power": 25.3,
  "voltage": 239.8,
  "current": 23.7,
  "energy": 156.7,
  "status": "online",
  "enabled": true
}
```

### Device Status Message
```json
{
  "device_id": "mock-hvac-001",
  "status": "online",
  "enabled": true,
  "timestamp": "2025-08-09T16:30:00Z"
}
```

## Integration

### With Energy Tracking Platform

1. **Ensure MQTT broker is running** (Mosquitto in docker-compose)
2. **Start the IoT Mock Service**
3. **Data automatically flows** to the energy tracking system
4. **Monitor in dashboard** at `http://localhost:3000`

### Default Devices

The service automatically creates 5 default devices:
- HVAC System (25kW)
- LED Lighting (8.5kW) 
- Server Rack (45kW)
- Production Line (120kW)
- Kitchen Equipment (15kW)

## Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
python main.py
```

### Testing the Service

```bash
# Check health
curl http://localhost:8090/health

# List devices
curl http://localhost:8090/api/v1/devices

# Check simulation status
curl http://localhost:8090/api/v1/simulation/status
```

## Troubleshooting

### Common Issues

1. **MQTT Connection Failed**
   - Check if Mosquitto broker is running
   - Verify MQTT credentials in .env
   - Check network connectivity

2. **No Data in Dashboard**
   - Ensure simulation is running
   - Check MQTT topic subscription in data-ingestion service
   - Verify InfluxDB is receiving data

3. **Device Not Responding**
   - Check device status via API
   - Verify device is online and enabled
   - Check MQTT message logs

### Logs

View service logs for debugging:
```bash
# Docker logs
docker logs energy-iot-mock

# Local logs are output to console
```

## Architecture

### Components
- **MockDeviceManager**: Manages device lifecycle and MQTT communication
- **DeviceSimulator**: Handles continuous data generation and transmission
- **MockDevice**: Individual device simulation with realistic patterns
- **REST API**: FastAPI-based management interface

### Data Flow
```
Mock Devices → Device Simulator → MQTT Broker → Data Ingestion → InfluxDB
     ↑              ↑                 ↑              ↑            ↑
   API Control   Scheduling      Message Broker   Processing   Storage
```

## License

This service is part of the Energy Tracking IoT Data Platform project.
