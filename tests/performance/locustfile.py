"""
Performance Tests for Energy Tracking System
Uses Locust for load testing and performance benchmarking
"""

import random
import json
from locust import HttpUser, task, between
from typing import Dict, Any


class EnergyTrackingUser(HttpUser):
    """Simulates a user interacting with the Energy Tracking System"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Called when a user starts - perform login"""
        self.login()
        self.device_id = None
    
    def login(self):
        """Login to get authentication token"""
        login_data = {
            "username": f"test_user_{random.randint(1, 1000)}@example.com",
            "password": "testpassword123"
        }
        
        # First, create the user if it doesn't exist
        self.client.post("/auth/register", json={
            "email": login_data["username"],
            "password": login_data["password"],
            "full_name": "Test User",
            "role": "user"
        })
        
        # Then login
        with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
            else:
                response.failure(f"Login failed: {response.text}")
    
    @task(10)
    def view_dashboard(self):
        """View dashboard - most common operation"""
        with self.client.get("/dashboard", headers=getattr(self, 'headers', {}), catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard view failed: {response.status_code}")
    
    @task(8)
    def get_devices(self):
        """Get list of devices"""
        with self.client.get("/devices", headers=getattr(self, 'headers', {}), catch_response=True) as response:
            if response.status_code == 200:
                devices = response.json()
                if devices and len(devices) > 0:
                    self.device_id = devices[0]["id"]
                response.success()
            else:
                response.failure(f"Get devices failed: {response.status_code}")
    
    @task(6)
    def get_energy_data(self):
        """Get energy consumption data"""
        params = {
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-31T23:59:59",
            "granularity": "day"
        }
        
        if hasattr(self, 'device_id') and self.device_id:
            params["device_id"] = self.device_id
        
        with self.client.get("/analytics/energy-consumption", 
                           params=params, 
                           headers=getattr(self, 'headers', {}), 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get energy data failed: {response.status_code}")
    
    @task(4)
    def create_device(self):
        """Create a new device"""
        device_data = {
            "name": f"Test Device {random.randint(1, 10000)}",
            "type": random.choice(["smart_meter", "solar_panel", "battery", "hvac"]),
            "location": f"Room {random.randint(1, 100)}",
            "metadata": {
                "manufacturer": random.choice(["Tesla", "Schneider", "Siemens", "ABB"]),
                "model": f"Model-{random.randint(100, 999)}",
                "install_date": "2024-01-01"
            }
        }
        
        with self.client.post("/devices", 
                            json=device_data, 
                            headers=getattr(self, 'headers', {}), 
                            catch_response=True) as response:
            if response.status_code in [200, 201]:
                device = response.json()
                self.device_id = device.get("id")
                response.success()
            else:
                response.failure(f"Create device failed: {response.status_code}")
    
    @task(3)
    def submit_energy_data(self):
        """Submit energy consumption data"""
        if not hasattr(self, 'device_id') or not self.device_id:
            return
        
        energy_data = {
            "device_id": self.device_id,
            "timestamp": "2024-01-15T12:00:00Z",
            "energy_consumed": round(random.uniform(10.0, 100.0), 2),
            "energy_produced": round(random.uniform(0.0, 50.0), 2),
            "power": round(random.uniform(1000.0, 5000.0), 2),
            "voltage": round(random.uniform(220.0, 240.0), 2),
            "current": round(random.uniform(5.0, 25.0), 2),
            "frequency": 50.0
        }
        
        with self.client.post("/data-ingestion/energy", 
                            json=energy_data, 
                            headers=getattr(self, 'headers', {}), 
                            catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Submit energy data failed: {response.status_code}")
    
    @task(2)
    def get_analytics_report(self):
        """Get analytics report"""
        params = {
            "report_type": random.choice(["daily", "weekly", "monthly"]),
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        
        with self.client.get("/analytics/report", 
                           params=params, 
                           headers=getattr(self, 'headers', {}), 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get analytics report failed: {response.status_code}")
    
    @task(2)
    def get_alerts(self):
        """Get user alerts"""
        with self.client.get("/notifications/alerts", 
                           headers=getattr(self, 'headers', {}), 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get alerts failed: {response.status_code}")
    
    @task(1)
    def update_device(self):
        """Update device information"""
        if not hasattr(self, 'device_id') or not self.device_id:
            return
        
        update_data = {
            "name": f"Updated Device {random.randint(1, 10000)}",
            "location": f"Updated Room {random.randint(1, 100)}",
            "metadata": {
                "last_maintenance": "2024-01-15",
                "status": random.choice(["active", "maintenance", "offline"])
            }
        }
        
        with self.client.put(f"/devices/{self.device_id}", 
                           json=update_data, 
                           headers=getattr(self, 'headers', {}), 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Update device failed: {response.status_code}")


class AdminUser(HttpUser):
    """Simulates an admin user with higher privileges"""
    
    wait_time = between(2, 8)
    weight = 1  # Admin users are less common
    
    def on_start(self):
        """Login as admin"""
        self.login_admin()
    
    def login_admin(self):
        """Login as admin user"""
        login_data = {
            "username": "admin@energytracking.com",
            "password": "adminpassword123"
        }
        
        with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
            else:
                response.failure(f"Admin login failed: {response.text}")
    
    @task(5)
    def get_all_users(self):
        """Admin: Get all users"""
        with self.client.get("/admin/users", 
                           headers=getattr(self, 'headers', {}), 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get all users failed: {response.status_code}")
    
    @task(3)
    def get_system_metrics(self):
        """Admin: Get system metrics"""
        with self.client.get("/admin/metrics", 
                           headers=getattr(self, 'headers', {}), 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get system metrics failed: {response.status_code}")
    
    @task(2)
    def get_audit_logs(self):
        """Admin: Get audit logs"""
        params = {
            "limit": 100,
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        
        with self.client.get("/admin/audit-logs", 
                           params=params,
                           headers=getattr(self, 'headers', {}), 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get audit logs failed: {response.status_code}")


class ApiOnlyUser(HttpUser):
    """Simulates API-only usage (IoT devices, integrations)"""
    
    wait_time = between(0.1, 1)  # IoT devices send data more frequently
    weight = 3  # More API-only users
    
    def on_start(self):
        """Setup API authentication"""
        self.device_id = f"iot_device_{random.randint(1000, 9999)}"
        self.api_key = "test-api-key-123"
        self.headers = {"X-API-Key": self.api_key}
    
    @task(10)
    def send_sensor_data(self):
        """Send sensor data via API"""
        sensor_data = {
            "device_id": self.device_id,
            "timestamp": "2024-01-15T12:00:00Z",
            "measurements": {
                "temperature": round(random.uniform(20.0, 35.0), 1),
                "humidity": round(random.uniform(30.0, 80.0), 1),
                "power": round(random.uniform(1000.0, 5000.0), 2),
                "energy": round(random.uniform(10.0, 100.0), 2)
            }
        }
        
        with self.client.post("/api/v1/sensors/data", 
                            json=sensor_data, 
                            headers=self.headers, 
                            catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Send sensor data failed: {response.status_code}")
    
    @task(2)
    def get_device_status(self):
        """Get device status via API"""
        with self.client.get(f"/api/v1/devices/{self.device_id}/status", 
                           headers=self.headers, 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get device status failed: {response.status_code}")


# Test scenarios for different load patterns
class PeakLoadUser(EnergyTrackingUser):
    """Simulates peak load conditions"""
    wait_time = between(0.1, 0.5)  # Very frequent requests
    
    @task(20)
    def rapid_dashboard_refresh(self):
        """Rapid dashboard refreshes during peak times"""
        super().view_dashboard()
    
    @task(15)
    def frequent_data_requests(self):
        """Frequent data requests"""
        super().get_energy_data()


class StressTestUser(HttpUser):
    """Stress testing with edge cases"""
    wait_time = between(0, 0.1)
    
    @task
    def stress_health_check(self):
        """Rapid health check requests"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task
    def stress_large_data_request(self):
        """Request large amounts of data"""
        params = {
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2024-12-31T23:59:59",
            "granularity": "hour"  # Large dataset
        }
        
        with self.client.get("/analytics/energy-consumption", 
                           params=params, 
                           catch_response=True) as response:
            if response.status_code in [200, 400, 413]:  # Accept timeout/too large responses
                response.success()
            else:
                response.failure(f"Large data request failed: {response.status_code}")
