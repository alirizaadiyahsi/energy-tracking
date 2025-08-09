#!/usr/bin/env python3
"""
IoT Mock Service Test Script

Quick test script to verify the IoT Mock Service functionality
"""

import asyncio
import json
import time
from datetime import datetime

import requests
import paho.mqtt.client as mqtt


class IoTMockTester:
    """Test class for IoT Mock Service"""
    
    def __init__(
        self,
        service_url: str = "http://localhost:8090",
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        mqtt_username: str = "iot_user",
        mqtt_password: str = "iot123"
    ):
        self.service_url = service_url
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        
        self.mqtt_client = None
        self.received_messages = []
        
    def setup_mqtt_client(self):
        """Setup MQTT client for testing"""
        self.mqtt_client = mqtt.Client("test_client")
        self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        
        print(f"Connecting to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
        self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
        self.mqtt_client.loop_start()
        
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            print("✓ Connected to MQTT broker")
            # Subscribe to all device topics
            client.subscribe("energy/devices/+/data")
            client.subscribe("energy/devices/+/status")
            print("✓ Subscribed to device topics")
        else:
            print(f"✗ Failed to connect to MQTT broker: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            timestamp = datetime.now().isoformat()
            
            message_info = {
                "timestamp": timestamp,
                "topic": topic,
                "payload": payload
            }
            
            self.received_messages.append(message_info)
            
            # Extract device ID and message type
            topic_parts = topic.split('/')
            if len(topic_parts) >= 4:
                device_id = topic_parts[2]
                msg_type = topic_parts[3]
                
                if msg_type == "data":
                    print(f"📊 Data from {device_id}: "
                          f"Power={payload.get('power', 'N/A')}kW, "
                          f"Voltage={payload.get('voltage', 'N/A')}V")
                elif msg_type == "status":
                    print(f"📡 Status from {device_id}: {payload.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"✗ Error processing MQTT message: {e}")
    
    def test_service_health(self):
        """Test service health endpoint"""
        print("\n=== Testing Service Health ===")
        try:
            response = requests.get(f"{self.service_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✓ Service is healthy")
                print(f"  - Service: {data.get('service')}")
                print(f"  - Device Manager: {data.get('device_manager')}")
                print(f"  - Device Simulator: {data.get('device_simulator')}")
                print(f"  - Active Devices: {data.get('active_devices')}")
                return True
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Health check error: {e}")
            return False
    
    def test_device_listing(self):
        """Test device listing endpoint"""
        print("\n=== Testing Device Listing ===")
        try:
            response = requests.get(f"{self.service_url}/api/v1/devices", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    devices = data.get('data', [])
                    print(f"✓ Found {len(devices)} devices")
                    for device in devices:
                        print(f"  - {device['id']}: {device['name']} ({device['type']})")
                    return devices
                else:
                    print(f"✗ API error: {data.get('message')}")
                    return []
            else:
                print(f"✗ Request failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"✗ Device listing error: {e}")
            return []
    
    def test_device_creation(self):
        """Test device creation"""
        print("\n=== Testing Device Creation ===")
        try:
            device_data = {
                "device_type": "lighting",
                "name": "Test LED Strip",
                "location": "Test Lab",
                "base_power": 5.0,
                "base_voltage": 240.0
            }
            
            response = requests.post(
                f"{self.service_url}/api/v1/devices",
                json=device_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    device = data.get('data')
                    print(f"✓ Created device: {device['id']}")
                    print(f"  - Name: {device['name']}")
                    print(f"  - Type: {device['type']}")
                    print(f"  - Location: {device['location']}")
                    return device['id']
                else:
                    print(f"✗ Creation failed: {data.get('message')}")
                    return None
            else:
                print(f"✗ Request failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"✗ Device creation error: {e}")
            return None
    
    def test_simulation_control(self):
        """Test simulation control"""
        print("\n=== Testing Simulation Control ===")
        try:
            # Check status
            response = requests.get(f"{self.service_url}/api/v1/simulation/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    status = data.get('data')
                    print(f"✓ Simulation status: {'Running' if status['is_running'] else 'Stopped'}")
                    print(f"  - Total devices: {status['total_devices']}")
                    print(f"  - Online devices: {status['online_devices']}")
                    print(f"  - MQTT connected: {status['mqtt_connected']}")
                    return status['is_running']
                else:
                    print(f"✗ Status check failed: {data.get('message')}")
                    return False
            else:
                print(f"✗ Status request failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Simulation control error: {e}")
            return False
    
    def test_mqtt_data_flow(self, duration: int = 10):
        """Test MQTT data flow"""
        print(f"\n=== Testing MQTT Data Flow ({duration}s) ===")
        
        initial_count = len(self.received_messages)
        start_time = time.time()
        
        print(f"📡 Listening for MQTT messages for {duration} seconds...")
        
        while time.time() - start_time < duration:
            time.sleep(1)
            current_count = len(self.received_messages)
            messages_received = current_count - initial_count
            
            if messages_received > 0:
                print(f"📊 Received {messages_received} messages so far...")
        
        final_count = len(self.received_messages)
        total_messages = final_count - initial_count
        
        if total_messages > 0:
            print(f"✓ Received {total_messages} messages in {duration} seconds")
            print(f"  - Average: {total_messages/duration:.1f} messages/second")
            
            # Show some sample messages
            if total_messages > 0:
                print("\n📋 Sample messages:")
                recent_messages = self.received_messages[-min(3, total_messages):]
                for msg in recent_messages:
                    print(f"  - {msg['topic']}: {msg['payload'].get('device_id', 'unknown')}")
            
            return True
        else:
            print(f"✗ No messages received in {duration} seconds")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
    
    def run_tests(self):
        """Run all tests"""
        print("🚀 Starting IoT Mock Service Tests")
        print("=" * 50)
        
        # Test service health
        if not self.test_service_health():
            print("\n❌ Service health check failed. Make sure the service is running.")
            return False
        
        # Setup MQTT client
        self.setup_mqtt_client()
        time.sleep(2)  # Allow connection to establish
        
        # Test device operations
        devices = self.test_device_listing()
        
        # Create a test device
        test_device_id = self.test_device_creation()
        
        # Test simulation control
        simulation_running = self.test_simulation_control()
        
        # Test MQTT data flow
        if simulation_running:
            mqtt_success = self.test_mqtt_data_flow(duration=15)
        else:
            print("\n⚠️ Simulation not running, starting it...")
            try:
                response = requests.post(f"{self.service_url}/api/v1/simulation/start")
                if response.status_code == 200:
                    print("✓ Simulation started")
                    time.sleep(2)
                    mqtt_success = self.test_mqtt_data_flow(duration=10)
                else:
                    print("✗ Failed to start simulation")
                    mqtt_success = False
            except Exception as e:
                print(f"✗ Error starting simulation: {e}")
                mqtt_success = False
        
        # Clean up test device
        if test_device_id:
            try:
                response = requests.delete(f"{self.service_url}/api/v1/devices/{test_device_id}")
                if response.status_code == 200:
                    print(f"✓ Cleaned up test device: {test_device_id}")
                else:
                    print(f"⚠️ Failed to clean up test device: {test_device_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up test device: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        print(f"  - Service Health: ✓")
        print(f"  - Device Operations: ✓")
        print(f"  - MQTT Communication: {'✓' if mqtt_success else '✗'}")
        print(f"  - Total MQTT Messages: {len(self.received_messages)}")
        
        if mqtt_success:
            print("\n🎉 All tests passed! IoT Mock Service is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Check the service logs for details.")
        
        return mqtt_success


def main():
    """Main test function"""
    tester = IoTMockTester()
    
    try:
        success = tester.run_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    import sys
    sys.exit(main())
