"""
Redis cache manager for CIS.

Provides caching for:
- User sessions
- Generated posts
- API responses
- Rate limiting data
"""

import os
import json
import redis
from typing import Optional, Any, Dict
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager with connection pooling and fallback"""
    
    def __init__(self, redis_url: Optional[str] = None, fallback_to_memory: bool = True):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL (default: from env)
            fallback_to_memory: If True, use in-memory dict if Redis unavailable
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.fallback_to_memory = fallback_to_memory
        self.client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Any] = {}
        self.using_fallback = False
        
        self._connect()
    
    def _connect(self):
        """Establish Redis connection with retry logic"""
        try:
            # Create connection pool for better performance
            pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=10,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                decode_responses=True
            )
            
            self.client = redis.Redis(connection_pool=pool)
            
            # Test connection
            self.client.ping()
            logger.info("[OK] Redis connected successfully")
            self.using_fallback = False
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"[WARN] Redis connection failed: {e}")
            
            if self.fallback_to_memory:
                logger.info("[FALLBACK] Falling back to in-memory cache")
                self.using_fallback = True
                self.client = None
            else:
                raise
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if self.using_fallback:
                return self.memory_cache.get(key)
            
            if self.client is None:
                return None
            
            value = self.client.get(key)
            if value:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
            
        except Exception as e:
            logger.error(f"Cache GET error for key '{key}': {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.using_fallback:
                self.memory_cache[key] = value
                return True
            
            if self.client is None:
                return False
            
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache SET error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.using_fallback:
                self.memory_cache.pop(key, None)
                return True
            
            if self.client is None:
                return False
            
            self.client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Cache DELETE error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            if self.using_fallback:
                return key in self.memory_cache
            
            if self.client is None:
                return False
            
            return bool(self.client.exists(key))
            
        except Exception as e:
            logger.error(f"Cache EXISTS error for key '{key}': {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value or None on error
        """
        try:
            if self.using_fallback:
                current = self.memory_cache.get(key, 0)
                new_value = current + amount
                self.memory_cache[key] = new_value
                return new_value
            
            if self.client is None:
                return None
            
            return self.client.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Cache INCREMENT error for key '{key}': {e}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on existing key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.using_fallback:
                # In-memory cache doesn't support expiration
                return True
            
            if self.client is None:
                return False
            
            return bool(self.client.expire(key, ttl))
            
        except Exception as e:
            logger.error(f"Cache EXPIRE error for key '{key}': {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            if self.using_fallback:
                # Simple pattern matching for memory cache
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                return len(keys_to_delete)
            
            if self.client is None:
                return 0
            
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Cache CLEAR_PATTERN error for pattern '{pattern}': {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check cache health.
        
        Returns:
            Health status dict
        """
        try:
            if self.using_fallback:
                return {
                    'status': 'degraded',
                    'backend': 'memory',
                    'keys': len(self.memory_cache),
                    'message': 'Using in-memory fallback'
                }
            
            if self.client is None:
                return {
                    'status': 'down',
                    'backend': 'redis',
                    'message': 'Redis not connected'
                }
            
            # Ping Redis
            self.client.ping()
            info = self.client.info('stats')
            
            return {
                'status': 'healthy',
                'backend': 'redis',
                'total_keys': self.client.dbsize(),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'unknown')
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'backend': 'redis',
                'message': str(e)
            }
    
    def close(self):
        """Close Redis connection"""
        try:
            if self.client:
                self.client.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get global cache instance (singleton pattern)"""
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = RedisCache()
    
    return _cache_instance


# Convenience functions
def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    return get_cache().get(key)


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache"""
    return get_cache().set(key, value, ttl)


def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    return get_cache().delete(key)


def cache_exists(key: str) -> bool:
    """Check if key exists"""
    return get_cache().exists(key)
