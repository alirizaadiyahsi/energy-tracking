# Testing Guide - Energy Tracking System

This directory contains comprehensive tests for the Energy Tracking IoT Data Platform. Our testing strategy follows industry best practices with multiple testing layers to ensure system reliability, performance, and security.

## 📁 Folder Structure

```
tests/
├── README.md                    # This file
├── conftest.py                 # Shared fixtures and utilities
├── pytest.ini                 # Pytest configuration
├── test-requirements.txt       # Testing dependencies
├── run_tests.py               # Test runner script
├── unit/                      # Unit tests
│   ├── auth-service/          # Authentication unit tests
│   ├── analytics/             # Analytics unit tests
│   ├── api-gateway/           # API Gateway unit tests
│   ├── data-ingestion/        # Data ingestion unit tests
│   ├── data-processing/       # Data processing unit tests
│   └── notification/          # Notification unit tests
├── integration/               # Integration tests
│   ├── auth-service/          # Authentication integration tests
│   ├── analytics/             # Analytics integration tests
│   ├── api-gateway/           # API Gateway integration tests
│   ├── data-ingestion/        # Data ingestion integration tests
│   ├── data-processing/       # Data processing integration tests
│   └── notification/          # Notification integration tests
├── performance/               # Performance tests
│   ├── auth-service/          # Authentication performance tests
│   ├── analytics/             # Analytics performance tests
│   ├── api-gateway/           # API Gateway performance tests
│   ├── data-ingestion/        # Data ingestion performance tests
│   ├── data-processing/       # Data processing performance tests
│   └── notification/          # Notification performance tests
└── e2e/                      # End-to-end tests
    ├── user_workflows.py      # Complete user journey tests
    ├── system_integration.py  # Full system integration tests
    └── api_flows.py          # API workflow tests
```

## 🧪 Test Types

### Unit Tests
Tests individual functions, classes, and modules in isolation.

**Coverage Target**: 90% for critical components, 80% overall
**Tools**: pytest, pytest-mock, pytest-asyncio
**Scope**: 
- Business logic validation
- Data transformation functions
- Security utilities
- API request/response handling

### Integration Tests
Tests service-to-service communication and workflows.

**Tools**: pytest, httpx, testcontainers
**Scope**:
- API endpoint integration
- Database operations
- Service communication
- Authentication flows

### Performance Tests
Tests system performance under various load conditions.

**Tools**: Locust, pytest-benchmark
**Scope**:
- API response times
- Database query performance
- Concurrent user simulation
- Resource utilization

### End-to-End Tests
Tests complete user workflows and system integration.

**Tools**: pytest, playwright (for frontend)
**Scope**:
- User registration to dashboard access
- Device management workflows
- Data ingestion to visualization pipeline
- Cross-service functionality

## 🚀 Running Tests

### Prerequisites

1. **Install dependencies**:
   ```bash
   pip install -r tests/test-requirements.txt
   ```

2. **Set up test environment**:
   ```bash
   # Copy and configure test environment
   cp .env.example .env.test
   # Edit .env.test with test-specific configurations
   ```

3. **Start test services** (for integration tests):
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

### Running Different Test Types

#### All Tests
```bash
# Run all tests with the test runner
python tests/run_tests.py --all

# Or use pytest directly
pytest tests/ -v
```

#### Unit Tests Only
```bash
# Using test runner
python tests/run_tests.py --unit

# Using pytest
pytest tests/unit/ -v -m unit
```

#### Integration Tests Only
```bash
# Using test runner
python tests/run_tests.py --integration

# Using pytest
pytest tests/integration/ -v -m integration
```

#### Performance Tests Only
```bash
# Using test runner
python tests/run_tests.py --performance

# Using pytest
pytest tests/performance/ -v -m performance

# Using Locust directly
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

#### End-to-End Tests Only
```bash
# Using test runner
python tests/run_tests.py --e2e

