from typing import Generator
import redis
from core.config import settings

def get_redis() -> Generator:
    """Get Redis connection"""
    try:
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        yield r
    except Exception as e:
        raise e
    finally:
        r.close()
