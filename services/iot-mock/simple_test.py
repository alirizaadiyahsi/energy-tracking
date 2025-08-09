#!/usr/bin/env python3
"""
Simple IoT Mock Service Tester

Test the IoT Mock Service API endpoints without external dependencies
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime


def make_request(url, method='GET', data=None, timeout=10):
    """Make HTTP request"""
    try:
        if data:
            data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', 'application/json')
        
        if method != 'GET':
            req.get_method = lambda: method
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return {
                'status_code': response.getcode(),
                'data': json.loads(response.read().decode('utf-8'))
            }
    except urllib.error.HTTPError as e:
        return {
            'status_code': e.code,
            'data': {'error': str(e)}
        }
    except Exception as e:
        return {
            'status_code': 0,
            'data': {'error': str(e)}
        }


def test_health(base_url):
    """Test service health"""
    print("🏥 Testing service health...")
    
    result = make_request(f"{base_url}/health")
    
    if result['status_code'] == 200:
        data = result['data']
        print(f"✅ Service is healthy")
        print(f"   - Status: {data.get('status')}")
        print(f"   - Active devices: {data.get('active_devices', 'N/A')}")
        print(f"   - Device simulator: {data.get('device_simulator', 'N/A')}")
        return True
    else:
        print(f"❌ Health check failed: {result['status_code']}")
        return False


def test_devices(base_url):
    """Test device endpoints"""
    print("\n📱 Testing device endpoints...")
    
    # List devices
    result = make_request(f"{base_url}/api/v1/devices")
    
    if result['status_code'] == 200 and result['data'].get('success'):
        devices = result['data'].get('data', [])
        print(f"✅ Found {len(devices)} devices")
        
        for device in devices[:3]:  # Show first 3 devices
            print(f"   - {device['id']}: {device['name']} ({device['type']})")
        
        if devices:
            # Test getting a specific device
            device_id = devices[0]['id']
            result = make_request(f"{base_url}/api/v1/devices/{device_id}")
            
            if result['status_code'] == 200 and result['data'].get('success'):
                device = result['data']['data']
                print(f"✅ Retrieved device details for {device_id}")
                print(f"   - Name: {device['name']}")
                print(f"   - Location: {device['location']}")
                print(f"   - Status: {device['status']}")
            else:
                print(f"❌ Failed to get device details: {result['status_code']}")
        
        return True
    else:
        print(f"❌ Failed to list devices: {result['status_code']}")
        return False


def test_simulation(base_url):
    """Test simulation endpoints"""
    print("\n🎮 Testing simulation endpoints...")
    
    # Get simulation status
    result = make_request(f"{base_url}/api/v1/simulation/status")
    
    if result['status_code'] == 200 and result['data'].get('success'):
        status = result['data']['data']
        print(f"✅ Simulation status retrieved")
        print(f"   - Running: {status['is_running']}")
        print(f"   - Total devices: {status['total_devices']}")
        print(f"   - Online devices: {status['online_devices']}")
        print(f"   - MQTT connected: {status['mqtt_connected']}")
        return status['is_running']
    else:
        print(f"❌ Failed to get simulation status: {result['status_code']}")
        return False


def test_device_creation(base_url):
    """Test device creation"""
    print("\n🔧 Testing device creation...")
    
    device_data = {
        "device_type": "lighting",
        "name": "Test LED Panel",
        "location": "Test Room",
        "base_power": 12.5,
        "base_voltage": 240.0
    }
    
    result = make_request(f"{base_url}/api/v1/devices", method='POST', data=device_data)
    
    if result['status_code'] == 200 and result['data'].get('success'):
        device = result['data']['data']
        device_id = device['id']
        print(f"✅ Created test device: {device_id}")
        print(f"   - Name: {device['name']}")
        print(f"   - Type: {device['type']}")
        
        # Clean up - delete the test device
        delete_result = make_request(f"{base_url}/api/v1/devices/{device_id}", method='DELETE')
        
        if delete_result['status_code'] == 200:
            print(f"✅ Cleaned up test device: {device_id}")
        else:
            print(f"⚠️ Failed to clean up test device: {device_id}")
        
        return True
    else:
        print(f"❌ Failed to create device: {result['status_code']}")
        if 'data' in result and 'message' in result['data']:
            print(f"   Error: {result['data']['message']}")
        return False


def test_device_readings(base_url):
    """Test device readings"""
    print("\n📊 Testing device readings...")
    
    # First get list of devices
    result = make_request(f"{base_url}/api/v1/devices")
    
    if result['status_code'] == 200 and result['data'].get('success'):
        devices = result['data'].get('data', [])
        
        if devices:
            device_id = devices[0]['id']
            
            # Get readings
            result = make_request(f"{base_url}/api/v1/devices/{device_id}/readings")
            
            if result['status_code'] == 200 and result['data'].get('success'):
                readings = result['data']['data']
                print(f"✅ Retrieved readings for {device_id}")
                print(f"   - Power: {readings.get('power', 'N/A')}kW")
                print(f"   - Voltage: {readings.get('voltage', 'N/A')}V")
                print(f"   - Current: {readings.get('current', 'N/A')}A")
                print(f"   - Energy: {readings.get('energy', 'N/A')}kWh")
                print(f"   - Status: {readings.get('status', 'N/A')}")
                return True
            else:
                print(f"❌ Failed to get readings: {result['status_code']}")
                return False
        else:
            print("⚠️ No devices available for readings test")
            return True
    else:
        print(f"❌ Failed to list devices for readings test: {result['status_code']}")
        return False


def main():
    """Main test function"""
    base_url = "http://localhost:8090"
    
    print("🚀 IoT Mock Service API Tester")
    print("=" * 40)
    print(f"Testing service at: {base_url}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    tests = [
        ("Health Check", lambda: test_health(base_url)),
        ("Device Listing", lambda: test_devices(base_url)),
        ("Simulation Status", lambda: test_simulation(base_url)),
        ("Device Creation", lambda: test_device_creation(base_url)),
        ("Device Readings", lambda: test_device_readings(base_url)),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 Test Summary:")
    print("-" * 20)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! IoT Mock Service is working correctly.")
        print("\n💡 Try these URLs in your browser:")
        print(f"   - API Docs: {base_url}/docs")
        print(f"   - Health: {base_url}/health")
        print(f"   - Devices: {base_url}/api/v1/devices")
        return 0
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed.")
        print("Check that the service is running and accessible.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
