from __future__ import annotations
import redis
from farmxpert.config.settings import settings


def get_redis_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


