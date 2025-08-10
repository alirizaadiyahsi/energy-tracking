"""
Mock Device Manager

Manages virtual IoT devices and their lifecycle
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import paho.mqtt.client as mqtt
from core.config import settings

logger = logging.getLogger(__name__)


class MockDevice:
    """Represents an IoT mock device"""
    
    def __init__(
        self,
        device_id: str,
        device_type: str,
        name: str,
        location: str,
        base_power: float = 10.0,
        base_voltage: float = 240.0
    ):
        self.device_id = device_id
        self.device_type = device_type
        self.name = name
        self.location = location
        self.base_power = base_power
        self.base_voltage = base_voltage
        
        # Device state
        self.is_online = True
        self.is_enabled = True
        self.last_seen = datetime.utcnow()
        self.created_at = datetime.utcnow()
        
        # Current readings
        self.current_power = base_power
        self.current_voltage = base_voltage
        self.current_current = self.calculate_current()
        self.total_energy = 0.0
        
        # Anomaly state
        self.anomaly_active = False
        self.anomaly_type = None
        self.anomaly_remaining_duration = 0
        self.anomaly_power_multiplier = 1.0
        self.anomaly_voltage_multiplier = 1.0
        
        # Device metadata
        self.firmware_version = "1.0.0"
        self.model = f"EnergyMock-{device_type.upper()}"
        self.serial_number = f"SN{device_id[-8:]}"
        
    def calculate_current(self) -> float:
        """Calculate current based on power and voltage"""
        if self.current_voltage > 0:
            return round(self.current_power * 1000 / self.current_voltage, 2)
        return 0.0
    
    def update_readings(self, power_variation: float = 0.1, anomaly_chance: float = 0.02) -> Dict[str, Any]:
        """Update device readings with realistic variations and occasional anomalies"""
        if not self.is_online or not self.is_enabled:
            return self.get_offline_readings()
        
        import random
        
        # Check if we should start a new anomaly
        if not self.anomaly_active and random.random() < anomaly_chance:
            self._start_anomaly()
        
        # Check if current anomaly should end
        if self.anomaly_active:
            self.anomaly_remaining_duration -= 1
            if self.anomaly_remaining_duration <= 0:
                self._end_anomaly()
        
        # Generate readings based on current state
        if self.anomaly_active:
            self._generate_anomalous_readings()
        else:
            self._generate_normal_readings(power_variation)
        
        # Calculate current
        self.current_current = self.calculate_current()
        
        # Update energy (integrate power over time)
        energy_increment = self.current_power * (settings.SIMULATION_INTERVAL / 3600)
        self.total_energy += energy_increment
        
        # Update last seen
        self.last_seen = datetime.utcnow()
        
        # Create readings with anomaly information
        readings = self.get_current_readings()
        if self.anomaly_active:
            readings["anomaly"] = True
            readings["anomaly_type"] = self.anomaly_type
            readings["anomaly_duration_remaining"] = self.anomaly_remaining_duration
        else:
            readings["anomaly"] = False
            
        return readings
    
    def _start_anomaly(self):
        """Start a new anomaly episode"""
        import random
        
        # Choose anomaly type
        anomaly_types = [
            "high_power_consumption",
            "voltage_fluctuation", 
            "power_spike",
            "sustained_high_load"
        ]
        
        self.anomaly_type = random.choice(anomaly_types)
        self.anomaly_active = True
        
        # Set anomaly duration (3-10 readings)
        self.anomaly_remaining_duration = random.randint(
            settings.ANOMALY_DURATION_MIN, 
            settings.ANOMALY_DURATION_MAX
        )
        
        # Set anomaly parameters based on type
        if self.anomaly_type == "high_power_consumption":
            self.anomaly_power_multiplier = random.uniform(
                settings.ANOMALY_POWER_MULTIPLIER_MIN,
                settings.ANOMALY_POWER_MULTIPLIER_MAX
            )
            self.anomaly_voltage_multiplier = random.uniform(0.95, 1.05)  # Slight voltage variation
            
        elif self.anomaly_type == "voltage_fluctuation":
            self.anomaly_power_multiplier = random.uniform(0.8, 1.2)  # Moderate power variation
            self.anomaly_voltage_multiplier = random.choice([0.8, 1.2])  # ±20% voltage
            
        elif self.anomaly_type == "power_spike":
            self.anomaly_power_multiplier = random.uniform(3.0, 8.0)  # High power spike
            self.anomaly_voltage_multiplier = random.uniform(0.9, 1.1)
            self.anomaly_remaining_duration = min(self.anomaly_remaining_duration, 3)  # Short duration
            
        elif self.anomaly_type == "sustained_high_load":
            self.anomaly_power_multiplier = random.uniform(1.5, 2.5)  # Moderate but sustained
            self.anomaly_voltage_multiplier = random.uniform(0.95, 1.05)
            self.anomaly_remaining_duration = max(self.anomaly_remaining_duration, 8)  # Longer duration
        
        logger.warning(f"Started {self.anomaly_type} anomaly for device {self.device_id} "
                      f"(duration: {self.anomaly_remaining_duration} readings, "
                      f"power_mult: {self.anomaly_power_multiplier:.2f})")
    
    def _end_anomaly(self):
        """End the current anomaly episode"""
        logger.info(f"Ended {self.anomaly_type} anomaly for device {self.device_id}")
        self.anomaly_active = False
        self.anomaly_type = None
        self.anomaly_power_multiplier = 1.0
        self.anomaly_voltage_multiplier = 1.0
        self.anomaly_remaining_duration = 0
    
    def _generate_anomalous_readings(self):
        """Generate readings during an anomaly"""
        import random
        
        # Apply anomaly multipliers with some variation
        base_power = self.base_power * self.anomaly_power_multiplier
        base_voltage = self.base_voltage * self.anomaly_voltage_multiplier
        
        # Add some random variation on top of anomaly
        power_variation = base_power * 0.05 * (random.random() - 0.5) * 2
        voltage_variation = base_voltage * 0.02 * (random.random() - 0.5) * 2
        
        self.current_power = max(0.1, base_power + power_variation)
        self.current_voltage = max(100, base_voltage + voltage_variation)
    
    def _generate_normal_readings(self, power_variation: float = 0.1):
        """Generate normal readings with typical variations"""
        import random
        
        # Power variation (±10% by default)
        power_delta = self.base_power * power_variation * (random.random() - 0.5) * 2
        self.current_power = max(0.1, self.base_power + power_delta)
        
        # Voltage variation (±2% typically)
        voltage_delta = self.base_voltage * 0.02 * (random.random() - 0.5) * 2
        self.current_voltage = max(200, self.base_voltage + voltage_delta)
    
    def get_current_readings(self) -> Dict[str, Any]:
        """Get current device readings"""
        return {
            "device_id": self.device_id,
            "timestamp": self.last_seen.isoformat() + "Z",
            "power": round(self.current_power, 2),
            "voltage": round(self.current_voltage, 1),
            "current": round(self.current_current, 2),
            "energy": round(self.total_energy, 3),
            "status": "online" if self.is_online else "offline",
            "enabled": self.is_enabled
        }
    
    def get_offline_readings(self) -> Dict[str, Any]:
        """Get readings when device is offline"""
        return {
            "device_id": self.device_id,
            "timestamp": self.last_seen.isoformat() + "Z",
            "power": 0.0,
            "voltage": 0.0,
            "current": 0.0,
            "energy": round(self.total_energy, 3),
            "status": "offline",
            "enabled": self.is_enabled
        }
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get complete device information"""
        return {
            "id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "location": self.location,
            "status": "online" if self.is_online else "offline",
            "enabled": self.is_enabled,
            "lastSeen": self.last_seen.isoformat() + "Z",
            "createdAt": self.created_at.isoformat() + "Z",
            "firmware": self.firmware_version,
            "model": self.model,
            "serialNumber": self.serial_number,
            "currentReadings": self.get_current_readings(),
            "basePower": self.base_power,
            "baseVoltage": self.base_voltage
        }
    
    def set_online(self, online: bool):
        """Set device online/offline status"""
        self.is_online = online
        if online:
            self.last_seen = datetime.utcnow()
    
    def set_enabled(self, enabled: bool):
        """Enable/disable device"""
        self.is_enabled = enabled
        if not enabled:
            self.current_power = 0.0
            self.current_current = 0.0


