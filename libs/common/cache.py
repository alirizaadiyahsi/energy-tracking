"""
Cache utilities for Redis operations
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis


class CacheManager:
    """Redis cache manager with common operations"""
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = ""):
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        if self.key_prefix:
            return f"{self.key_prefix}:{key}"
        return key
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            value = await self.redis.get(self._make_key(key))
            if value is None:
                return default
            
            # Try to deserialize JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value)
        except Exception:
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache"""
        try:
            # Try to serialize as JSON first, then pickle
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value)
            
            cache_key = self._make_key(key)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                return await self.redis.setex(cache_key, expire, serialized_value)
            else:
                return await self.redis.set(cache_key, serialized_value)
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            result = await self.redis.delete(self._make_key(key))
            return result > 0
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return await self.redis.exists(self._make_key(key)) > 0
        except Exception:
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            return await self.redis.expire(self._make_key(key), seconds)
        except Exception:
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            return await self.redis.ttl(self._make_key(key))
        except Exception:
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value"""
        try:
            return await self.redis.incrby(self._make_key(key), amount)
        except Exception:
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement numeric value"""
        try:
            return await self.redis.decrby(self._make_key(key), amount)
        except Exception:
            return None
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        try:
            cache_keys = [self._make_key(key) for key in keys]
            values = await self.redis.mget(cache_keys)
            
            result = {}
            for i, (original_key, value) in enumerate(zip(keys, values)):
                if value is not None:
                    try:
                        result[original_key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[original_key] = pickle.loads(value)
                else:
                    result[original_key] = None
            
            return result
        except Exception:
            return {key: None for key in keys}
    
    async def set_many(
        self, 
        mapping: Dict[str, Any], 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple values in cache"""
        try:
            pipe = self.redis.pipeline()
            
            for key, value in mapping.items():
                try:
                    serialized_value = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    serialized_value = pickle.dumps(value)
                
                cache_key = self._make_key(key)
                
                if expire:
                    if isinstance(expire, timedelta):
                        expire_seconds = int(expire.total_seconds())
                    else:
                        expire_seconds = expire
                    pipe.setex(cache_key, expire_seconds, serialized_value)
                else:
                    pipe.set(cache_key, serialized_value)
            
            await pipe.execute()
            return True
        except Exception:
            return False
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from cache"""
        try:
            cache_keys = [self._make_key(key) for key in keys]
            return await self.redis.delete(*cache_keys)
        except Exception:
            return 0
    
    async def clear_prefix(self, prefix: str = "") -> int:
        """Clear all keys with given prefix"""
        try:
            search_prefix = f"{self.key_prefix}:{prefix}" if self.key_prefix else prefix
            pattern = f"{search_prefix}*"
            
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception:
            return 0


class SessionCache(CacheManager):
    """Cache manager for user sessions"""
    
    def __init__(self, redis_client: redis.Redis):
        super().__init__(redis_client, "session")
    
    async def create_session(
        self, 
        user_id: str, 
        session_data: Dict[str, Any],
        expire_hours: int = 24
    ) -> str:
        """Create user session"""
        session_id = f"user:{user_id}:session:{datetime.utcnow().timestamp()}"
        
        session_info = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            **session_data
        }
        
        expire_seconds = expire_hours * 3600
        await self.set(session_id, session_info, expire_seconds)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return await self.get(session_id)
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        session_data = await self.get_session(session_id)
        if session_data:
            session_data["last_activity"] = datetime.utcnow().isoformat()
            return await self.set(session_id, session_data)
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete user session"""
        return await self.delete(session_id)
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user"""
        return await self.clear_prefix(f"user:{user_id}")


class RateLimitCache(CacheManager):
    """Cache manager for rate limiting"""
    
    def __init__(self, redis_client: redis.Redis):
        super().__init__(redis_client, "rate_limit")
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int
    ) -> Dict[str, Any]:
        """Check and update rate limit"""
        key = f"{identifier}:{window_seconds}"
        
        try:
            # Get current count
            current = await self.redis.get(self._make_key(key))
            current_count = int(current) if current else 0
            
            # Check if limit exceeded
            if current_count >= limit:
                ttl = await self.ttl(key)
                return {
                    "allowed": False,
                    "count": current_count,
                    "limit": limit,
                    "reset_in": ttl if ttl > 0 else window_seconds
                }
            
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(self._make_key(key))
            if current_count == 0:
                pipe.expire(self._make_key(key), window_seconds)
            
            results = await pipe.execute()
            new_count = results[0]
            
            return {
                "allowed": True,
                "count": new_count,
                "limit": limit,
                "remaining": limit - new_count,
                "reset_in": window_seconds if current_count == 0 else await self.ttl(key)
            }
        except Exception:
            # Allow on cache errors
            return {
                "allowed": True,
                "count": 0,
                "limit": limit,
                "remaining": limit,
                "reset_in": window_seconds
            }
