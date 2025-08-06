"""
Shared test fixtures and utilities
"""
import pytest
import asyncio
import asyncpg
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from typing import AsyncGenerator, Generator
import sys
import os
from pathlib import Path

# Add services to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "services" / "auth-service"))
sys.path.insert(0, str(project_root / "services" / "api-gateway"))
sys.path.insert(0, str(project_root / "services" / "data-processing"))
sys.path.insert(0, str(project_root / "services" / "analytics"))
sys.path.insert(0, str(project_root / "services" / "notification"))

# Test database configuration
TEST_DATABASE_URL = "postgresql://test:test@localhost:5433/test_energy_tracking"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL container for testing"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        postgres.with_env("POSTGRES_DB", "test_energy_tracking")
        postgres.with_env("POSTGRES_USER", "test")
        postgres.with_env("POSTGRES_PASSWORD", "test")
        yield postgres


@pytest.fixture(scope="session")
async def redis_container():
    """Start Redis container for testing"""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
async def test_db(postgres_container):
    """Create test database and tables"""
    database_url = postgres_container.get_connection_url()
    
    # Create engine and tables
    from core.database import Base
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    
    yield database_url
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
async def db_session(test_db):
    """Create database session for each test"""
    from core.database import get_database_session
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async_database_url = test_db.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(async_database_url)
    
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()


@pytest.fixture
async def client():
    """Create test HTTP client"""
    from main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "firstName": "Test",
        "lastName": "User",
        "role": "user"
    }


@pytest.fixture
def sample_device_data():
    """Sample device data for testing"""
    return {
        "name": "Test Device",
        "type": "sensor",
        "location": "Test Location",
        "status": "online"
    }


@pytest.fixture
def sample_energy_reading():
    """Sample energy reading data"""
    return {
        "deviceId": "test-device-1",
        "timestamp": "2024-01-15T10:30:00Z",
        "power": 1250.5,
        "voltage": 230.2,
        "current": 5.43,
        "frequency": 50.0,
        "powerFactor": 0.95,
        "energy": 125.5
    }


@pytest.fixture
async def authenticated_client(client, sample_user_data):
    """Create authenticated test client"""
    # Create user
    await client.post("/auth/register", json=sample_user_data)
    
    # Login
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    response = await client.post("/auth/login", json=login_data)
    token = response.json()["accessToken"]
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user(**kwargs):
        """Create user with default values"""
        default = {
            "email": "user@test.com",
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
            "name": "Test Device",
            "type": "sensor",
            "status": "online",
            "location": "Test Location"
        }
        default.update(kwargs)
        return default
    
    @staticmethod
    def create_energy_reading(**kwargs):
        """Create energy reading with default values"""
        default = {
            "power": 1000.0,
            "voltage": 230.0,
            "current": 4.35,
            "frequency": 50.0,
            "powerFactor": 0.95,
            "energy": 100.0
        }
        default.update(kwargs)
        return default


# Utility functions for tests
async def create_test_user(session, **kwargs):
    """Create test user in database"""
    from models.user import User
    from core.security import hash_password
    
    user_data = TestDataFactory.create_user(**kwargs)
    if "password" in user_data:
        user_data["passwordHash"] = hash_password(user_data.pop("password"))
    
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_test_device(session, **kwargs):
    """Create test device in database"""
    from models.device import Device
    
    device_data = TestDataFactory.create_device(**kwargs)
    device = Device(**device_data)
    session.add(device)
    await session.commit()
    await session.refresh(device)
    return device
