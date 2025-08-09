# IoT Mock Service - Implementation Summary

## Overview

I've successfully created a comprehensive IoT Mock Service for your Energy Tracking Platform. This service simulates IoT devices and provides realistic energy monitoring data streams to help with development, testing, and demonstration.

## What's Been Created

### 🏗️ Core Service Components

1. **MockDeviceManager** (`services/mock_device_manager.py`)
   - Manages virtual IoT devices lifecycle
   - Handles MQTT communication
   - Processes device commands
   - Maintains device state and status

2. **DeviceSimulator** (`services/device_simulator.py`)
   - Continuous data generation and transmission
   - Realistic energy consumption patterns
   - Configurable simulation intervals
   - Background processing

3. **MockDevice Class** (`services/mock_device_manager.py`)
   - Individual device simulation
   - Power, voltage, current, and energy readings
   - Device status management (online/offline, enabled/disabled)
   - Realistic data variations

### 🌐 REST API (`api/routes.py`)

**Device Management:**
- `GET /api/v1/devices` - List all devices
- `GET /api/v1/devices/{id}` - Get device details  
- `POST /api/v1/devices` - Create new device
- `PUT /api/v1/devices/{id}` - Update device
- `DELETE /api/v1/devices/{id}` - Delete device

**Device Operations:**
- `GET /api/v1/devices/{id}/readings` - Get current readings
- `POST /api/v1/devices/{id}/command` - Send device command
- `POST /api/v1/devices/{id}/simulate` - Trigger data simulation

**Simulation Control:**
- `GET /api/v1/simulation/status` - Get simulation status
- `POST /api/v1/simulation/start` - Start simulation
- `POST /api/v1/simulation/stop` - Stop simulation

### 📡 MQTT Integration

**Topics Used:**
- `energy/devices/{device_id}/data` - Energy readings
- `energy/devices/{device_id}/status` - Device status
- `energy/devices/{device_id}/commands` - Device commands

**Data Format:**
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

### 🐳 Docker Integration

- Added to main `docker-compose.yml`
- Dockerfile with health checks
- Environment configuration
- Network integration with existing services

### 🛠️ Configuration (`core/config.py`)

**Key Settings:**
- MQTT broker connection
- Simulation parameters
- Device types and ranges
- API configuration
- Data variation settings

### 📚 Documentation & Tools

1. **README.md** - Comprehensive service documentation
2. **setup.py** - Interactive setup script
3. **simple_test.py** - API testing without dependencies
4. **test_service.py** - Full service testing with MQTT
5. **start-mock-service.ps1** - PowerShell management script

## Default Devices

The service automatically creates 5 realistic devices:

1. **HVAC System** (25kW) - Building A HVAC
2. **LED Lighting** (8.5kW) - Office lighting
3. **Server Rack** (45kW) - Data center equipment
4. **Production Line** (120kW) - Industrial equipment
5. **Kitchen Equipment** (15kW) - Cafeteria appliances

## Key Features

### ✨ Realistic Simulation
- **Power variations**: ±10% realistic fluctuations
- **Voltage stability**: ±2% variations around nominal
- **Energy integration**: Cumulative energy consumption
- **Device states**: Online/offline, enabled/disabled
- **Error conditions**: Simulated device failures

### 🔧 Device Management
- **Dynamic device creation** via API
- **Device type support**: HVAC, lighting, server, industrial, appliance
- **Remote control**: Commands via MQTT or API
- **Status monitoring**: Real-time device status
- **Configuration updates**: Runtime parameter changes

### 🚀 Easy Integration
- **Standard MQTT topics** matching your existing system
- **Docker Compose integration** with your platform
- **Health checks** and monitoring
- **Configurable intervals** and data ranges
- **CORS support** for web interface integration

## How to Use

### 🚀 Quick Start

1. **Start the service:**
   ```bash
   cd services/iot-mock
   python setup.py
   ```

2. **Or with Docker:**
   ```bash
   cd docker
   docker-compose up -d iot-mock
   ```

3. **Test the API:**
   ```bash
   python simple_test.py
   ```

### 🌐 Access Points

- **Service**: http://localhost:8090
- **API Docs**: http://localhost:8090/docs
- **Health Check**: http://localhost:8090/health

### 📊 Monitor Data Flow

1. **Check simulation status:**
   ```bash
   curl http://localhost:8090/api/v1/simulation/status
   ```

2. **View device data:**
   ```bash
   curl http://localhost:8090/api/v1/devices
   ```

3. **Watch MQTT messages** (if you have mosquitto_sub):
   ```bash
   mosquitto_sub -h localhost -u iot_user -P iot123 -t "energy/devices/+/data"
   ```

## Integration with Your Platform

### 📥 Data Flow
```
IoT Mock Service → MQTT Broker → Data Ingestion → InfluxDB → Dashboard
```

### 🔌 Automatic Integration
- The mock service publishes to the same MQTT topics your data-ingestion service subscribes to
- No changes needed to your existing services
- Data automatically flows through your pipeline
- Appears in your dashboard as real device data

### 🎛️ Device Management
- Add new devices via the IoT Mock API
- They automatically start sending data
- Control device behavior (power levels, online/offline)
- Remove devices when no longer needed

## Benefits

### 🧪 For Development
- **No real hardware needed** for development
- **Consistent test data** for reproducible testing
- **Multiple device types** for comprehensive testing
- **Controlled scenarios** (failures, variations, etc.)

### 📈 For Demonstrations
- **Realistic data patterns** for convincing demos
- **Multiple simultaneous devices** showing scale
- **Interactive control** for live demonstrations
- **Immediate data visualization** in your dashboard

### ⚙️ For Testing
- **Load testing** with many simulated devices
- **Edge case simulation** (failures, high loads)
- **API testing** without hardware dependencies
- **Integration testing** of the full pipeline

## Next Steps

### 🔄 Immediate Use
1. Start the IoT Mock Service
2. Verify data appears in your dashboard
3. Create additional devices as needed
4. Test different scenarios

### 🚀 Future Enhancements
- **Device profiles** for different energy patterns
- **Scenario scripting** for complex test cases
- **Historical data replay** from real devices
- **Advanced failure simulation**

## Files Created

```
services/iot-mock/
├── main.py                     # Main FastAPI application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── README.md                   # Service documentation
├── .env.example               # Configuration template
├── setup.py                   # Interactive setup
├── simple_test.py             # API testing
├── test_service.py            # Full service testing
├── start-mock-service.ps1     # PowerShell management
├── core/
│   ├── __init__.py
│   └── config.py              # Configuration settings
├── services/
│   ├── __init__.py
│   ├── mock_device_manager.py # Device management
│   └── device_simulator.py    # Data simulation
└── api/
    ├── __init__.py
    └── routes.py              # REST API endpoints
```

The IoT Mock Service is now fully integrated into your Energy Tracking Platform and ready to provide realistic IoT device simulation for development, testing, and demonstration purposes! 🎉
