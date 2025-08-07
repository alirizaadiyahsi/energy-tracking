"""
Performance tests for authentication service using Locust
"""
from locust import HttpUser, task, between
import json
import uuid
import random


class AuthServiceUser(HttpUser):
    """Simulated user for authentication service performance testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Setup before test starts"""
        self.auth_token = None
        self.user_email = f"perftest{uuid.uuid4().hex[:8]}@test.com"
        self.user_password = "PerfTest123!"
    
    @task(1)
    def register_user(self):
        """Test user registration performance"""
        unique_email = f"user{uuid.uuid4().hex[:8]}@test.com"
        user_data = {
            "email": unique_email,
            "password": "TestPass123!",
            "firstName": "Performance",
            "lastName": "Test"
        }
        
        with self.client.post(
            "/auth/register",
            json=user_data,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Registration failed: {response.status_code}")
    
    @task(3)
    def login_user(self):
        """Test user login performance"""
        # First register a user if we haven't already
        if not hasattr(self, '_registered'):
            self._register_test_user()
        
        login_data = {
            "email": self.user_email,
            "password": self.user_password
        }
        
        with self.client.post(
            "/auth/login",
            json=login_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    self.auth_token = response_data.get("accessToken")
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    @task(2)
    def access_profile(self):
        """Test accessing user profile with authentication"""
        if not self.auth_token:
            self.login_user()
        
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            with self.client.get(
                "/auth/me",
                headers=headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 401:
                    # Token might be expired, try to login again
                    self.auth_token = None
                    response.failure("Token expired")
                else:
                    response.failure(f"Profile access failed: {response.status_code}")
    
    @task(1)
    def refresh_token(self):
        """Test token refresh performance"""
        if self.auth_token:
            refresh_data = {"refreshToken": "mock_refresh_token"}
            
            with self.client.post(
                "/auth/refresh",
                json=refresh_data,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        self.auth_token = response_data.get("accessToken")
                        response.success()
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON response")
                else:
                    response.failure(f"Token refresh failed: {response.status_code}")
    
    def _register_test_user(self):
        """Helper method to register a test user"""
        user_data = {
            "email": self.user_email,
            "password": self.user_password,
            "firstName": "Performance",
            "lastName": "Test"
        }
        
        response = self.client.post("/auth/register", json=user_data)
        if response.status_code == 201:
            self._registered = True


class DataIngestionUser(HttpUser):
    """Simulated user for data ingestion performance testing"""
    
    wait_time = between(0.1, 0.5)  # High frequency data ingestion
    
    def on_start(self):
        """Setup before test starts"""
        self.device_id = f"perf_device_{uuid.uuid4().hex[:8]}"
        self.auth_token = self._get_auth_token()
    
    @task(10)
    def send_energy_reading(self):
        """Test energy reading ingestion performance"""
        if not self.auth_token:
            self.auth_token = self._get_auth_token()
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Generate realistic energy reading data
        energy_data = {
            "deviceId": self.device_id,
            "timestamp": "2024-01-15T10:30:00Z",
            "power": round(random.uniform(800, 1500), 2),
            "voltage": round(random.uniform(220, 240), 1),
            "current": round(random.uniform(3.5, 6.5), 2),
            "frequency": 50.0,
            "powerFactor": round(random.uniform(0.85, 0.98), 3)
        }
        
        with self.client.post(
            "/data-ingestion/ingest",
            json=energy_data,
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Data ingestion failed: {response.status_code}")
    
    @task(1)
    def batch_send_readings(self):
        """Test batch data ingestion performance"""
        if not self.auth_token:
            self.auth_token = self._get_auth_token()
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Generate batch of readings
        batch_size = random.randint(5, 20)
        readings = []
        
        for i in range(batch_size):
            reading = {
                "deviceId": f"{self.device_id}_{i}",
                "timestamp": f"2024-01-15T10:{30+i:02d}:00Z",
                "power": round(random.uniform(800, 1500), 2),
                "voltage": round(random.uniform(220, 240), 1),
                "current": round(random.uniform(3.5, 6.5), 2),
                "frequency": 50.0,
                "powerFactor": round(random.uniform(0.85, 0.98), 3)
            }
            readings.append(reading)
        
        batch_data = {"readings": readings}
        
        with self.client.post(
            "/data-ingestion/batch",
            json=batch_data,
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Batch ingestion failed: {response.status_code}")
    
    def _get_auth_token(self):
        """Helper method to get authentication token"""
        # This would normally make a real auth request
        # For performance testing, we might use a pre-generated token
        return "mock_performance_test_token"


class AnalyticsUser(HttpUser):
    """Simulated user for analytics service performance testing"""
    
    wait_time = between(2, 5)  # Analytics requests are less frequent
    
    def on_start(self):
        """Setup before test starts"""
        self.auth_token = self._get_auth_token()
    
    @task(5)
    def get_dashboard_data(self):
        """Test dashboard data retrieval performance"""
        if not self.auth_token:
            self.auth_token = self._get_auth_token()
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        with self.client.get(
            "/analytics/dashboard",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Check response time
                if response.elapsed.total_seconds() > 2.0:
                    response.failure("Dashboard response too slow")
                else:
                    response.success()
            else:
                response.failure(f"Dashboard request failed: {response.status_code}")
    
    @task(3)
    def get_energy_report(self):
        """Test energy report generation performance"""
        if not self.auth_token:
            self.auth_token = self._get_auth_token()
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test different time periods
        time_periods = ["24h", "7d", "30d"]
        period = random.choice(time_periods)
        
        with self.client.get(
            f"/analytics/energy-report?period={period}",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Longer reports can take more time
                max_time = {"24h": 1.0, "7d": 3.0, "30d": 5.0}
                if response.elapsed.total_seconds() > max_time[period]:
                    response.failure(f"Report generation too slow for {period}")
                else:
                    response.success()
            else:
                response.failure(f"Report request failed: {response.status_code}")
    
    @task(2)
    def get_device_analytics(self):
        """Test device-specific analytics performance"""
        if not self.auth_token:
            self.auth_token = self._get_auth_token()
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        device_id = f"test_device_{random.randint(1, 100)}"
        
        with self.client.get(
            f"/analytics/devices/{device_id}/stats",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Device not found is acceptable
                response.success()
            else:
                response.failure(f"Device analytics failed: {response.status_code}")
    
    @task(1)
    def get_comparison_report(self):
        """Test comparison report performance"""
        if not self.auth_token:
            self.auth_token = self._get_auth_token()
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        with self.client.get(
            "/analytics/compare?current=7d&previous=7d",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Comparison reports can be complex
                if response.elapsed.total_seconds() > 4.0:
                    response.failure("Comparison report too slow")
                else:
                    response.success()
            else:
                response.failure(f"Comparison report failed: {response.status_code}")
    
    def _get_auth_token(self):
        """Helper method to get authentication token"""
        return "mock_analytics_test_token"


class APIGatewayUser(HttpUser):
    """Simulated user for API Gateway performance testing"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Setup before test starts"""
        self.auth_token = self._get_auth_token()
    
    @task(3)
    def health_check(self):
        """Test health check endpoint performance"""
        with self.client.get(
            "/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Health check should be very fast
                if response.elapsed.total_seconds() > 0.1:
                    response.failure("Health check too slow")
                else:
                    response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def service_discovery(self):
        """Test service discovery performance"""
        with self.client.get(
            "/services",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Service discovery failed: {response.status_code}")
    
    @task(1)
    def rate_limit_test(self):
        """Test rate limiting behavior"""
        # Make multiple rapid requests to test rate limiting
        for i in range(10):
            with self.client.get(
                "/api/test-endpoint",
                catch_response=True
            ) as response:
                if response.status_code == 429:
                    # Rate limited - this is expected behavior
                    response.success()
                    break
                elif response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Unexpected response: {response.status_code}")
    
    def _get_auth_token(self):
        """Helper method to get authentication token"""
        return "mock_gateway_test_token"


# Custom Locust task sets for different load scenarios
class HighLoadUser(HttpUser):
    """High-load scenario user"""
    
    wait_time = between(0.1, 0.3)  # Very fast requests
    weight = 3  # This user type is 3x more likely to be chosen
    
    @task
    def rapid_requests(self):
        """Make rapid requests to test system under load"""
        endpoints = ["/health", "/auth/me", "/devices", "/analytics/dashboard"]
        endpoint = random.choice(endpoints)
        
        headers = {"Authorization": "Bearer mock_token"}
        
        with self.client.get(
            endpoint,
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:  # 401 is acceptable for mock token
                response.success()
            else:
                response.failure(f"Request failed: {response.status_code}")


class StressTestUser(HttpUser):
    """Stress test scenario user"""
    
    wait_time = between(0, 0.1)  # Almost no wait time
    weight = 1
    
    @task
    def stress_endpoints(self):
        """Stress test critical endpoints"""
        # Simulate high-frequency IoT data
        data = {
            "deviceId": f"stress_device_{random.randint(1, 1000)}",
            "power": random.uniform(100, 2000),
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        with self.client.post(
            "/data-ingestion/ingest",
            json=data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 429]:  # 429 (rate limited) is acceptable
                response.success()
            else:
                response.failure(f"Stress test failed: {response.status_code}")
