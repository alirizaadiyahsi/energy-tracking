# Device Management Testing Documentation

## Overview

This document describes the comprehensive testing strategy for the device management system, including unit tests, integration tests, and end-to-end test coverage.

## Test Structure

```
tests/
├── unit/
│   └── data-ingestion/
│       └── test_device_endpoints.py      # Unit tests for device API endpoints
├── integration/
│   └── test_device_management.py         # Integration tests for device workflows
└── frontend/
    └── src/components/__tests__/
        └── DeviceForm.test.tsx           # Frontend component tests
```

## Unit Tests

### Backend Unit Tests (`test_device_endpoints.py`)

Comprehensive unit tests covering all device management endpoints with mocked dependencies.

**Test Coverage:**

- **Device CRUD Operations**
  - Create device with valid data
  - List devices with pagination
  - Get device by ID
  - Update device information
  - Delete device
  - Handle non-existent devices

- **Authentication & Authorization**
  - Valid JWT token validation
  - Invalid/expired token handling
  - Missing authorization header
  - Role-based permission checking
  - Organization isolation

- **Input Validation**
  - Required field validation
  - Data type validation
  - Field length constraints
  - Invalid enum values
  - Malformed JSON handling

- **Permission System**
  - READ_DEVICE permission
  - CREATE_DEVICE permission
  - UPDATE_DEVICE permission
  - DELETE_DEVICE permission
  - Admin vs user role differences

- **Rate Limiting**
  - Request rate tracking
  - Rate limit enforcement
  - Different limits per role
  - Rate limit header responses

- **Audit Logging**
  - Operation logging
  - User and organization tracking
  - Success/failure logging
  - Sensitive data handling

**Key Test Classes:**

```python
class TestDeviceEndpoints:
    """Test device CRUD operations"""
    
class TestDeviceValidation:
    """Test input validation and data constraints"""
    
class TestPermissionChecking:
    """Test role-based access control"""
    
class TestRateLimiting:
    """Test API rate limiting functionality"""
    
class TestAuditLogging:
    """Test audit trail generation"""
```

**Running Backend Unit Tests:**

```bash
# Run specific test file
python -m pytest tests/unit/data-ingestion/test_device_endpoints.py -v

# Run with coverage
python -m pytest tests/unit/data-ingestion/test_device_endpoints.py --cov=services/data-ingestion

# Run specific test class
python -m pytest tests/unit/data-ingestion/test_device_endpoints.py::TestDeviceEndpoints -v
```

### Frontend Unit Tests (`DeviceForm.test.tsx`)

React component tests using Vitest and React Testing Library.

**Test Coverage:**

- **Component Rendering**
  - Form renders when open
  - Form hidden when closed
  - Correct title display (Add vs Edit)
  - All form fields present

- **Form Validation**
  - Required field validation
  - Numeric field validation
  - Device type selection
  - Error message display
  - Real-time validation clearing

- **User Interactions**
  - Form submission with valid data
  - Close button functionality
  - Backdrop click handling
  - Loading state display

- **Data Handling**
  - Pre-filling form for editing
  - Form reset on device change
  - Correct data submission format
  - Error handling

**Running Frontend Unit Tests:**

```bash
cd frontend
npm test                    # Run all tests
npm run test:watch         # Run in watch mode
npm run test:coverage      # Run with coverage report
```

## Integration Tests

### Backend Integration Tests (`test_device_management.py`)

End-to-end workflow tests simulating real user scenarios.

**Test Scenarios:**

- **Complete Device Lifecycle**
  - Create new device
  - Read device details
  - Update device information
  - Delete device
  - Verify audit trails

- **Multi-User Scenarios**
  - Organization isolation
  - Permission boundary testing
  - Concurrent access handling

- **Error Recovery**
  - Database connection failures
  - External service failures
  - Network timeout handling

- **Performance Testing**
  - Large dataset handling
  - Pagination performance
  - Rate limiting under load

**Running Integration Tests:**

```bash
# Run integration tests
python -m pytest tests/integration/test_device_management.py -v

# Run with specific markers
python -m pytest -m "integration" -v
```

## Test Data Management

### Test Fixtures

**User Fixtures:**
```python
@pytest.fixture
def test_user():
    return MockUser(
        user_id="test-user-123",
        org_id="test-org-456",
        role="user"
    )

@pytest.fixture  
def admin_user():
    return MockUser(
        user_id="admin-user-789",
        org_id="test-org-456", 
        role="admin"
    )
```

**Device Fixtures:**
```python
@pytest.fixture
def sample_device():
    return {
        "name": "Test Device",
        "type": "sensor",
        "location": "Test Location",
        "description": "Test Description",
        "base_power": 5.0,
        "base_voltage": 240.0,
        "firmware_version": "1.0.0",
        "model": "TestModel"
    }
```

### Database Setup

