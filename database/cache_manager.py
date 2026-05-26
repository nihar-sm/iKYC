import logging
from typing import Any, Optional, Dict, Callable
from functools import wraps
import hashlib
import json
from .redis_client.operations import redis_ops
from datetime import datetime

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced caching manager for performance optimization"""
    
    def __init__(self):
        self.redis_ops = redis_ops
        self.default_cache_time = 3600  # 1 hour
        self.cache_prefix = "cache"
    
    def _generate_cache_key(self, key: str, namespace: str = None) -> str:
        """Generate standardized cache key"""
        if namespace:
            return f"{self.cache_prefix}:{namespace}:{key}"
        return f"{self.cache_prefix}:{key}"
    
    def set(self, key: str, value: Any, expiry_seconds: Optional[int] = None, 
            namespace: str = None) -> bool:
        """Set cache with optional expiry and namespace"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            expiry = expiry_seconds or self.default_cache_time
            return self.redis_ops.set_data(cache_key, value, expiry)
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False
    
    def get(self, key: str, namespace: str = None) -> Optional[Any]:
        """Get cached value with optional namespace"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            return self.redis_ops.get_data(cache_key)
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None
    
    def delete(self, key: str, namespace: str = None) -> bool:
        """Delete cached value with optional namespace"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            return self.redis_ops.delete_data(cache_key)
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False
    
    def exists(self, key: str, namespace: str = None) -> bool:
        """Check if cache exists with optional namespace"""
        try:
            cache_key = self._generate_cache_key(key, namespace)
            return self.redis_ops.exists(cache_key)
        except Exception as e:
            logger.error(f"Error checking cache existence for key {key}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_keys = self.redis_ops.get_keys_count_by_pattern(f"{self.cache_prefix}:*")
            return {
                'total_cached_items': total_keys,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

# Global cache manager instance
cache_manager = CacheManager()
