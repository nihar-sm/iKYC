import redis
import json
import logging
from typing import Optional, Dict, Any
from .config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def set_user_data(self, user_id: str, data: Dict[str, Any], expire_seconds: int = 3600):
        key = f"user:{user_id}"
        return self.redis_client.setex(key, expire_seconds, json.dumps(data))

    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        key = f"user:{user_id}"
        data = self.redis_client.get(key)
        return json.loads(data) if data else None

    def set_session_data(self, session_id: str, data: Dict[str, Any], expire_seconds: int = 1800):
        key = f"session:{session_id}"
        return self.redis_client.setex(key, expire_seconds, json.dumps(data))

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        key = f"session:{session_id}"
        data = self.redis_client.get(key)
        return json.loads(data) if data else None

db = RedisManager()
