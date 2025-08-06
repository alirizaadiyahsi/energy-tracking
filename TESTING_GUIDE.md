# Testing Guide - Energy Tracking System

## 🧪 Testing Overview

This document provides comprehensive testing strategies for the Energy Tracking System, including unit tests, integration tests, and end-to-end testing approaches.

## 📋 Testing Strategy

### 1. Testing Pyramid
```
    /\
   /  \    E2E Tests (Few)
  /____\   
 /      \   Integration Tests (Some)  
/________\  Unit Tests (Many)
```

### 2. Test Types
- **Unit Tests**: Individual components and functions
- **Integration Tests**: API endpoints and service interactions
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization

## 🔧 Setup and Installation

### Backend Testing Setup

1. **Install test dependencies**:
   ```bash
   pip install -r test-requirements.txt
   ```

2. **Run all tests**:
   ```bash
   pytest tests/ -v
   ```

3. **Run specific test types**:
   ```bash
   # Unit tests only
   pytest tests/unit/ -v -m unit
   
   # Integration tests only
   pytest tests/integration/ -v -m integration
   
   # With coverage
   pytest tests/ --cov=services --cov-report=html
   ```

### Frontend Testing Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install test dependencies**:
   ```bash
   npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest jsdom
   ```

3. **Update package.json**:
   ```json
   {
     "scripts": {
       "test": "vitest",
       "test:coverage": "vitest --coverage",
       "test:ui": "vitest --ui"
     }
   }
   ```

4. **Create vitest config** (`frontend/vite.config.ts`):
   ```typescript
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'

   export default defineConfig({
     plugins: [react()],
     test: {
       globals: true,
       environment: 'jsdom',
       setupFiles: './src/test/setup.ts',
     },
   })
   ```

## 🎯 Unit Testing

### Backend Unit Tests

#### Authentication Service Tests
```python
# tests/unit/auth_service/test_security.py
import pytest
from core.security import hash_password, verify_password, create_access_token

def test_password_hashing():
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_jwt_token_creation():
    user_data = {"user_id": "123", "email": "test@example.com"}
    token = create_access_token(user_data)
    
    assert isinstance(token, str)
    assert len(token) > 50
```

#### Data Processing Tests
```python
# tests/unit/data_processing/test_processing.py
import pytest
from services.processing_service import ProcessingService

@pytest.mark.asyncio
async def test_energy_data_processing():
    service = ProcessingService()
    
    energy_data = {
        "deviceId": "test-device",
        "power": 1000.0,
        "voltage": 230.0,
        "current": 4.35
    }
    
    result = await service.process_energy_reading(energy_data)
    
    assert result["processed"] is True
    assert result["deviceId"] == "test-device"
    assert "timestamp" in result
```

### Frontend Unit Tests

#### Component Tests
```typescript
// frontend/src/test/components/LoginForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { LoginForm } from '../components/auth/LoginForm'

describe('LoginForm', () => {
  it('renders form fields', () => {
    render(<LoginForm />)
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    render(<LoginForm />)
    
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    fireEvent.click(submitButton)
    
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument()
  })
})
```

#### Utility Tests
```typescript
// frontend/src/test/utils/formatters.test.ts
import { formatEnergy, formatPower } from '../utils/formatters'

describe('formatters', () => {
  describe('formatEnergy', () => {
    it('formats energy values correctly', () => {
      expect(formatEnergy(1500.5)).toBe('1.50 kWh')
      expect(formatEnergy(500)).toBe('500 Wh')
    })
  })
})
```

## 🔗 Integration Testing

### API Integration Tests

#### Authentication Flow
```python
# tests/integration/test_auth_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAuthFlow:
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self):
        async with AsyncClient(base_url="http://localhost:8005") as client:
            # Register
            user_data = {
                "email": "integration@test.com",
                "password": "TestPass123!",
                "firstName": "Test",
                "lastName": "User"
            }
            
            response = await client.post("/auth/register", json=user_data)
            assert response.status_code == 201
            
            # Login
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            
            response = await client.post("/auth/login", json=login_data)
            assert response.status_code == 200
            
            token = response.json()["accessToken"]
            
            # Access protected resource
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/auth/me", headers=headers)
            assert response.status_code == 200
```

### Service Integration Tests

#### Data Flow Tests
```python
# tests/integration/test_data_flow.py
@pytest.mark.integration
class TestDataFlow:
    @pytest.mark.asyncio
    async def test_iot_to_dashboard_flow(self):
        # Send data to ingestion
        energy_reading = {
            "deviceId": "integration-device",
            "power": 1200.0,
            "voltage": 230.0,
            "current": 5.22
        }
        
        async with AsyncClient(base_url="http://localhost:8001") as client:
            response = await client.post("/ingest", json=energy_reading)
            assert response.status_code == 200
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check analytics
        async with AsyncClient(base_url="http://localhost:8003") as client:
            response = await client.get("/dashboard")
            assert response.status_code == 200
            
            data = response.json()
            assert "totalEnergyToday" in data
```

## 🚀 End-to-End Testing

