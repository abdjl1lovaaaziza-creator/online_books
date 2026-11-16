import json
import time
from typing import Optional, Any
import redis.asyncio as aioredis
from loguru import logger
from app.config import settings


class CacheService:
    """Async Redis cache manager with graceful in-memory fallback."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[aioredis.Redis] = None
        self._in_memory_store: dict[str, tuple[Any, Optional[float]]] = {}
        self.is_connected = False

    async def connect(self) -> None:
        """Establish Redis connection with fallback to in-memory store."""
        try:
            self.client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0
            )
            await self.client.ping()
            self.is_connected = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            self.is_connected = False
            self.client = None
            logger.warning(f"Could not connect to Redis: {e}. Utilizing in-memory cache fallback.")

    async def close(self) -> None:
        """Close connection to Redis."""
        if self.client:
            await self.client.aclose()
            self.is_connected = False
            logger.info("Redis connection closed.")

    async def get(self, key: str) -> Optional[str]:
        """Retrieve value from cache."""
        if self.is_connected and self.client:
            try:
                return await self.client.get(key)
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        # In-memory fallback
        if key in self._in_memory_store:
            val, expiry = self._in_memory_store[key]
            if expiry is None or expiry > time.time():
                return val
            del self._in_memory_store[key]
        return None

    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """Store value in cache with optional TTL."""
        if self.is_connected and self.client:
            try:
                await self.client.set(key, value, ex=expire_seconds)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")

        # In-memory fallback
        expiry = time.time() + expire_seconds if expire_seconds else None
        self._in_memory_store[key] = (value, expiry)
        return True

    async def get_json(self, key: str) -> Optional[Any]:
        """Fetch and deserialize JSON value."""
        data = await self.get(key)
        if data:
            try:
                return json.loads(data)
            except Exception:
                return None
        return None

    async def set_json(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Serialize and store JSON value."""
        try:
            data = json.dumps(value)
            return await self.set(key, data, expire_seconds=expire_seconds)
        except Exception as e:
            logger.error(f"Error serializing JSON for cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Remove key from cache."""
        if self.is_connected and self.client:
            try:
                await self.client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

        if key in self._in_memory_store:
            del self._in_memory_store[key]
            return True
        return False

    async def check_rate_limit(self, user_id: int, max_calls: int = 10, period: int = 3) -> bool:
        """
        Token-bucket rate limiter.
        Returns True if request is allowed, False if user exceeded rate limit.
        """
        key = f"rl:{user_id}"
        if self.is_connected and self.client:
            try:
                current = await self.client.incr(key)
                if current == 1:
                    await self.client.expire(key, period)
                return current <= max_calls
            except Exception as e:
                logger.error(f"Redis rate limit check error: {e}")

        # In-memory rate limiting fallback
        now = time.time()
        val = self._in_memory_store.get(key)
        if val is None or (val[1] and val[1] < now):
            self._in_memory_store[key] = (1, now + period)
            return True
        count, expiry = val
        if count >= max_calls:
            return False
        self._in_memory_store[key] = (count + 1, expiry)
        return True

    @property
    def status_str(self) -> str:
        """Human-readable status for admin panel."""
        return "Connected (Redis)" if self.is_connected else "Running (In-Memory Fallback)"


cache = CacheService(settings.REDIS_URL)
