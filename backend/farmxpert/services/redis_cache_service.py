"""
Redis Cache Service for FarmXpert
Provides efficient caching for AI responses and frequently accessed data
"""

import json
import asyncio
import atexit
import inspect
import redis.asyncio as redis
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from farmxpert.config.settings import settings
from farmxpert.core.utils.logger import get_logger


class RedisCacheService:
    def __init__(self):
        self.logger = get_logger("redis_cache")
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False

        # Best-effort cleanup for short-lived scripts (Windows asyncio loop teardown).
        # Uses sync disconnect to avoid depending on an active event loop.
        atexit.register(self._disconnect_sync)
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.logger.info("Redis cache service initialized successfully")
            self._initialized = True
        except Exception as e:
            self.logger.warning(f"Failed to initialize Redis cache: {e}. Using in-memory fallback.")
            self.redis_client = None
            self._initialized = True

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self._initialize_redis()

    def _disconnect_sync(self) -> None:
        """Sync-safe disconnect used during interpreter shutdown.

        redis.asyncio objects may emit 'Event loop is closed' if left to __del__.
        Disconnecting the pool avoids that in short-lived scripts.
        """
        try:
            # If we're currently inside an active event loop, do nothing here.
            # Proper async shutdown should call `await redis_cache.close()`.
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    return
            except RuntimeError:
                pass

            client = self.redis_client
            if not client:
                return
            pool = getattr(client, "connection_pool", None)
            if pool and hasattr(pool, "disconnect"):
                maybe = pool.disconnect(inuse_connections=True)
                if inspect.isawaitable(maybe):
                    loop = asyncio.new_event_loop()
                    try:
                        loop.run_until_complete(maybe)
                    finally:
                        loop.close()
        except Exception:
            # Never raise during shutdown
            pass
    
    async def is_available(self) -> bool:
        """Check if Redis is available"""
        self._ensure_initialized()
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not await self.is_available():
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                self.logger.debug(f"Cache hit for key: {key[:8]}...")
            return value
        except Exception as e:
            self.logger.error(f"Error getting from cache: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not await self.is_available():
            return False
        
        try:
            await self.redis_client.setex(key, ttl, value)
            self.logger.debug(f"Cached value for key: {key[:8]}... (TTL: {ttl}s)")
            return True
        except Exception as e:
            self.logger.error(f"Error setting cache: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value from cache"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to decode JSON for key: {key[:8]}...")
        return None
    
    async def set_json(self, key: str, data: Dict[str, Any], ttl: int = 300) -> bool:
        """Set JSON value in cache"""
        try:
            value = json.dumps(data, default=str)
            return await self.set(key, value, ttl)
        except Exception as e:
            self.logger.error(f"Error serializing JSON for cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not await self.is_available():
            return False
        
        try:
            result = await self.redis_client.delete(key)
            self.logger.debug(f"Deleted cache key: {key[:8]}...")
            return bool(result)
        except Exception as e:
            self.logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not await self.is_available():
            return False
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception:
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get TTL for a key"""
        if not await self.is_available():
            return -1
        
        try:
            return await self.redis_client.ttl(key)
        except Exception:
            return -1
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not await self.is_available():
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            self.logger.error(f"Error clearing pattern {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not await self.is_available():
            return {"status": "unavailable", "error": "Redis not connected"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "available",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "total_keys": await self.redis_client.dbsize()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0
    
    async def close(self):
        """Close Redis connection"""
        if not self.redis_client:
            return
        try:
            await self.redis_client.close()
        finally:
            # Ensure sync disconnect to prevent loop-closed warnings
            self._disconnect_sync()
            self.redis_client = None
            self.logger.info("Redis connection closed")


# Global instance
redis_cache = RedisCacheService()
