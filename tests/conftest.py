"""
Shared test fixtures and utilities for the Energy Tracking System
"""
import pytest
import asyncio
import asyncpg
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from typing import AsyncGenerator, Generator
import sys
import os
from pathlib import Path
import uuid
from datetime import datetime, timedelta
import json

# Add services to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
for service in ["auth-service", "api-gateway", "data-processing", "analytics", "notification", "data-ingestion"]:
    sys.path.insert(0, str(project_root / "services" / service))

# Test database configuration
TEST_DATABASE_URL = "postgresql://test:test@localhost:5433/test_energy_tracking"
TEST_REDIS_URL = "redis://localhost:6380"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL container for testing"""
    with PostgresContainer(
        "postgres:15-alpine",
        username="test",
        password="test",
        dbname="test_energy_tracking"
    ).with_exposed_ports(5432) as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def redis_container():
    """Start Redis container for testing"""
    with RedisContainer("redis:7-alpine").with_exposed_ports(6379) as redis:
        yield redis


@pytest.fixture(scope="session")
async def test_db(postgres_container):
    """Create test database and tables"""
    database_url = postgres_container.get_connection_url()
    
    # Create async engine for database operations
    engine = create_async_engine(
        database_url.replace("postgresql://", "postgresql+asyncpg://")
    )
    
    # Create tables (this would normally be done by migrations)
    async with engine.begin() as conn:
        # Create basic tables for testing
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                role VARCHAR(50) DEFAULT 'user',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS devices (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                device_type VARCHAR(100),
                location VARCHAR(255),
                status VARCHAR(50) DEFAULT 'online',
                user_id UUID REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS energy_readings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_id UUID REFERENCES devices(id),
                power DECIMAL(10,2),
                voltage DECIMAL(10,2),
                current DECIMAL(10,2),
                frequency DECIMAL(5,2),
                power_factor DECIMAL(3,2),
                energy DECIMAL(15,2),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
    
    yield database_url
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def db_session(test_db):
    """Create database session for each test"""
    async_database_url = test_db.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(async_database_url, echo=False)
    
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
    
    await engine.dispose()


@pytest.fixture
async def client():
    """Create test HTTP client"""
    # This would normally import your FastAPI app
    # For now, we'll create a mock client
    from unittest.mock import MagicMock
    
    # Mock client for testing
    mock_client = MagicMock()
    mock_client.base_url = "http://test"
    yield mock_client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!",
        "firstName": "Test",
        "lastName": "User",
        "role": "user"
    }


@pytest.fixture
def sample_device_data():
    """Sample device data for testing"""
    return {
        "name": f"Test Device {uuid.uuid4().hex[:8]}",
        "device_type": "sensor",
        "location": "Test Location",
        "status": "online"
    }


@pytest.fixture
def sample_energy_reading():
    """Sample energy reading data for testing"""
    return {
        "power": 1250.5,
        "voltage": 230.2,
        "current": 5.43,
        "frequency": 50.0,
        "power_factor": 0.95,
        "energy": 125.5,
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
async def authenticated_client(client, sample_user_data, db_session):
    """Create authenticated test client"""
    # This would normally create a user and get auth token
    # Mock implementation for now
    from unittest.mock import AsyncMock
    
    mock_token = "test-auth-token"
    client.headers = {"Authorization": f"Bearer {mock_token}"}
    return client


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user(**kwargs):
        """Create user with default values"""
        default = {
            "email": f"user-{uuid.uuid4().hex[:8]}@test.com",
            "firstName": "Test",
            "lastName": "User",
            "role": "user",
            "isActive": True
        }
        default.update(kwargs)
        return default
    
    @staticmethod
    def create_device(**kwargs):
        """Create device with default values"""
        default = {
            "name": f"Test Device {uuid.uuid4().hex[:8]}",
            "device_type": "sensor",
            "status": "online",
            "location": "Test Location"
        }
        default.update(kwargs)
        return default
    
    @staticmethod
    def create_energy_reading(**kwargs):
        """Create energy reading with default values"""
        default = {
            "power": 1000.0 + (uuid.uuid4().int % 1000),
            "voltage": 230.0,
            "current": 4.35,
            "frequency": 50.0,
            "power_factor": 0.95,
            "energy": 100.0 + (uuid.uuid4().int % 100),
            "timestamp": datetime.utcnow()
        }
        default.update(kwargs)
        return default
    
    @staticmethod
    def create_notification(**kwargs):
        """Create notification with default values"""
        default = {
            "title": "Test Notification",
            "message": "This is a test notification",
            "type": "info",
            "priority": "medium",
            "created_at": datetime.utcnow()
        }
        default.update(kwargs)
        return default


# Utility functions for tests
async def create_test_user(session, **kwargs):
    """Create test user in database"""
    from unittest.mock import MagicMock
    
    user_data = TestDataFactory.create_user(**kwargs)
    
    # Mock user creation - in real implementation, this would use your User model
    mock_user = MagicMock()
    mock_user.id = str(uuid.uuid4())
    mock_user.email = user_data["email"]
    mock_user.first_name = user_data["firstName"]
    mock_user.last_name = user_data["lastName"]
    mock_user.role = user_data["role"]
    mock_user.is_active = user_data["isActive"]
    
    return mock_user


async def create_test_device(session, user_id=None, **kwargs):
    """Create test device in database"""
    from unittest.mock import MagicMock
    
    device_data = TestDataFactory.create_device(**kwargs)
    
    # Mock device creation
    mock_device = MagicMock()
    mock_device.id = str(uuid.uuid4())
    mock_device.name = device_data["name"]
    mock_device.device_type = device_data["device_type"]
    mock_device.location = device_data["location"]
    mock_device.status = device_data["status"]
    mock_device.user_id = user_id or str(uuid.uuid4())
    
    return mock_device


async def create_test_energy_reading(session, device_id=None, **kwargs):
    """Create test energy reading in database"""
    from unittest.mock import MagicMock
    
    reading_data = TestDataFactory.create_energy_reading(**kwargs)
    
    # Mock energy reading creation
    mock_reading = MagicMock()
    mock_reading.id = str(uuid.uuid4())
    mock_reading.device_id = device_id or str(uuid.uuid4())
    mock_reading.power = reading_data["power"]
    mock_reading.voltage = reading_data["voltage"]
    mock_reading.current = reading_data["current"]
    mock_reading.frequency = reading_data["frequency"]
    mock_reading.power_factor = reading_data["power_factor"]
    mock_reading.energy = reading_data["energy"]
    mock_reading.timestamp = reading_data["timestamp"]
    
    return mock_reading


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    from unittest.mock import AsyncMock
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = False
    
    return mock_redis


@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client for testing"""
    from unittest.mock import MagicMock
    
    mock_mqtt = MagicMock()
    mock_mqtt.connect.return_value = True
    mock_mqtt.publish.return_value = True
    mock_mqtt.subscribe.return_value = True
    mock_mqtt.disconnect.return_value = True
    
    return mock_mqtt


@pytest.fixture
def mock_email_service():
    """Mock email service for testing"""
    from unittest.mock import AsyncMock
    
    mock_email = AsyncMock()
    mock_email.send_email.return_value = {"status": "sent", "message_id": "test-message-id"}
    mock_email.test_connection.return_value = True
    
    return mock_email


# Performance testing utilities
@pytest.fixture
def performance_config():
    """Configuration for performance tests"""
    return {
        "max_response_time": 1.0,  # seconds
        "max_concurrent_requests": 100,
        "test_duration": 30,  # seconds
        "ramp_up_time": 10,  # seconds
    }


# Security testing utilities
@pytest.fixture
def security_headers():
    """Expected security headers"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'"
    }


# Test environment configuration
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables"""
    test_env = {
        "ENVIRONMENT": "test",
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": TEST_REDIS_URL,
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "SMTP_SERVER": "localhost",
        "SMTP_PORT": "1025",
        "SMTP_USERNAME": "test",
        "SMTP_PASSWORD": "test",
        "MQTT_BROKER_HOST": "localhost",
        "MQTT_BROKER_PORT": "1883",
        "LOG_LEVEL": "DEBUG"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


# Cleanup utilities
@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Cleanup logic here
    pass
