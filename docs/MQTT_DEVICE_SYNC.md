# MQTT Device Event Synchronization

This implementation provides automatic synchronization between the main energy tracking system and the IoT mock service using MQTT events.

## How It Works

### 1. Event Publishing (Data Ingestion Service)
When devices are created, updated, or deleted in the main system:
1. The device operation is performed in the database
2. An MQTT event is published to `energy/events/devices/{device_id}/{event_type}`
3. Event types: `device.created`, `device.updated`, `device.deleted`

### 2. Event Listening (IoT Mock Service)
The IoT mock service automatically:
1. Listens for device events on MQTT
2. Creates corresponding mock devices with ID format: `mock-real-{real_device_id}`
3. Starts generating realistic data for new devices
4. Updates or removes mock devices when real devices change

### 3. Event Topics
```
energy/events/devices/{device_id}/device.created
energy/events/devices/{device_id}/device.updated  
energy/events/devices/{device_id}/device.deleted
```

### 4. Event Payload Format
```json
{
  "event_type": "device.created",
  "device_id": "uuid-of-real-device",
  "timestamp": "2025-08-10T12:00:00Z",
  "device_data": {
    "id": "uuid-of-real-device",
    "name": "HVAC Unit 1",
    "type": "hvac",
    "location": "Building A - Floor 2",
    "status": "offline",
    "base_power": null,
    "base_voltage": null,
    ...
  },
  "metadata": {
    "source": "data-ingestion-service"
  }
}
```

## Configuration

### Data Ingestion Service (.env)
```env
MQTT_BROKER=mosquitto
MQTT_PORT=1883
MQTT_USERNAME=iot_user
MQTT_PASSWORD=iot123
```

### IoT Mock Service (.env)
```env
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_USERNAME=iot_user
MQTT_PASSWORD=iot123
```

## Mock Device Mapping

The system automatically maps real device types to appropriate mock device configurations:

| Real Device Type | Mock Base Power | Mock Base Voltage |
|------------------|----------------|-------------------|
| hvac             | 25.0 kW        | 240.0 V          |
| lighting         | 8.5 kW         | 240.0 V          |
| server           | 45.0 kW        | 240.0 V          |
| industrial       | 120.0 kW       | 480.0 V          |
| appliance        | 15.0 kW        | 240.0 V          |
| sensor           | 2.0 kW         | 12.0 V           |
| meter            | 5.0 kW         | 240.0 V          |
| gateway          | 10.0 kW        | 240.0 V          |
| controller       | 12.0 kW        | 240.0 V          |

## Benefits

1. **Automatic Synchronization**: No manual intervention needed
2. **Real-time**: Mock devices created immediately when real devices are added
3. **Consistent**: Mock device IDs follow predictable pattern
4. **Reliable**: Uses MQTT with QoS 1 for guaranteed delivery
5. **Scalable**: Event-driven architecture handles multiple services

## Usage

1. Start the MQTT broker (Mosquitto)
2. Start the Data Ingestion Service
3. Start the IoT Mock Service
4. Add a device through the frontend or API
5. Mock device automatically appears and starts generating data

## Monitoring

Check logs for synchronization status:
- Data Ingestion Service: "Published device event: device.created for device {id}"
- IoT Mock Service: "Created mock device mock-real-{id} for real device: {id}"
