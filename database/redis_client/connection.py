import redis
import os
from typing import Optional
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisConnection:
    """Redis connection manager for IntelliKYC system"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        # Docker-friendly configuration
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD', None)

    def connect(self) -> redis.Redis:
        """Establish connection to Redis server"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=10,  # Increased for Docker
                socket_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            self.client.ping()
            logger.info(f"✅ Successfully connected to Redis at {self.host}:{self.port}")
            return self.client

        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    def get_client(self) -> redis.Redis:
        """Get Redis client, connect if not already connected"""
        if self.client is None:
            return self.connect()
        
        try:
            self.client.ping()
            return self.client
        except redis.ConnectionError:
            logger.warning("⚠️ Redis connection lost, reconnecting...")
            return self.connect()

    def close_connection(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("✅ Redis connection closed")

    def get_info(self) -> dict:
        """Get Redis server information"""
        try:
            client = self.get_client()
            return client.info()
        except Exception as e:
            logger.error(f"❌ Error getting Redis info: {e}")
            return {}

# Global Redis connection instance
redis_connection = RedisConnection()
