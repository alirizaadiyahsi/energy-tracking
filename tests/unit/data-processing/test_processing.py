"""
Unit tests for data processing service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import uuid
import json


@pytest.mark.unit
@pytest.mark.data_processing
class TestDataProcessing:
    """Test data processing logic"""
    
    def test_energy_data_validation(self):
        """Test energy data validation"""
        
        def validate_energy_data(data):
            """Mock energy data validator"""
            required_fields = ["device_id", "timestamp", "power", "voltage", "current"]
            errors = []
            
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            # Validate data types and ranges
            if "power" in data:
                try:
                    power = float(data["power"])
                    if power < 0:
                        errors.append("Power must be non-negative")
                    if power > 100000:  # 100kW max
                        errors.append("Power value seems unrealistic")
                except (ValueError, TypeError):
                    errors.append("Power must be a valid number")
            
            if "voltage" in data:
                try:
                    voltage = float(data["voltage"])
                    if voltage < 0 or voltage > 1000:
                        errors.append("Voltage must be between 0 and 1000V")
                except (ValueError, TypeError):
                    errors.append("Voltage must be a valid number")
            
            if "current" in data:
                try:
                    current = float(data["current"])
                    if current < 0:
                        errors.append("Current must be non-negative")
                except (ValueError, TypeError):
                    errors.append("Current must be a valid number")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors
            }
        
        # Valid data
        valid_data = {
            "device_id": "device_123",
            "timestamp": "2024-01-15T10:30:00Z",
            "power": 1250.5,
            "voltage": 230.0,
            "current": 5.43
        }
        
        # Invalid data
        invalid_data = {
            "device_id": "device_123",
            "power": -100,  # Negative power
            "voltage": 1500,  # Too high voltage
            "current": "invalid"  # Invalid current
        }
        
        valid_result = validate_energy_data(valid_data)
        assert valid_result["is_valid"] is True
        assert len(valid_result["errors"]) == 0
        
        invalid_result = validate_energy_data(invalid_data)
        assert invalid_result["is_valid"] is False
        assert len(invalid_result["errors"]) > 0
    
    def test_data_transformation(self):
        """Test data transformation logic"""
        
        def transform_energy_data(raw_data):
            """Mock data transformer"""
            transformed = raw_data.copy()
            
            # Add calculated fields
            if "power" in raw_data and "timestamp" in raw_data:
                # Calculate energy consumption (simplified)
                transformed["energy_kwh"] = raw_data["power"] / 1000  # Convert W to kW
            
            # Add processing timestamp
            transformed["processed_at"] = datetime.utcnow().isoformat()
            
            # Normalize device_id
            if "device_id" in raw_data:
                transformed["device_id"] = raw_data["device_id"].upper()
            
            # Round numerical values
            for field in ["power", "voltage", "current"]:
                if field in transformed:
                    transformed[field] = round(float(transformed[field]), 2)
            
            return transformed
        
        raw_data = {
            "device_id": "device_123",
            "timestamp": "2024-01-15T10:30:00Z",
            "power": 1250.567,
            "voltage": 230.123,
            "current": 5.4321
        }
        
        transformed = transform_energy_data(raw_data)
        
        assert transformed["device_id"] == "DEVICE_123"
        assert "processed_at" in transformed
        assert "energy_kwh" in transformed
        assert transformed["energy_kwh"] == 1.25  # 1250W / 1000
        assert transformed["power"] == 1250.57
        assert transformed["voltage"] == 230.12
        assert transformed["current"] == 5.43
    
    def test_anomaly_detection(self):
        """Test anomaly detection logic"""
        
        def detect_anomalies(current_reading, historical_data):
            """Mock anomaly detector"""
            anomalies = []
            
            if not historical_data:
                return anomalies
            
            # Calculate statistics from historical data
            power_values = [reading["power"] for reading in historical_data]
            avg_power = sum(power_values) / len(power_values)
            max_power = max(power_values)
            min_power = min(power_values)
            
            # Check for power anomalies
            current_power = current_reading["power"]
            
            # Sudden spike (more than 3x average)
            if current_power > avg_power * 3:
                anomalies.append({
                    "type": "power_spike",
                    "value": current_power,
                    "threshold": avg_power * 3,
                    "severity": "high"
                })
            
            # Sudden drop (less than 10% of average)
            if current_power < avg_power * 0.1:
                anomalies.append({
                    "type": "power_drop",
                    "value": current_power,
                    "threshold": avg_power * 0.1,
                    "severity": "medium"
                })
            
            # Check voltage anomalies
            if "voltage" in current_reading:
                voltage = current_reading["voltage"]
                if voltage < 200 or voltage > 250:  # Normal range 200-250V
                    anomalies.append({
                        "type": "voltage_abnormal",
                        "value": voltage,
                        "expected_range": [200, 250],
                        "severity": "high"
                    })
            
            return anomalies
        
        # Historical data
        historical_data = [
            {"power": 1000, "voltage": 230},
            {"power": 1100, "voltage": 235},
            {"power": 950, "voltage": 225},
            {"power": 1050, "voltage": 240}
        ]
        
        # Normal reading
        normal_reading = {"power": 1020, "voltage": 232}
        anomalies = detect_anomalies(normal_reading, historical_data)
        assert len(anomalies) == 0
        
        # Anomalous reading (power spike)
        spike_reading = {"power": 5000, "voltage": 180}
        anomalies = detect_anomalies(spike_reading, historical_data)
        assert len(anomalies) == 2  # Power spike + voltage anomaly
        assert any(a["type"] == "power_spike" for a in anomalies)
        assert any(a["type"] == "voltage_abnormal" for a in anomalies)
    
    def test_data_aggregation(self):
        """Test data aggregation logic"""
        
        def aggregate_data(readings, time_window="hour"):
            """Mock data aggregator"""
            if not readings:
                return {}
            
            # Group by time window
            if time_window == "hour":
                grouped = {}
                for reading in readings:
                    timestamp = datetime.fromisoformat(reading["timestamp"].replace("Z", "+00:00"))
                    hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                    
                    if hour_key not in grouped:
                        grouped[hour_key] = []
                    grouped[hour_key].append(reading)
                
                # Calculate aggregates for each hour
                aggregated = {}
                for hour, hour_readings in grouped.items():
                    power_values = [r["power"] for r in hour_readings]
                    
                    aggregated[hour.isoformat()] = {
                        "count": len(hour_readings),
                        "avg_power": sum(power_values) / len(power_values),
                        "min_power": min(power_values),
                        "max_power": max(power_values),
                        "total_energy": sum(power_values) / 1000  # Simplified kWh
                    }
                
                return aggregated
        
        readings = [
            {"timestamp": "2024-01-15T10:15:00Z", "power": 1000},
            {"timestamp": "2024-01-15T10:30:00Z", "power": 1100},
            {"timestamp": "2024-01-15T10:45:00Z", "power": 950},
            {"timestamp": "2024-01-15T11:15:00Z", "power": 1200},
            {"timestamp": "2024-01-15T11:30:00Z", "power": 1150}
        ]
        
        aggregated = aggregate_data(readings, "hour")
        
        assert len(aggregated) == 2  # Two hours
        
        # Check first hour (10:00)
        hour_10 = next(k for k in aggregated.keys() if "T10:00:00" in k)
        assert aggregated[hour_10]["count"] == 3
        assert aggregated[hour_10]["avg_power"] == (1000 + 1100 + 950) / 3
        assert aggregated[hour_10]["min_power"] == 950
        assert aggregated[hour_10]["max_power"] == 1100
    
    def test_data_filtering(self):
        """Test data filtering logic"""
        
        def filter_readings(readings, filters):
            """Mock data filter"""
            filtered = readings.copy()
            
            # Filter by device_id
            if "device_id" in filters:
                filtered = [r for r in filtered if r.get("device_id") == filters["device_id"]]
            
            # Filter by time range
            if "start_time" in filters:
                start_time = datetime.fromisoformat(filters["start_time"].replace("Z", "+00:00"))
                filtered = [
                    r for r in filtered 
                    if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) >= start_time
                ]
            
            if "end_time" in filters:
                end_time = datetime.fromisoformat(filters["end_time"].replace("Z", "+00:00"))
                filtered = [
                    r for r in filtered 
                    if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) <= end_time
                ]
            
            # Filter by power range
            if "min_power" in filters:
                filtered = [r for r in filtered if r.get("power", 0) >= filters["min_power"]]
            
            if "max_power" in filters:
                filtered = [r for r in filtered if r.get("power", 0) <= filters["max_power"]]
            
            return filtered
        
        readings = [
            {"device_id": "dev1", "timestamp": "2024-01-15T10:00:00Z", "power": 1000},
            {"device_id": "dev1", "timestamp": "2024-01-15T11:00:00Z", "power": 1500},
            {"device_id": "dev2", "timestamp": "2024-01-15T10:30:00Z", "power": 800},
            {"device_id": "dev2", "timestamp": "2024-01-15T12:00:00Z", "power": 2000}
        ]
        
        # Filter by device
        dev1_readings = filter_readings(readings, {"device_id": "dev1"})
        assert len(dev1_readings) == 2
        assert all(r["device_id"] == "dev1" for r in dev1_readings)
        
        # Filter by time range
        morning_readings = filter_readings(readings, {
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T11:00:00Z"
        })
        assert len(morning_readings) == 3
        
        # Filter by power range
        high_power_readings = filter_readings(readings, {"min_power": 1200})
        assert len(high_power_readings) == 2
        assert all(r["power"] >= 1200 for r in high_power_readings)


@pytest.mark.unit
@pytest.mark.data_processing
class TestDataStorage:
    """Test data storage operations"""
    
    @pytest.mark.asyncio
    async def test_data_insertion(self):
        """Test data insertion logic"""
        
        class MockDataStore:
            def __init__(self):
                self.data = []
            
            async def insert_reading(self, reading):
                # Validate required fields
                required_fields = ["device_id", "timestamp", "power"]
                for field in required_fields:
                    if field not in reading:
                        raise ValueError(f"Missing required field: {field}")
                
                # Add ID and insert
                reading_with_id = reading.copy()
                reading_with_id["id"] = str(uuid.uuid4())
                reading_with_id["created_at"] = datetime.utcnow().isoformat()
                
                self.data.append(reading_with_id)
                return reading_with_id["id"]
            
            async def get_reading(self, reading_id):
                for reading in self.data:
                    if reading["id"] == reading_id:
                        return reading
                return None
        
        store = MockDataStore()
        
        reading = {
            "device_id": "device_123",
            "timestamp": "2024-01-15T10:30:00Z",
            "power": 1250.5,
            "voltage": 230.0,
            "current": 5.43
        }
        
        # Insert reading
        reading_id = await store.insert_reading(reading)
        assert reading_id is not None
        
        # Retrieve reading
        stored_reading = await store.get_reading(reading_id)
        assert stored_reading is not None
        assert stored_reading["device_id"] == reading["device_id"]
        assert stored_reading["power"] == reading["power"]
        assert "id" in stored_reading
        assert "created_at" in stored_reading
    
    @pytest.mark.asyncio
    async def test_batch_insertion(self):
        """Test batch data insertion"""
        
        class MockBatchDataStore:
            def __init__(self):
                self.data = []
                self.batch_size = 100
            
            async def insert_batch(self, readings):
                if len(readings) > self.batch_size:
                    raise ValueError(f"Batch size exceeds limit of {self.batch_size}")
                
                inserted_ids = []
                for reading in readings:
                    reading_with_id = reading.copy()
                    reading_with_id["id"] = str(uuid.uuid4())
                    reading_with_id["created_at"] = datetime.utcnow().isoformat()
                    
                    self.data.append(reading_with_id)
                    inserted_ids.append(reading_with_id["id"])
                
                return inserted_ids
        
        store = MockBatchDataStore()
        
        readings = [
            {"device_id": "dev1", "timestamp": "2024-01-15T10:00:00Z", "power": 1000},
            {"device_id": "dev1", "timestamp": "2024-01-15T10:01:00Z", "power": 1100},
            {"device_id": "dev2", "timestamp": "2024-01-15T10:00:00Z", "power": 800}
        ]
        
        # Insert batch
        inserted_ids = await store.insert_batch(readings)
        assert len(inserted_ids) == 3
        assert len(store.data) == 3
        
        # Test batch size limit
        large_batch = [{"device_id": "dev1", "power": 1000}] * 150
        with pytest.raises(ValueError, match="Batch size exceeds limit"):
            await store.insert_batch(large_batch)


@pytest.mark.unit
@pytest.mark.data_processing
class TestDataQuality:
    """Test data quality checks"""
    
    def test_duplicate_detection(self):
        """Test duplicate detection logic"""
        
        def detect_duplicates(readings):
            """Mock duplicate detector"""
            seen = set()
            duplicates = []
            
            for i, reading in enumerate(readings):
                # Create a key based on device_id, timestamp, and power
                key = (
                    reading.get("device_id"),
                    reading.get("timestamp"),
                    reading.get("power")
                )
                
                if key in seen:
                    duplicates.append({
                        "index": i,
                        "reading": reading,
                        "duplicate_of": key
                    })
                else:
                    seen.add(key)
            
            return duplicates
        
        readings = [
            {"device_id": "dev1", "timestamp": "2024-01-15T10:00:00Z", "power": 1000},
            {"device_id": "dev1", "timestamp": "2024-01-15T10:01:00Z", "power": 1100},
            {"device_id": "dev1", "timestamp": "2024-01-15T10:00:00Z", "power": 1000},  # Duplicate
            {"device_id": "dev2", "timestamp": "2024-01-15T10:00:00Z", "power": 800}
        ]
        
        duplicates = detect_duplicates(readings)
        assert len(duplicates) == 1
        assert duplicates[0]["index"] == 2
    
    def test_data_completeness(self):
        """Test data completeness checks"""
        
        def check_completeness(readings, required_fields):
            """Mock completeness checker"""
            incomplete_readings = []
            
            for i, reading in enumerate(readings):
                missing_fields = []
                for field in required_fields:
                    if field not in reading or reading[field] is None or reading[field] == "":
                        missing_fields.append(field)
                
                if missing_fields:
                    incomplete_readings.append({
                        "index": i,
                        "reading": reading,
                        "missing_fields": missing_fields
                    })
            
            return incomplete_readings
        
        required_fields = ["device_id", "timestamp", "power", "voltage"]
        
        readings = [
            {"device_id": "dev1", "timestamp": "2024-01-15T10:00:00Z", "power": 1000, "voltage": 230},
            {"device_id": "dev1", "timestamp": "2024-01-15T10:01:00Z", "power": 1100},  # Missing voltage
            {"device_id": "", "timestamp": "2024-01-15T10:02:00Z", "power": 1200, "voltage": 235},  # Empty device_id
            {"timestamp": "2024-01-15T10:03:00Z", "power": 1300, "voltage": 240}  # Missing device_id
        ]
        
        incomplete = check_completeness(readings, required_fields)
        assert len(incomplete) == 3
        
        # Check specific missing fields
        assert "voltage" in incomplete[0]["missing_fields"]
        assert "device_id" in incomplete[1]["missing_fields"]
        assert "device_id" in incomplete[2]["missing_fields"]
    
    def test_data_consistency(self):
        """Test data consistency checks"""
        
        def check_consistency(readings):
            """Mock consistency checker"""
            inconsistencies = []
            
            for i, reading in enumerate(readings):
                # Check power factor calculation (P = V * I * PF)
                if all(field in reading for field in ["power", "voltage", "current", "power_factor"]):
                    expected_power = reading["voltage"] * reading["current"] * reading["power_factor"]
                    actual_power = reading["power"]
                    
                    # Allow 5% tolerance
                    tolerance = 0.05
                    if abs(expected_power - actual_power) / actual_power > tolerance:
                        inconsistencies.append({
                            "index": i,
                            "type": "power_calculation_mismatch",
                            "expected": expected_power,
                            "actual": actual_power,
                            "tolerance": tolerance
                        })
                
                # Check timestamp ordering
                if i > 0:
                    current_time = datetime.fromisoformat(reading["timestamp"].replace("Z", "+00:00"))
                    previous_time = datetime.fromisoformat(readings[i-1]["timestamp"].replace("Z", "+00:00"))
                    
                    if current_time < previous_time:
                        inconsistencies.append({
                            "index": i,
                            "type": "timestamp_out_of_order",
                            "current_time": reading["timestamp"],
                            "previous_time": readings[i-1]["timestamp"]
                        })
            
            return inconsistencies
        
        readings = [
            {
                "timestamp": "2024-01-15T10:00:00Z",
                "power": 1000,
                "voltage": 230,
                "current": 4.35,
                "power_factor": 1.0
            },
            {
                "timestamp": "2024-01-15T10:01:00Z",
                "power": 2000,  # Inconsistent with V*I*PF
                "voltage": 230,
                "current": 4.35,
                "power_factor": 1.0
            },
            {
                "timestamp": "2024-01-15T09:59:00Z",  # Out of order
                "power": 1100,
                "voltage": 235,
                "current": 4.68,
                "power_factor": 1.0
            }
        ]
        
        inconsistencies = check_consistency(readings)
        assert len(inconsistencies) == 2
        
        # Check types of inconsistencies
        types = [inc["type"] for inc in inconsistencies]
        assert "power_calculation_mismatch" in types
        assert "timestamp_out_of_order" in types
