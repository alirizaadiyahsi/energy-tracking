"""
Device Event Publisher

Publishes device lifecycle events to MQTT for other services to consume
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

import paho.mqtt.client as mqtt
from core.config import settings

logger = logging.getLogger(__name__)


class DeviceEventType(str, Enum):
    """Device event types"""
    CREATED = "device.created"
    UPDATED = "device.updated"
    DELETED = "device.deleted"
    STATUS_CHANGED = "device.status_changed"


class DeviceEventPublisher:
    """Publishes device lifecycle events via MQTT"""
    
    def __init__(self):
        self.mqtt_client: Optional[mqtt.Client] = None
        self.is_connected = False
        self._client_initialized = False
    
    def _initialize_client(self):
        """Initialize MQTT client (lazy initialization)"""
        if self._client_initialized:
            logger.info("MQTT client already initialized")
            return
            
        logger.info("Starting MQTT client initialization...")
        try:
            self.mqtt_client = mqtt.Client(
                client_id=f"data-ingestion-device-events-{id(self)}"
            )
            logger.info(f"Created MQTT client with ID: {self.mqtt_client._client_id}")
            
            # Set credentials
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(
                    settings.MQTT_USERNAME,
                    settings.MQTT_PASSWORD
                )
                logger.info("Set MQTT username and password")
            
            # Set callbacks
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_disconnect = self._on_disconnect
            self.mqtt_client.on_publish = self._on_publish
            logger.info("Set MQTT callbacks")
            
            self._client_initialized = True
            logger.info("MQTT client initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
            raise
    
    def _ensure_connected(self, timeout=5):
        """Ensure MQTT client is connected"""
        logger.error(f"DEBUG: Ensuring MQTT connection (current status: connected={self.is_connected})")
        
        if not self._client_initialized:
            logger.error("DEBUG: MQTT client not initialized, initializing now...")
            self._initialize_client()
            
        if not self.is_connected and self.mqtt_client:
            try:
                logger.error(f"DEBUG: Attempting to connect to MQTT broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
                
                # Connect to broker
                self.mqtt_client.connect(
                    settings.MQTT_BROKER,
                    settings.MQTT_PORT,
                    settings.MQTT_KEEPALIVE
                )
                logger.error("DEBUG: MQTT connect() call completed")
                
                # Start the client loop
                self.mqtt_client.loop_start()
                logger.error("DEBUG: MQTT loop_start() completed, waiting for connection...")
                
                # Wait for connection to be established
                import time
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if not self.is_connected:
                    logger.error(f"DEBUG: MQTT connection timeout after {timeout} seconds")
                else:
                    logger.error("DEBUG: MQTT connection established successfully")
                
            except Exception as e:
                logger.error(f"DEBUG: Exception during MQTT connection: {e}")
                import traceback
                logger.error(f"DEBUG: Traceback: {traceback.format_exc()}")
                return False
        elif self.is_connected:
            logger.info("MQTT client is already connected")
        
        return self.is_connected
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        logger.error(f"DEBUG: MQTT connection callback called with rc={rc}")
        if rc == 0:
            self.is_connected = True
            logger.error("DEBUG: Device event publisher connected to MQTT broker successfully")
        else:
            logger.error(f"DEBUG: Failed to connect to MQTT broker with error code: {rc}")
            # MQTT error codes: 0=success, 1=incorrect protocol version, 2=invalid client identifier, 3=server unavailable, 4=bad username or password, 5=not authorized
            error_messages = {
                1: "incorrect protocol version",
                2: "invalid client identifier", 
                3: "server unavailable",
                4: "bad username or password",
                5: "not authorized"
            }
            error_msg = error_messages.get(rc, f"unknown error code {rc}")
            logger.error(f"DEBUG: MQTT connection error: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        logger.warning("Device event publisher disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        logger.debug(f"Device event published successfully: {mid}")
    
    async def publish_device_event(
        self,
        event_type: DeviceEventType,
        device_id: str,
        device_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Publish a device lifecycle event"""
        try:
            # Ensure connection before publishing
            if not self._ensure_connected():
                logger.warning("MQTT client not connected, cannot publish device event")
                return False
            
            # Create event payload
            event_payload = {
                "event_type": event_type.value,
                "device_id": device_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "device_data": device_data,
                "metadata": metadata or {}
            }
            
            # Determine topic
            topic = f"energy/events/devices/{device_id}/{event_type.value}"
            
            # Publish event
            result = self.mqtt_client.publish(
                topic,
                json.dumps(event_payload),
                qos=1,  # At least once delivery
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published device event: {event_type.value} for device {device_id}")
                return True
            else:
                logger.error(f"Failed to publish device event: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing device event: {e}")
            return False
    
    async def publish_device_created(self, device_id: str, device_data: Dict[str, Any]) -> bool:
        """Publish device created event"""
        return await self.publish_device_event(
            DeviceEventType.CREATED,
            device_id,
            device_data,
            {"source": "data-ingestion-service"}
        )
    
    async def publish_device_updated(self, device_id: str, device_data: Dict[str, Any]) -> bool:
        """Publish device updated event"""
        return await self.publish_device_event(
            DeviceEventType.UPDATED,
            device_id,
            device_data,
            {"source": "data-ingestion-service"}
        )
    
    async def publish_device_deleted(self, device_id: str, device_data: Dict[str, Any]) -> bool:
        """Publish device deleted event"""
        return await self.publish_device_event(
            DeviceEventType.DELETED,
            device_id,
            device_data,
            {"source": "data-ingestion-service"}
        )
    
    def cleanup(self):
        """Cleanup MQTT resources"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            logger.info("Device event publisher cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global instance
device_event_publisher = DeviceEventPublisher()
