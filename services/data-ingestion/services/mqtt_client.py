"""
MQTT Client for Data Ingestion Service
Subscribes to IoT device data and stores it in database
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

import paho.mqtt.client as mqtt_client
from core.config import settings
from core.database import engine
from sqlalchemy import text
from .influx_service import influx_service

logger = logging.getLogger(__name__)


class MQTTDataIngestion:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.device_data: Dict[str, Any] = {}
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the MQTT broker"""
        print(f"MQTT on_connect called with rc={rc}")  # Debug print
        if rc == 0:
            self.is_connected = True
            print("Connected to MQTT broker successfully")  # Debug print
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to device data topics
            for topic in settings.MQTT_TOPICS:
                result = client.subscribe(topic)
                print(f"Subscribed to topic: {topic}, result: {result}")  # Debug print
                logger.info(f"Subscribed to topic: {topic}, result: {result}")
                
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}")  # Debug print
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")
            # Log the meaning of return codes
            rc_meanings = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier", 
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised"
            }
            error_meaning = rc_meanings.get(rc, 'Unknown error')
            print(f"Connection error meaning: {error_meaning}")  # Debug print
            logger.error(f"Connection error meaning: {error_meaning}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the MQTT broker"""
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT broker, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            print(f"MQTT message received on topic: {msg.topic}")  # Debug print
            # Parse the JSON message
            payload = json.loads(msg.payload.decode())
            topic_parts = msg.topic.split('/')
            
            if len(topic_parts) >= 4:
                device_id = topic_parts[2]  # energy/devices/{device_id}/data
                topic_type = topic_parts[3]  # data, status, alerts
                
                # Only store device readings from 'data' topics, ignore 'status' topics
                if topic_type == "data":
                    # Store the latest reading for this device
                    self.device_data[device_id] = {
                        **payload,
                        'topic': msg.topic,
                        'received_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    print(f"Updated device {device_id} data: power={payload.get('power', 0)}W")  # Debug print
                    logger.debug(f"Received data from {device_id}: power={payload.get('power', 0)}W")
                    
                    # Store the reading in InfluxDB using threading to avoid blocking MQTT callback
                    try:
                        import threading
                        def store_in_background():
                            try:
                                import asyncio
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(
                                    influx_service.write_energy_reading(device_id, payload)
                                )
                                loop.close()
                                print(f"Successfully stored reading for {device_id} in InfluxDB")
                                logger.debug(f"Stored reading for {device_id} in InfluxDB")
                            except Exception as e:
                                print(f"Failed to store reading for {device_id} in InfluxDB: {e}")
                                logger.error(f"Failed to store reading for {device_id} in InfluxDB: {e}")
                        
                        thread = threading.Thread(target=store_in_background, daemon=True)
                        thread.start()
                    except Exception as e:
                        logger.error(f"Failed to start background thread for InfluxDB storage: {e}")
                    
                    logger.info(f"Updated device {device_id} data: power={payload.get('power', 0)}W")
                else:
                    print(f"Ignoring {topic_type} message for {device_id}")  # Debug print
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON message: {e}")  # Debug print
            logger.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")  # Debug print
            logger.error(f"Error processing MQTT message: {e}")
    
    async def store_reading(self, device_id: str, data: Dict[str, Any]):
        """Store reading in InfluxDB"""
        try:
            await influx_service.write_energy_reading(device_id, data)
            logger.info(f"Stored reading for {device_id} in InfluxDB: {data}")
        except Exception as e:
            logger.error(f"Error storing reading in InfluxDB: {e}")
    
    def start(self):
        """Start the MQTT client"""
        try:
            print("Initializing MQTT client...")  # Debug print
            logger.info("Initializing MQTT client...")
            self.client = mqtt_client.Client()
            
            # Set username and password if provided
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                print(f"Setting MQTT credentials for user: {settings.MQTT_USERNAME}")  # Debug print
                logger.info(f"Setting MQTT credentials for user: {settings.MQTT_USERNAME}")
                self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # Connect to broker
            print(f"Connecting to MQTT broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}")  # Debug print
            logger.info(f"Connecting to MQTT broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
            result = self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, settings.MQTT_KEEPALIVE)
            print(f"MQTT connect result: {result}")  # Debug print
            logger.info(f"MQTT connect result: {result}")
            
            # Start the network loop in a separate thread
            self.client.loop_start()
            
            # Wait a moment for connection to establish
            import time
            time.sleep(2)
            
            # Check connection status
            if self.is_connected:
                print("MQTT client connected successfully")  # Debug print
                logger.info("MQTT client connected successfully")
            else:
                print("MQTT client started but not yet connected")  # Debug print
                logger.warning("MQTT client started but not yet connected")
            
            print("MQTT client started successfully")  # Debug print
            logger.info("MQTT client started successfully")
            
        except Exception as e:
            print(f"Failed to start MQTT client: {e}")  # Debug print
            logger.error(f"Failed to start MQTT client: {e}")
            import traceback
            print(traceback.format_exc())  # Debug print
            logger.error(traceback.format_exc())
    
    def stop(self):
        """Stop the MQTT client"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client stopped")
    
    def get_device_data(self) -> Dict[str, Any]:
        """Get the latest device data"""
        return self.device_data
    
    def get_devices(self) -> list:
        """Get devices in API format"""
        devices = []
        for device_id, data in self.device_data.items():
            devices.append({
                "id": device_id,
                "name": self.get_device_name(device_id),
                "type": self.get_device_type(device_id),
                "location": self.get_device_location(device_id),
                "status": data.get("status", "online"),
                "lastSeen": data.get("timestamp", data.get("received_at")),
                "power": data.get("power", 0),
                "energy": data.get("energy", 0),
                "voltage": data.get("voltage", 0),
                "current": data.get("current", 0),
                "enabled": data.get("enabled", True),
                "createdAt": data.get("received_at"),
            })
        return devices
    
    def get_device_name(self, device_id: str) -> str:
        """Get friendly name for device"""
        name_mapping = {
            "mock-hvac-001": "HVAC System - Building A",
            "mock-lighting-001": "LED Lighting - Office", 
            "mock-server-001": "Server Rack - Data Center",
            "mock-industrial-001": "Production Line - Assembly",
            "mock-appliance-001": "Kitchen Equipment"
        }
        return name_mapping.get(device_id, f"Device {device_id}")
    
    def get_device_type(self, device_id: str) -> str:
        """Get device type from device ID"""
        if "hvac" in device_id:
            return "hvac"
        elif "lighting" in device_id:
            return "lighting"
        elif "server" in device_id:
            return "server"
        elif "industrial" in device_id:
            return "industrial"
        elif "appliance" in device_id:
            return "appliance"
        return "unknown"
    
    def get_device_location(self, device_id: str) -> str:
        """Get device location from device ID"""
        location_mapping = {
            "mock-hvac-001": "Building A - Floor 2",
            "mock-lighting-001": "Building A - Floor 1",
            "mock-server-001": "Building B - Basement", 
            "mock-industrial-001": "Factory - Zone A",
            "mock-appliance-001": "Cafeteria - Ground Floor"
        }
        return location_mapping.get(device_id, "Unknown Location")


    def get_device_readings(self, device_id: str, limit: int = 100) -> list:
        """Get readings for a specific device"""
        device_data = self.device_data.get(device_id)
        if not device_data:
            return []
        
        # For now, return the latest reading
        # In a real implementation, you'd query a database for historical data
        readings = [{
            "id": f"reading-{device_id}-0",
            "deviceId": device_id,
            "timestamp": device_data.get("timestamp", device_data.get("received_at")),
            "power": device_data.get("power", 0),
            "energy": device_data.get("energy", 0),
            "voltage": device_data.get("voltage", 0),
            "current": device_data.get("current", 0),
        }]
        
        return readings


# Global MQTT client instance
mqtt_ingestion = MQTTDataIngestion()