### Complete User Workflows
```python
# tests/e2e/test_user_workflows.py
@pytest.mark.e2e
class TestUserWorkflows:
    @pytest.mark.asyncio
    async def test_user_registration_to_dashboard_access(self):
        """Complete user journey from registration to dashboard access"""
        
        async with AsyncClient(base_url="http://localhost:8000") as client:
            # 1. User registration
            user_data = {
                "email": "e2e@example.com",
                "password": "E2EPassword123!",
                "firstName": "E2E",
                "lastName": "User"
            }
            
            response = await client.post("/auth/register", json=user_data)
            assert response.status_code == 201
            
            # 2. User login
            response = await client.post("/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            assert response.status_code == 200
            
            token = response.json()["accessToken"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 3. Access dashboard
            response = await client.get("/analytics/dashboard", headers=headers)
            assert response.status_code == 200
            
            # 4. View devices
            response = await client.get("/devices", headers=headers)
            assert response.status_code == 200
            
            # 5. Access user profile
            response = await client.get("/auth/me", headers=headers)
            assert response.status_code == 200
            
            profile = response.json()
            assert profile["email"] == user_data["email"]
```

## 📊 Performance Testing

### Load Testing with Locust
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class EnergyTrackingUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login user
        response = self.client.post("/auth/login", json={
            "email": "loadtest@example.com",
            "password": "LoadTest123!"
        })
        
        if response.status_code == 200:
            self.token = response.json()["accessToken"]
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
    
    @task(3)
    def view_dashboard(self):
        self.client.get("/analytics/dashboard")
    
    @task(2)
    def view_devices(self):
        self.client.get("/devices")
    
    @task(1)
    def send_energy_data(self):
        energy_data = {
            "deviceId": f"load-test-{self.environment.runner.user_count}",
            "power": 1000.0,
            "voltage": 230.0,
            "current": 4.35
        }
        self.client.post("/data-ingestion/ingest", json=energy_data)
```

**Run load tests**:
```bash
pip install locust
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 🔒 Security Testing

### Authentication & Authorization Tests
```python
# tests/security/test_auth_security.py
@pytest.mark.security
class TestAuthSecurity:
    @pytest.mark.asyncio
    async def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints reject unauthenticated requests"""
        async with AsyncClient(base_url="http://localhost:8000") as client:
            protected_endpoints = [
                "/auth/me",
                "/devices",
                "/analytics/dashboard",
                "/data-processing/process"
            ]
            
            for endpoint in protected_endpoints:
                response = await client.get(endpoint)
                assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_role_based_access_control(self):
        """Test RBAC functionality"""
        # Test with different user roles
        test_cases = [
            ("viewer", "/devices", 200),
            ("viewer", "/admin/users", 403),
            ("admin", "/admin/users", 200),
        ]
        
        for role, endpoint, expected_status in test_cases:
            # Create user with specific role
            user = await create_test_user(role=role)
            token = await login_user(user.email, "password123")
            
            async with AsyncClient(base_url="http://localhost:8000") as client:
                client.headers.update({"Authorization": f"Bearer {token}"})
                response = await client.get(endpoint)
                assert response.status_code == expected_status
```

## 📈 Test Coverage

### Coverage Requirements
- **Overall Coverage**: Minimum 80%
- **Critical Components**: Minimum 90%
  - Authentication service
  - Data processing service
  - Core security functions

### Generate Coverage Reports
```bash
# Backend coverage
pytest tests/ --cov=services --cov-report=html --cov-report=term --cov-fail-under=80

# Frontend coverage
cd frontend && npm run test:coverage
```

### Coverage Configuration (`pytest.ini`)
```ini
[tool:pytest]
addopts = --cov=services --cov-report=html --cov-report=term-missing --cov-fail-under=80
```

## 🚀 CI/CD Testing Pipeline

### GitHub Actions Workflow (`.github/workflows/test.yml`)
```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r test-requirements.txt
        pip install -r services/auth-service/requirements.txt
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=services
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage
```

## 📝 Test Documentation

### Test Case Template
```markdown
## Test Case: [Test Name]

**Objective**: [What is being tested]

**Preconditions**: 
- [Required setup]

**Test Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Results**:
- [Expected outcome]

**Test Data**:
- [Test data used]

**Priority**: [High/Medium/Low]
```

### Test Reporting
- **Daily Test Reports**: Automated test runs with results
- **Coverage Reports**: Updated on each commit
- **Performance Benchmarks**: Weekly performance test results
- **Security Scans**: Monthly security test reports

## 🔧 Running Tests in Development

### Quick Test Commands
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests (requires services running)
docker-compose up -d
make test-integration

# Run with coverage
make test-coverage

# Frontend tests
cd frontend && npm test

# Performance tests
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Docker Test Environment
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test-postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: test_energy_tracking
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
  
  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
  
  test-runner:
    build:
      context: .
      dockerfile: Dockerfile.test
    depends_on:
      - test-postgres
      - test-redis
    command: pytest tests/ -v --cov=services
    environment:
      DATABASE_URL: postgresql://test:test@test-postgres:5432/test_energy_tracking
      REDIS_URL: redis://test-redis:6379/0
```

This comprehensive testing strategy ensures reliability, performance, and security across the entire Energy Tracking System.
