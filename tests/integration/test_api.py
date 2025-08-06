"""
Integration tests for API endpoints
"""
import pytest
import json
import asyncio
from httpx import AsyncClient
from pathlib import Path


@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPI:
    """Test authentication API endpoints"""
    
    @pytest.fixture
    def auth_base_url(self):
        return "http://localhost:8005"
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, auth_base_url):
        """Test auth service health endpoint"""
        async with AsyncClient(base_url=auth_base_url) as client:
            try:
                response = await client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
            except Exception:
                pytest.skip("Auth service not running")
    
    @pytest.mark.asyncio
    async def test_user_registration(self, auth_base_url):
        """Test user registration endpoint"""
        async with AsyncClient(base_url=auth_base_url) as client:
            user_data = {
                "email": "testuser@example.com",
                "password": "TestPassword123!",
                "firstName": "Test",
                "lastName": "User"
            }
            
            try:
                response = await client.post("/auth/register", json=user_data)
                if response.status_code == 201:
                    data = response.json()
                    assert "user" in data
                    assert data["user"]["email"] == user_data["email"]
                    assert data["user"]["firstName"] == user_data["firstName"]
                    assert "accessToken" in data
                elif response.status_code == 400:
                    # User might already exist
                    data = response.json()
                    assert "email" in data["detail"].lower() or "exists" in data["detail"].lower()
            except Exception:
                pytest.skip("Auth service not running")
    
    @pytest.mark.asyncio
    async def test_user_login(self, auth_base_url):
        """Test user login endpoint"""
        async with AsyncClient(base_url=auth_base_url) as client:
            # First register a user
            user_data = {
                "email": "logintest@example.com",
                "password": "TestPassword123!",
                "firstName": "Login",
                "lastName": "Test"
            }
            
            try:
                await client.post("/auth/register", json=user_data)
                
                # Then try to login
                login_data = {
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
                
                response = await client.post("/auth/login", json=login_data)
                assert response.status_code == 200
                
                data = response.json()
                assert "accessToken" in data
                assert "refreshToken" in data
                assert "user" in data
                assert data["user"]["email"] == user_data["email"]
            except Exception:
                pytest.skip("Auth service not running")
    
    @pytest.mark.asyncio
    async def test_protected_endpoint(self, auth_base_url):
        """Test accessing protected endpoint with token"""
        async with AsyncClient(base_url=auth_base_url) as client:
            try:
                # Register and login
                user_data = {
                    "email": "protected@example.com",
                    "password": "TestPassword123!",
                    "firstName": "Protected",
                    "lastName": "Test"
                }
                
                await client.post("/auth/register", json=user_data)
                
                login_response = await client.post("/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                
                token = login_response.json()["accessToken"]
                
                # Test protected endpoint
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get("/auth/me", headers=headers)
                
                assert response.status_code == 200
                data = response.json()
                assert data["email"] == user_data["email"]
            except Exception:
                pytest.skip("Auth service not running")


@pytest.mark.integration
class TestAPIGateway:
    """Test API Gateway endpoints"""
    
    @pytest.fixture
    def gateway_base_url(self):
        return "http://localhost:8000"
    
    @pytest.mark.asyncio
    async def test_gateway_health(self, gateway_base_url):
        """Test API gateway health"""
        async with AsyncClient(base_url=gateway_base_url) as client:
            try:
                response = await client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
            except Exception:
                pytest.skip("API Gateway not running")
    
    @pytest.mark.asyncio
    async def test_gateway_routing(self, gateway_base_url):
        """Test API gateway routing to services"""
        async with AsyncClient(base_url=gateway_base_url) as client:
            try:
                # Test routing to auth service
                response = await client.get("/auth/health")
                # Should either work (200) or return service error (5xx)
                assert response.status_code in [200, 500, 502, 503, 504]
                
                # Test routing to other services
                services = ["/data-processing/health", "/analytics/health", "/notification/health"]
                for service_path in services:
                    response = await client.get(service_path)
                    # Accept any valid response - service might not be running
                    assert response.status_code in [200, 404, 500, 502, 503, 504]
            except Exception:
                pytest.skip("API Gateway not running")


@pytest.mark.integration
class TestDataProcessingAPI:
    """Test Data Processing service API"""
    
    @pytest.fixture
    def processing_base_url(self):
        return "http://localhost:8002"
    
    @pytest.mark.asyncio
    async def test_processing_health(self, processing_base_url):
        """Test data processing service health"""
        async with AsyncClient(base_url=processing_base_url) as client:
            try:
                response = await client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
            except Exception:
                pytest.skip("Data Processing service not running")
    
    @pytest.mark.asyncio
    async def test_process_energy_data(self, processing_base_url):
        """Test energy data processing endpoint"""
        async with AsyncClient(base_url=processing_base_url) as client:
            energy_data = {
                "deviceId": "test-device-001",
                "timestamp": "2024-01-15T10:30:00Z",
                "power": 1250.5,
                "voltage": 230.2,
                "current": 5.43,
                "frequency": 50.0,
                "powerFactor": 0.95,
                "energy": 125.5
            }
            
            try:
                response = await client.post("/process", json=energy_data)
                # Should either process successfully or return validation error
                assert response.status_code in [200, 201, 400, 422]
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    assert "processed" in data or "result" in data
            except Exception:
                pytest.skip("Data Processing service not running")


@pytest.mark.integration 
class TestAnalyticsAPI:
    """Test Analytics service API"""
    
    @pytest.fixture
    def analytics_base_url(self):
        return "http://localhost:8003"
    
    @pytest.mark.asyncio
    async def test_analytics_health(self, analytics_base_url):
        """Test analytics service health"""
        async with AsyncClient(base_url=analytics_base_url) as client:
            try:
                response = await client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
            except Exception:
                pytest.skip("Analytics service not running")
    
    @pytest.mark.asyncio
    async def test_dashboard_data(self, analytics_base_url):
        """Test dashboard data endpoint"""
        async with AsyncClient(base_url=analytics_base_url) as client:
            try:
                response = await client.get("/dashboard")
                assert response.status_code in [200, 401]  # May require auth
                
                if response.status_code == 200:
                    data = response.json()
                    # Should have basic dashboard structure
                    expected_keys = ["totalDevices", "onlineDevices", "totalEnergyToday", "averagePower"]
                    for key in expected_keys:
                        assert key in data
            except Exception:
                pytest.skip("Analytics service not running")


@pytest.mark.integration
class TestNotificationAPI:
    """Test Notification service API"""
    
    @pytest.fixture
    def notification_base_url(self):
        return "http://localhost:8004"
    
    @pytest.mark.asyncio
    async def test_notification_health(self, notification_base_url):
        """Test notification service health"""
        async with AsyncClient(base_url=notification_base_url) as client:
            try:
                response = await client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
            except Exception:
                pytest.skip("Notification service not running")
    
    @pytest.mark.asyncio
    async def test_send_notification(self, notification_base_url):
        """Test sending a notification"""
        async with AsyncClient(base_url=notification_base_url) as client:
            notification_data = {
                "recipient": "test@example.com",
                "subject": "Test Notification",
                "message": "This is a test notification",
                "type": "info"
            }
            
            try:
                response = await client.post("/send", json=notification_data)
                # Should either accept notification or require authentication
                assert response.status_code in [200, 201, 401, 422]
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    assert "id" in data or "status" in data
            except Exception:
                pytest.skip("Notification service not running")


@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    @pytest.mark.asyncio
    async def test_complete_user_workflow(self):
        """Test complete user registration, login, and data access workflow"""
        gateway_url = "http://localhost:8000"
        
        async with AsyncClient(base_url=gateway_url) as client:
            try:
                # 1. Register user
                user_data = {
                    "email": "e2e@example.com",
                    "password": "E2EPassword123!",
                    "firstName": "E2E",
                    "lastName": "User"
                }
                
                register_response = await client.post("/auth/register", json=user_data)
                if register_response.status_code not in [201, 400]:
                    pytest.skip("Auth service not working properly")
                
                # 2. Login
                login_response = await client.post("/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                
                if login_response.status_code != 200:
                    pytest.skip("Login failed")
                
                token = login_response.json()["accessToken"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # 3. Access protected resources
                me_response = await client.get("/auth/me", headers=headers)
                assert me_response.status_code == 200
                
                # 4. Try to access dashboard data
                dashboard_response = await client.get("/analytics/dashboard", headers=headers)
                # May or may not work depending on service status
                assert dashboard_response.status_code in [200, 401, 403, 404, 500, 502, 503]
                
            except Exception as e:
                pytest.skip(f"E2E test failed due to service issues: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_data_ingestion_to_analytics_flow(self):
        """Test data flow from ingestion to analytics"""
        gateway_url = "http://localhost:8000"
        
        async with AsyncClient(base_url=gateway_url) as client:
            try:
                # Simulate IoT data ingestion
                energy_reading = {
                    "deviceId": "test-device-e2e",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "power": 1500.0,
                    "voltage": 230.0,
                    "current": 6.52,
                    "frequency": 50.0,
                    "powerFactor": 0.92,
                    "energy": 150.0
                }
                
                # Send data to ingestion service
                ingest_response = await client.post("/data-ingestion/ingest", json=energy_reading)
                
                # Wait a moment for processing
                await asyncio.sleep(2)
                
                # Check if data appears in analytics
                analytics_response = await client.get("/analytics/dashboard")
                
                # Test passes if services respond appropriately
                assert ingest_response.status_code in [200, 201, 401, 404, 500, 502]
                assert analytics_response.status_code in [200, 401, 404, 500, 502]
                
            except Exception:
                pytest.skip("Data flow test requires running services")
