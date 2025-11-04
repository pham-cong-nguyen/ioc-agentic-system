"""
Redis cache manager
"""
import json
import pickle
from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio import Redis
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,
                max_connections=50
            )
            await self.redis.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis or not settings.CACHE_ENABLED:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                # Try to deserialize as JSON first
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Fall back to pickle
                    return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.redis or not settings.CACHE_ENABLED:
            return False
        
        try:
            # Try to serialize as JSON first
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                # Fall back to pickle
                serialized = pickle.dumps(value)
            
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear(self, pattern: str = "*") -> int:
        """Clear cache by pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error for pattern {pattern}: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment value"""
        if not self.redis:
            return 0
        
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def get_ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self.redis:
            return -1
        
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1


# Global cache instance
cache = RedisCache()


async def init_cache():
    """Initialize cache connection"""
    await cache.connect()


async def close_cache():
    """Close cache connection"""
    await cache.close()
