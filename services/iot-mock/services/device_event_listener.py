"""
Device Event Listener

Listens for device lifecycle events from the main system and automatically
creates/updates/deletes corresponding mock devices
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional

import paho.mqtt.client as mqtt
from core.config import settings

logger = logging.getLogger(__name__)


class DeviceEventListener:
    """Listens for device lifecycle events and manages mock devices"""
    
    def __init__(self, device_manager):
        logger.info("DeviceEventListener constructor called")
        self.device_manager = device_manager
        self.mqtt_client: Optional[mqtt.Client] = None
        self.is_connected = False
        logger.info("About to initialize MQTT client...")
        self._initialize_client()
        logger.info("DeviceEventListener initialization completed")
    
    def _initialize_client(self):
        """Initialize MQTT client for listening to device events"""
        logger.info("Starting DeviceEventListener MQTT client initialization...")
        try:
            self.mqtt_client = mqtt.Client(
                client_id=f"iot-mock-device-listener-{uuid.uuid4().hex[:8]}"
            )
            logger.info(f"Created MQTT client with ID: {self.mqtt_client._client_id}")
            
            # Set credentials
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(
                    settings.MQTT_USERNAME,
                    settings.MQTT_PASSWORD
                )
                logger.info("Set MQTT credentials")
            
            # Set callbacks
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_disconnect = self._on_disconnect
            self.mqtt_client.on_message = self._on_message
            logger.info("Set MQTT callbacks")
            
            # Connect to broker
            logger.info(f"Attempting to connect to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
            self.mqtt_client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                60
            )
            
            # Start the client loop
            self.mqtt_client.loop_start()
            logger.info("MQTT client loop started")
            
        except Exception as e:
            logger.error(f"Failed to initialize device event listener: {e}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            logger.info("Device event listener connected to MQTT broker")
            
            # Subscribe to all device events
            event_topics = [
                "energy/events/devices/+/device.created",
                "energy/events/devices/+/device.updated", 
                "energy/events/devices/+/device.deleted"
            ]
            
            for topic in event_topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to device events: {topic}")
                
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        logger.warning("Device event listener disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming device event messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Extract event information from topic
            # Topic format: energy/events/devices/{device_id}/{event_type}
            topic_parts = topic.split('/')
            if len(topic_parts) >= 5:
                device_id = topic_parts[3]
                event_type = topic_parts[4]
                
                # Schedule async event handling in a thread-safe way
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we have a running loop, schedule the coroutine
                        asyncio.ensure_future(self._handle_device_event(event_type, device_id, payload))
                    else:
                        # If no loop is running, create a new one
                        asyncio.run(self._handle_device_event(event_type, device_id, payload))
                except RuntimeError:
                    # No event loop available, create a new one in a thread
                    import threading
                    def run_async():
                        asyncio.run(self._handle_device_event(event_type, device_id, payload))
                    thread = threading.Thread(target=run_async)
                    thread.daemon = True
                    thread.start()
            
        except Exception as e:
            logger.error(f"Error processing device event message: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _handle_device_event(self, event_type: str, device_id: str, payload: Dict[str, Any]):
        """Handle device lifecycle events"""
        try:
            device_data = payload.get("device_data", {})
            
            if event_type == "device.created":
                await self._handle_device_created(device_id, device_data)
            elif event_type == "device.updated":
                await self._handle_device_updated(device_id, device_data)
            elif event_type == "device.deleted":
                await self._handle_device_deleted(device_id, device_data)
            else:
                logger.warning(f"Unknown device event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling device event {event_type} for {device_id}: {e}")
    
    async def _handle_device_created(self, device_id: str, device_data: Dict[str, Any]):
        """Handle device created event"""
        try:
            # Generate mock device ID based on real device ID
            mock_device_id = f"mock-real-{device_id}"
            
            logger.error(f"DEBUG: Processing device created event for {device_id}")
            logger.error(f"DEBUG: Device data received: {device_data}")
            
            # Check if mock device already exists
            existing_device = await self.device_manager.get_device(mock_device_id)
            if existing_device:
                logger.info(f"Mock device {mock_device_id} already exists, skipping creation")
                return
            
            # Map device data to mock device format
            mock_device_data = self._map_device_data_to_mock(device_data)
            logger.error(f"DEBUG: Mapped mock device data: {mock_device_data}")
            
            # Create mock device
            await self.device_manager.add_device(
                device_id=mock_device_id,
                **mock_device_data
            )
            
            logger.info(f"Created mock device {mock_device_id} for real device: {device_id}")
            
        except Exception as e:
            logger.error(f"Error creating mock device for {device_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _handle_device_updated(self, device_id: str, device_data: Dict[str, Any]):
        """Handle device updated event"""
        try:
            # Generate mock device ID based on real device ID
            mock_device_id = f"mock-real-{device_id}"
            
            # Check if mock device exists
            existing_device = await self.device_manager.get_device(mock_device_id)
            if not existing_device:
                logger.info(f"Mock device {mock_device_id} not found, creating new one")
                await self._handle_device_created(device_id, device_data)
                return
            
            # Update mock device properties
            mock_device = existing_device
            
            # Update basic properties
            if "name" in device_data:
                mock_device.name = device_data["name"]
            if "location" in device_data:
                mock_device.location = device_data["location"]
            if "status" in device_data:
                status = device_data["status"]
                mock_device.set_online(status == "online")
                mock_device.set_enabled(status != "offline")
            
            logger.info(f"Updated mock device {mock_device_id} for real device: {device_id}")
            
        except Exception as e:
            logger.error(f"Error updating mock device {device_id}: {e}")
    
    async def _handle_device_deleted(self, device_id: str, device_data: Dict[str, Any]):
        """Handle device deleted event"""
        try:
            # Generate mock device ID based on real device ID
            mock_device_id = f"mock-real-{device_id}"
            
            # Remove mock device if it exists
            success = await self.device_manager.remove_device(mock_device_id)
            if success:
                logger.info(f"Deleted mock device {mock_device_id} for real device: {device_id}")
            else:
                logger.info(f"Mock device {mock_device_id} not found for deletion")
                
        except Exception as e:
            logger.error(f"Error deleting mock device {device_id}: {e}")
    
    def _map_device_data_to_mock(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map real device data to mock device format"""
        # Default mock device parameters based on device type
        device_type = device_data.get("type", "sensor").lower()
        
        # Device type mapping and default parameters
        type_defaults = {
            "hvac": {"base_power": 25.0, "base_voltage": 240.0},
            "lighting": {"base_power": 8.5, "base_voltage": 240.0},
            "server": {"base_power": 45.0, "base_voltage": 240.0},
            "industrial": {"base_power": 120.0, "base_voltage": 480.0},
            "appliance": {"base_power": 15.0, "base_voltage": 240.0},
            "sensor": {"base_power": 2.0, "base_voltage": 12.0},
            "meter": {"base_power": 5.0, "base_voltage": 240.0},
            "gateway": {"base_power": 10.0, "base_voltage": 240.0},
            "controller": {"base_power": 12.0, "base_voltage": 240.0}
        }
        
        defaults = type_defaults.get(device_type, {"base_power": 10.0, "base_voltage": 240.0})
        
        return {
            "device_type": device_type,
            "name": device_data.get("name", f"Mock {device_type.title()}"),
            "location": device_data.get("location", "Unknown Location"),
            "base_power": device_data.get("base_power") or defaults["base_power"],
            "base_voltage": device_data.get("base_voltage") or defaults["base_voltage"]
        }
    
    def cleanup(self):
        """Cleanup MQTT resources"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            logger.info("Device event listener cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
