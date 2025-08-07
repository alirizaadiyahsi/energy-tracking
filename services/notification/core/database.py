"""
Database configuration and connection management
"""

import logging

from core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.LOG_LEVEL == "DEBUG",
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create sync engine for celery tasks
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "DEBUG",
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session makers
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all database models"""

    pass


async def get_db():
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


def get_sync_db():
    """Get sync database session for celery tasks"""
    db = SyncSessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


async def init_db():
    """Initialize database"""
    logger.info("Notification database initialized")


async def close_db():
    """Close database connections"""
    await async_engine.dispose()
    sync_engine.dispose()
