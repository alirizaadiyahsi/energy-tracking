"""
MQTT client utilities for IoT device communication
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import paho.mqtt.client as mqtt_client


class MQTTManager:
    """MQTT client manager for IoT device communication"""
    
    def __init__(
        self, 
        broker_host: str, 
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.client_id = client_id or f"energy_tracking_{datetime.now().timestamp()}"
        
        self.client = None
        self.is_connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self.client = mqtt_client.Client(self.client_id)
            
            # Set authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Connect to broker
            result = self.client.connect(self.broker_host, self.broker_port, 60)
            
            if result == mqtt_client.MQTT_ERR_SUCCESS:
                self.client.loop_start()
                self.is_connected = True
                self.logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
                return True
            else:
                self.logger.error(f"Failed to connect to MQTT broker: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client and self.is_connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            self.logger.info("Disconnected from MQTT broker")
    
    async def publish(
        self, 
        topic: str, 
        payload: Dict[str, Any], 
        qos: int = 1,
        retain: bool = False
    ) -> bool:
        """Publish message to MQTT topic"""
        if not self.is_connected:
            self.logger.error("Not connected to MQTT broker")
            return False
        
        try:
            # Add timestamp to payload
            payload_with_timestamp = {
                **payload,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            message = json.dumps(payload_with_timestamp)
            result = self.client.publish(topic, message, qos, retain)
            
            if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published message to {topic}: {message}")
                return True
            else:
                self.logger.error(f"Failed to publish message to {topic}: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing message to {topic}: {e}")
            return False
    
    async def subscribe(
        self, 
        topic: str, 
        handler: Callable[[str, Dict[str, Any]], None],
        qos: int = 1
    ) -> bool:
        """Subscribe to MQTT topic with handler"""
        if not self.is_connected:
            self.logger.error("Not connected to MQTT broker")
            return False
        
        try:
            self.message_handlers[topic] = handler
            result = self.client.subscribe(topic, qos)
            
            if result[0] == mqtt_client.MQTT_ERR_SUCCESS:
                self.logger.info(f"Subscribed to topic: {topic}")
                return True
            else:
                self.logger.error(f"Failed to subscribe to {topic}: {result[0]}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error subscribing to {topic}: {e}")
            return False
    
    async def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from MQTT topic"""
        if not self.is_connected:
            return False
        
        try:
            result = self.client.unsubscribe(topic)
            
            if result[0] == mqtt_client.MQTT_ERR_SUCCESS:
                if topic in self.message_handlers:
                    del self.message_handlers[topic]
                self.logger.info(f"Unsubscribed from topic: {topic}")
                return True
            else:
                self.logger.error(f"Failed to unsubscribe from {topic}: {result[0]}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error unsubscribing from {topic}: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connect callback"""
        if rc == 0:
            self.is_connected = True
            self.logger.info("MQTT client connected successfully")
        else:
            self.is_connected = False
            self.logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        self.is_connected = False
        if rc != 0:
            self.logger.warning("MQTT client disconnected unexpectedly")
        else:
            self.logger.info("MQTT client disconnected")
    
    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Find matching handler
            handler = None
            for pattern, h in self.message_handlers.items():
                if self._topic_matches(topic, pattern):
                    handler = h
                    break
            
            if handler:
                # Run handler in background to avoid blocking
                asyncio.create_task(self._run_handler(handler, topic, payload))
            else:
                self.logger.warning(f"No handler found for topic: {topic}")
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in message from {msg.topic}")
        except Exception as e:
            self.logger.error(f"Error processing message from {msg.topic}: {e}")
    
    async def _run_handler(self, handler: Callable, topic: str, payload: Dict[str, Any]):
        """Run message handler asynchronously"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(topic, payload)
            else:
                handler(topic, payload)
        except Exception as e:
            self.logger.error(f"Error in message handler for {topic}: {e}")
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern (supports MQTT wildcards)"""
        if pattern == topic:
            return True
        
        # Handle + wildcard (single level)
        if '+' in pattern:
            pattern_parts = pattern.split('/')
            topic_parts = topic.split('/')
            
            if len(pattern_parts) != len(topic_parts):
                return False
            
            for p_part, t_part in zip(pattern_parts, topic_parts):
                if p_part != '+' and p_part != t_part:
                    return False
            
            return True
        
        # Handle # wildcard (multi-level)
        if pattern.endswith('#'):
            prefix = pattern[:-1]
            return topic.startswith(prefix)
        
        return False


class DeviceManager:
    """Manager for IoT device communication via MQTT"""
    
    def __init__(self, mqtt_manager: MQTTManager):
        self.mqtt = mqtt_manager
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def register_device(
        self, 
        device_id: str, 
        device_type: str,
        topics: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a new IoT device"""
        device_info = {
            "device_id": device_id,
            "device_type": device_type,
            "topics": topics,
            "metadata": metadata or {},
            "last_seen": None,
            "status": "offline"
        }
        
        self.devices[device_id] = device_info
        
        # Subscribe to device topics
        for topic in topics:
            await self.mqtt.subscribe(
                topic,
                lambda t, p, did=device_id: self._handle_device_message(did, t, p)
            )
        
        self.logger.info(f"Registered device: {device_id} ({device_type})")
    
    async def send_command(
        self, 
        device_id: str, 
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send command to device"""
        if device_id not in self.devices:
            self.logger.error(f"Device not found: {device_id}")
            return False
        
        command_topic = f"devices/{device_id}/commands"
        command_payload = {
            "command": command,
            "parameters": parameters or {},
            "command_id": f"cmd_{datetime.now().timestamp()}"
        }
        
        return await self.mqtt.publish(command_topic, command_payload)
    
    async def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device status"""
        return self.devices.get(device_id)
    
    async def get_all_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered devices"""
        return self.devices.copy()
    
    async def _handle_device_message(self, device_id: str, topic: str, payload: Dict[str, Any]):
        """Handle message from device"""
        if device_id in self.devices:
            # Update device status
            self.devices[device_id]["last_seen"] = datetime.utcnow().isoformat() + "Z"
            self.devices[device_id]["status"] = "online"
            
            # Log device data
            self.logger.debug(f"Received data from {device_id} on {topic}: {payload}")
            
            # Here you could forward the data to other services
            # For example, to the data ingestion service
        else:
            self.logger.warning(f"Received message from unknown device: {device_id}")


class MQTTHealthCheck:
    """Health check for MQTT connection"""
    
    def __init__(self, mqtt_manager: MQTTManager):
        self.mqtt = mqtt_manager
    
    async def check_connection(self) -> Dict[str, Any]:
        """Check MQTT connection health"""
        return {
            "connected": self.mqtt.is_connected,
            "broker": f"{self.mqtt.broker_host}:{self.mqtt.broker_port}",
            "client_id": self.mqtt.client_id
        }
    
    async def ping_broker(self) -> bool:
        """Send ping to broker to test connectivity"""
        if not self.mqtt.is_connected:
            return False
        
        try:
            # Send a test message to a system topic
            test_topic = f"system/health/ping/{self.mqtt.client_id}"
            test_payload = {"ping": "test", "timestamp": datetime.utcnow().isoformat()}
            
            return await self.mqtt.publish(test_topic, test_payload, qos=0)
        except Exception:
            return False
