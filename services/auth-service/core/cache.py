"""
Redis cache configuration and connection management
"""
import logging
import json
from typing import Any, Optional
import redis.asyncio as redis
from core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection
_redis_client: Optional[redis.Redis] = None

async def init_redis():
    """Initialize Redis connection"""
    global _redis_client
    try:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30,
        )
        
        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection successful")
        
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        raise

async def get_redis() -> redis.Redis:
    """Get Redis client"""
    if _redis_client is None:
        await init_redis()
    return _redis_client

async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")

class CacheService:
    """Cache service for managing Redis operations"""
    
    def __init__(self):
        self.redis = None
    
    async def get_client(self):
        """Get Redis client"""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis
    
    async def set(self, key: str, value: Any, expire: int = None):
        """Set value in cache"""
        try:
            client = await self.get_client()
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def delete(self, key: str):
        """Delete key from cache"""
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in cache"""
        try:
            client = await self.get_client()
            return await client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int):
        """Set expiration for key"""
        try:
            client = await self.get_client()
            await client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")

# Global cache service instance
cache = CacheService()
