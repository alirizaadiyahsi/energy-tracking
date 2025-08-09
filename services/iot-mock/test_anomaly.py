#!/usr/bin/env python3
"""
Test script for IoT Mock Service Anomaly functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8090"

def test_service_health():
    """Test if the service is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Service health check failed: {e}")
        return False

def test_get_devices():
    """Test getting all devices"""
    try:
        response = requests.get(f"{BASE_URL}/devices")
        if response.status_code == 200:
            devices = response.json()
            print(f"Found {len(devices.get('data', []))} devices")
            for device in devices.get('data', []):
                print(f"  - {device['device_id']}: {device['name']} ({device['device_type']})")
            return devices.get('data', [])
        else:
            print(f"Failed to get devices: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting devices: {e}")
        return []

def test_trigger_anomaly(device_id=None):
    """Test triggering a manual anomaly"""
    try:
        payload = {}
        if device_id:
            payload["device_id"] = device_id
            payload["anomaly_type"] = "high_power_consumption"
        
        response = requests.post(
            f"{BASE_URL}/trigger-anomaly",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Trigger anomaly response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Anomaly triggered: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Failed to trigger anomaly: {response.text}")
            return False
    except Exception as e:
        print(f"Error triggering anomaly: {e}")
        return False

def test_get_anomaly_status():
    """Test getting anomaly status"""
    try:
        response = requests.get(f"{BASE_URL}/anomaly-status")
        if response.status_code == 200:
            status = response.json()
            print(f"Anomaly status: {json.dumps(status, indent=2)}")
            return True
        else:
            print(f"Failed to get anomaly status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error getting anomaly status: {e}")
        return False

def main():
    """Main test function"""
    print("=== IoT Mock Service Anomaly Test ===")
    
    # Check if service is running
    if not test_service_health():
        print("❌ Service is not running. Please start the IoT Mock Service first.")
        return
    
    print("✅ Service is running")
    
    # Get devices
    devices = test_get_devices()
    if not devices:
        print("❌ No devices found")
        return
    
    print("✅ Devices found")
    
    # Test anomaly status
    print("\n--- Testing anomaly status ---")
    test_get_anomaly_status()
    
    # Trigger manual anomaly for first device
    print("\n--- Testing manual anomaly trigger ---")
    first_device = devices[0]["device_id"]
    if test_trigger_anomaly(first_device):
        print("✅ Manual anomaly triggered successfully")
        
        # Wait a moment and check status again
        time.sleep(2)
        print("\n--- Checking anomaly status after trigger ---")
        test_get_anomaly_status()
    else:
        print("❌ Failed to trigger manual anomaly")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
