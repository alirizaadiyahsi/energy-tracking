## IoT Mock Service Anomaly System - Implementation Complete

### 🎯 **What We Accomplished**

You requested: *"I want iot-mock service sometimes send some data with anomaly for random device"*

✅ **Successfully implemented comprehensive anomaly generation system!**

### 🔧 **Key Features Implemented**

#### 1. **Automatic Random Anomaly Generation**
- **2% chance** of anomaly per device reading (configurable)
- **Random device selection** for anomalies
- **Multiple anomaly types**:
  - `high_power_consumption` - Power spikes 2-5x normal
  - `voltage_fluctuation` - Voltage varies ±20%
  - `power_spike` - Sudden power surges
  - `sustained_high_load` - Extended high power usage

#### 2. **Anomaly Duration & Intensity**
- **Duration**: 3-10 readings per anomaly (configurable)
- **Power multipliers**: 2.0x to 5.0x normal consumption
- **Voltage variation**: ±20% from baseline
- **Realistic simulation**: Gradual changes, not instant jumps

#### 3. **Manual Anomaly Control API**
- **POST `/trigger-anomaly`** - Force anomaly on specific/random device
- **GET `/anomaly-status`** - Check current anomaly states
- **POST `/clear-anomalies`** - Stop all active anomalies

#### 4. **Enhanced Monitoring & Logging**
- Real-time anomaly detection warnings
- Detailed logging with device ID, type, duration
- Current power/voltage readings during anomalies
- MQTT publishing of anomalous data

### 📊 **Live Example Output**
```
2025-08-10 00:18:47,325 - WARNING - Started voltage_fluctuation anomaly for device mock-appliance-001 (duration: 5 readings, power_mult: 0.83)
2025-08-10 00:18:47,326 - WARNING - Anomaly detected in device mock-appliance-001: voltage_fluctuation (Power: 12.23W, Voltage: 195.6V)
2025-08-10 00:18:52,336 - WARNING - Anomaly detected in device mock-appliance-001: voltage_fluctuation (Power: 12.94W, Voltage: 194.1V)
...
2025-08-10 00:19:07,378 - INFO - Ended voltage_fluctuation anomaly for device mock-appliance-001
```

### 🔄 **How It Works**
1. **Every 5 seconds** (simulation interval), each device checks for anomalies
2. **2% random chance** triggers automatic anomaly
3. **Anomaly state machine** tracks active anomalies per device
4. **Data transformation** applies power/voltage multipliers during anomalies
5. **MQTT publishing** sends anomalous data to data ingestion service
6. **Automatic cleanup** ends anomalies after duration expires

### 🎮 **API Usage Examples**

**Trigger manual anomaly:**
```bash
curl -X POST "http://localhost:8090/trigger-anomaly" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "mock-hvac-001", "anomaly_type": "high_power_consumption"}'
```

**Check anomaly status:**
```bash
curl "http://localhost:8090/anomaly-status"
```

### 🔧 **Configuration Settings**
All anomaly behavior is configurable in `core/config.py`:
- `ANOMALY_CHANCE = 0.02` (2% chance per reading)
- `ANOMALY_POWER_MULTIPLIER_MIN/MAX = 2.0/5.0`
- `ANOMALY_DURATION_MIN/MAX = 3/10` readings
- `ANOMALY_VOLTAGE_VARIATION = 0.2` (±20%)

### 🚀 **Next Steps**
The anomaly system is now fully functional and will generate realistic anomalous data that your analytics dashboard can detect and display as alerts! The data flows through:

**IoT Mock Service → MQTT → Data Ingestion → Analytics → Dashboard Alerts**

Perfect for testing your monitoring and alerting systems! 🎉