```python
@pytest.fixture
async def test_db():
    """Create test database session"""
    # Use in-memory SQLite for fast tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        yield session
```

## Mocking Strategy

### External Dependencies

**Authentication Service:**
```python
@patch('core.auth.httpx.AsyncClient')
async def test_with_mocked_auth(mock_client):
    mock_client.return_value.post.return_value.json.return_value = {
        "user_id": "test-user",
        "organization_id": "test-org"
    }
```

**Database Operations:**
```python
@patch('services.device_service.DeviceService.create_device')
async def test_with_mocked_db(mock_create):
    mock_create.return_value = MockDevice("device-123", "Test", "sensor", "org-123")
```

**Rate Limiting:**
```python
@patch('core.permissions.RateLimiter.check_rate_limit')
async def test_with_mocked_rate_limit(mock_rate_limit):
    mock_rate_limit.return_value = True
```

## Test Configuration

### Environment Variables

```bash
# Test database
TEST_DATABASE_URL="sqlite+aiosqlite:///:memory:"

# Authentication service
TEST_AUTH_SERVICE_URL="http://localhost:8001"

# Disable external calls
TESTING_MODE=true
```

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    auth: Authentication tests
    permissions: Permission tests
asyncio_mode = auto
```

## Coverage Requirements

### Minimum Coverage Targets

- **Overall Coverage:** 85%
- **Critical Paths:** 95%
- **Security Functions:** 100%
- **API Endpoints:** 90%
- **Business Logic:** 95%

### Coverage Reports

```bash
# Generate HTML coverage report
python -m pytest --cov=services/data-ingestion --cov-report=html

# View coverage in terminal
python -m pytest --cov=services/data-ingestion --cov-report=term

# Check specific coverage thresholds
python -m pytest --cov=services/data-ingestion --cov-fail-under=85
```

## Continuous Integration

### GitHub Actions Pipeline

```yaml
name: Device Management Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/test-requirements.txt
      - name: Run unit tests
        run: pytest tests/unit/ --cov=services/data-ingestion
      - name: Run integration tests
        run: pytest tests/integration/
        
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend
      - name: Run tests
        run: npm test
        working-directory: ./frontend
```

## Security Testing

### Authentication Tests

- JWT token validation
- Token expiration handling
- Invalid signature detection
- Role escalation prevention

### Authorization Tests

- Organization boundary enforcement
- Permission requirement validation
- Access control bypass attempts
- Privilege escalation detection

### Input Security Tests

- SQL injection prevention
- XSS protection
- Command injection prevention
- Path traversal protection

## Performance Testing

### Load Testing

```python
async def test_device_list_performance():
    """Test device listing under load"""
    # Create 1000 test devices
    devices = await create_test_devices(1000)
    
    # Measure response time
    start_time = time.time()
    response = await client.get("/api/v1/devices?limit=100")
    end_time = time.time()
    
    assert response.status_code == 200
    assert end_time - start_time < 1.0  # Response under 1 second
```

### Memory Usage Tests

```python
async def test_memory_usage():
    """Test memory usage during large operations"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operation
    await process_large_device_batch(10000)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB
```

## Test Maintenance

### Regular Tasks

1. **Update test data** when schemas change
2. **Review mock accuracy** against real services
3. **Monitor test performance** and optimize slow tests
4. **Update coverage targets** as codebase grows
5. **Refresh test documentation** with new scenarios

### Test Review Checklist

- [ ] All new features have corresponding tests
- [ ] Tests cover both success and failure scenarios
- [ ] Security-related functionality is thoroughly tested
- [ ] Performance implications are considered
- [ ] Error handling is tested
- [ ] Edge cases are covered
- [ ] Documentation is updated

## Debugging Tests

### Common Issues

**Import Errors:**
```bash
# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Async Test Issues:**
```python
# Use proper async test decoration
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

**Mock Setup:**
```python
# Reset mocks between tests
@pytest.fixture(autouse=True)
def reset_mocks():
    with patch.object(SomeClass, 'method') as mock:
        yield mock
    mock.reset_mock()
```

### Test Debugging Commands

```bash
# Run single test with output
pytest tests/unit/data-ingestion/test_device_endpoints.py::TestDeviceEndpoints::test_create_device -s

# Run with pdb debugging
pytest tests/unit/data-ingestion/test_device_endpoints.py --pdb

# Run with verbose logging
pytest tests/unit/data-ingestion/test_device_endpoints.py --log-cli-level=DEBUG
```

## Best Practices

1. **Test Isolation:** Each test should be independent
2. **Clear Naming:** Test names should describe what they test
3. **Arrange-Act-Assert:** Structure tests clearly
4. **Mock External Dependencies:** Don't rely on external services
5. **Test Edge Cases:** Include boundary conditions
6. **Keep Tests Fast:** Unit tests should run quickly
7. **Regular Maintenance:** Update tests with code changes
8. **Documentation:** Document complex test scenarios