# Using pytest
pytest tests/e2e/ -v -m e2e
```

#### Specific Service Tests
```bash
# Test specific service
pytest tests/unit/auth-service/ -v
pytest tests/integration/analytics/ -v
```

### Coverage Reports

```bash
# Run tests with coverage
pytest tests/ --cov=services --cov-report=html --cov-report=term

# Generate coverage report
python tests/run_tests.py --coverage

# View HTML coverage report
# Open htmlcov/index.html in browser
```

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test markers for categorization
- Coverage settings and thresholds
- Test discovery patterns
- Plugin configurations

### Environment Variables
Tests use separate environment configurations:
- `DATABASE_URL_TEST`: Test database connection
- `REDIS_URL_TEST`: Test Redis connection
- `MQTT_BROKER_TEST`: Test MQTT broker
- `LOG_LEVEL`: Set to DEBUG for detailed test logs

### Test Data Management
- **Fixtures**: Shared test data and utilities in `conftest.py`
- **Factories**: Generate realistic test data using factory_boy
- **Isolation**: Each test runs with fresh data
- **Cleanup**: Automatic teardown after test completion

## 🛠️ Testing Tools & Libraries

### Core Testing
- **pytest**: Main testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **pytest-cov**: Coverage reporting
- **httpx**: HTTP client for API testing

### Performance Testing
- **Locust**: Load testing framework
- **pytest-benchmark**: Micro-benchmarks

### Database Testing
- **testcontainers**: Isolated database containers
- **factory_boy**: Test data generation
- **faker**: Realistic fake data

### Frontend Testing (in frontend/ directory)
- **Jest**: Unit testing framework
- **React Testing Library**: Component testing
- **Playwright**: End-to-end testing

## 📊 Coverage & Quality Metrics

### Coverage Targets
- **Overall**: Minimum 80%
- **Critical Services**: Minimum 90%
  - Authentication service
  - Data processing service
  - Security modules

### Quality Checks
- **Linting**: flake8, black
- **Security**: bandit, safety
- **Type checking**: mypy
- **Import sorting**: isort

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Ensure test database is running
   docker-compose -f docker-compose.test.yml up -d postgres
   ```

2. **Port Conflicts**
   ```bash
   # Check for conflicting services
   netstat -tulpn | grep :8000
   ```

3. **Permission Errors**
   ```bash
   # Fix file permissions
   chmod +x tests/run_tests.py
   ```

4. **Dependency Issues**
   ```bash
   # Reinstall test dependencies
   pip install -r tests/test-requirements.txt --force-reinstall
   ```

### Debug Mode
```bash
# Run tests with debug output
pytest tests/ -v -s --log-cli-level=DEBUG

# Run specific test with debugging
pytest tests/unit/auth-service/test_auth.py::test_user_creation -v -s
```

## 📋 Best Practices

### Writing Tests
1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Keep tests isolated** and independent
4. **Mock external dependencies** appropriately
5. **Test both success and failure scenarios**

### Test Data
1. **Use factories** for generating test data
2. **Keep test data minimal** but realistic
3. **Clean up after each test**
4. **Use meaningful test data** that reflects real scenarios

### Performance
1. **Set realistic performance targets**
2. **Test under various load conditions**
3. **Monitor resource usage**
4. **Document performance baselines**

### Security
1. **Test authentication and authorization**
2. **Validate input sanitization**
3. **Test rate limiting**
4. **Check for sensitive data exposure**

## 🤝 Contributing to Tests

### Adding New Tests
1. **Choose appropriate test type** (unit/integration/performance/e2e)
2. **Follow naming conventions**: `test_<functionality>.py`
3. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
4. **Include documentation** for complex test scenarios
5. **Update this README** if adding new test categories

### Code Review
- All tests must pass before merging
- New features require corresponding tests
- Maintain or improve coverage percentages
- Review test quality and maintainability

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing FastAPI Applications](https://fastapi.tiangolo.com/tutorial/testing/)
- [Locust Documentation](https://docs.locust.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

For questions or issues with the testing setup, please refer to the main project documentation or create an issue in the repository.