class MockDeviceManager:
    """Manages IoT mock devices"""
    
    def __init__(self):
        self.devices: Dict[str, MockDevice] = {}
        self.mqtt_client: Optional[mqtt.Client] = None
        self.is_connected = False
        
    async def initialize(self):
        """Initialize the device manager"""
        try:
            # Setup MQTT client
            self.mqtt_client = mqtt.Client(
                client_id=f"{settings.MQTT_CLIENT_ID_PREFIX}_manager_{uuid.uuid4().hex[:8]}"
            )
            
            # Set credentials if provided
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(
                    settings.MQTT_USERNAME, 
                    settings.MQTT_PASSWORD
                )
            
            # Set callbacks
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            self.mqtt_client.on_message = self._on_mqtt_message
            
            # Connect to MQTT broker
            self.mqtt_client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                60
            )
            
            # Start MQTT loop
            self.mqtt_client.loop_start()
            
            logger.info("Mock Device Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize device manager: {e}")
            raise
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            logger.info("Connected to MQTT broker")
            
            # Subscribe to command topics for all devices
            for device_id in self.devices.keys():
                command_topic = settings.get_command_topic(device_id)
                client.subscribe(command_topic)
                logger.debug(f"Subscribed to {command_topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        logger.warning("Disconnected from MQTT broker")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages (commands)"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Extract device ID from topic
            # Topic format: energy/devices/{device_id}/commands
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3:
                device_id = topic_parts[2]
                # Schedule the async command handling
                asyncio.create_task(self._handle_device_command(device_id, payload))
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    async def _handle_device_command(self, device_id: str, command: Dict[str, Any]):
        """Handle device command"""
        try:
            if device_id not in self.devices:
                logger.warning(f"Received command for unknown device: {device_id}")
                return
            
            device = self.devices[device_id]
            command_type = command.get("command")
            
            if command_type == "set_power":
                new_power = command.get("parameters", {}).get("power", device.base_power)
                device.base_power = float(new_power)
                logger.info(f"Set power for {device_id} to {new_power}W")
                
            elif command_type == "set_enabled":
                enabled = command.get("parameters", {}).get("enabled", True)
                device.set_enabled(enabled)
                logger.info(f"Set enabled for {device_id} to {enabled}")
                
            elif command_type == "set_online":
                online = command.get("parameters", {}).get("online", True)
                device.set_online(online)
                logger.info(f"Set online for {device_id} to {online}")
                
            else:
                logger.warning(f"Unknown command: {command_type}")
                
        except Exception as e:
            logger.error(f"Error handling device command: {e}")
    
    async def add_device(
        self,
        device_id: str,
        device_type: str,
        name: str,
        location: str,
        base_power: float = 10.0,
        base_voltage: float = 240.0
    ) -> MockDevice:
        """Add a new mock device"""
        try:
            if device_id in self.devices:
                raise ValueError(f"Device {device_id} already exists")
            
            # Create device
            device = MockDevice(
                device_id=device_id,
                device_type=device_type,
                name=name,
                location=location,
                base_power=base_power,
                base_voltage=base_voltage
            )
            
            self.devices[device_id] = device
            
            # Subscribe to command topic if MQTT is connected
            if self.is_connected:
                command_topic = settings.get_command_topic(device_id)
                self.mqtt_client.subscribe(command_topic)
            
            logger.info(f"Added device: {device_id} ({device_type})")
            return device
            
        except Exception as e:
            logger.error(f"Error adding device: {e}")
            raise
    
    async def remove_device(self, device_id: str) -> bool:
        """Remove a mock device"""
        try:
            if device_id not in self.devices:
                return False
            
            # Unsubscribe from command topic
            if self.is_connected:
                command_topic = settings.get_command_topic(device_id)
                self.mqtt_client.unsubscribe(command_topic)
            
            # Remove device
            del self.devices[device_id]
            
            logger.info(f"Removed device: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing device: {e}")
            return False
    
    async def get_device(self, device_id: str) -> Optional[MockDevice]:
        """Get a specific device"""
        return self.devices.get(device_id)
    
    async def get_all_devices(self) -> Dict[str, MockDevice]:
        """Get all devices"""
        return self.devices.copy()
    
    async def publish_device_data(self, device_id: str) -> bool:
        """Publish device data to MQTT"""
        try:
            if not self.is_connected:
                return False
            
            device = self.devices.get(device_id)
            if not device:
                return False
            
            # Update readings with anomaly chance from settings
            readings = device.update_readings(
                power_variation=settings.DATA_VARIATION_PERCENT,
                anomaly_chance=settings.ANOMALY_CHANCE
            )
            
            # Log anomaly events
            if readings.get("anomaly", False):
                logger.warning(f"Anomaly detected in device {device_id}: "
                             f"{readings.get('anomaly_type')} "
                             f"(Power: {readings.get('power')}W, "
                             f"Voltage: {readings.get('voltage')}V)")
            
            # Publish to data topic
            data_topic = settings.get_data_topic(device_id)
            self.mqtt_client.publish(
                data_topic,
                json.dumps(readings),
                qos=1
            )
            
            # Publish status update
            status_topic = settings.get_status_topic(device_id)
            status_data = {
                "device_id": device_id,
                "status": "online" if device.is_online else "offline",
                "enabled": device.is_enabled,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "anomaly_active": readings.get("anomaly", False)
            }
            
            self.mqtt_client.publish(
                status_topic,
                json.dumps(status_data),
                qos=1
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing device data: {e}")
            return False
    
    async def add_default_devices(self):
        """Add default devices for testing"""
        default_devices = [
            {
                "device_id": "mock-hvac-001",
                "device_type": "hvac",
                "name": "HVAC System - Building A",
                "location": "Building A - Floor 2",
                "base_power": 25.0,
                "base_voltage": 240.0
            },
            {
                "device_id": "mock-lighting-001",
                "device_type": "lighting",
                "name": "LED Lighting - Office",
                "location": "Building A - Floor 1",
                "base_power": 8.5,
                "base_voltage": 240.0
            },
            {
                "device_id": "mock-server-001",
                "device_type": "server",
                "name": "Server Rack - Data Center",
                "location": "Building B - Basement",
                "base_power": 45.0,
                "base_voltage": 240.0
            },
            {
                "device_id": "mock-industrial-001",
                "device_type": "industrial",
                "name": "Production Line - Assembly",
                "location": "Factory - Zone A",
                "base_power": 120.0,
                "base_voltage": 480.0
            },
            {
                "device_id": "mock-appliance-001",
                "device_type": "appliance",
                "name": "Kitchen Equipment",
                "location": "Cafeteria - Ground Floor",
                "base_power": 15.0,
                "base_voltage": 240.0
            }
        ]
        
        for device_config in default_devices:
            try:
                await self.add_device(**device_config)
            except Exception as e:
                logger.error(f"Error adding default device {device_config['device_id']}: {e}")
        
        logger.info(f"Added {len(default_devices)} default devices")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            
            logger.info("Device manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
