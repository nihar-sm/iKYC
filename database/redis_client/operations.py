import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .connection import redis_connection

logger = logging.getLogger(__name__)

class RedisOperations:
    """Redis CRUD operations for KYC data management"""
    
    def __init__(self):
        self.client = redis_connection.get_client()
    
    # ==================== BASIC OPERATIONS ====================
    
    def set_data(self, key: str, value: Any, expiry_seconds: Optional[int] = None) -> bool:
        """Store data in Redis with optional expiry"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            result = self.client.set(key, value, ex=expiry_seconds)
            logger.debug(f"Data stored with key: {key}")
            return result
        except Exception as e:
            logger.error(f"Error storing data with key {key}: {e}")
            return False
    
    def get_data(self, key: str) -> Optional[Any]:
        """Retrieve data from Redis"""
        try:
            value = self.client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Error retrieving data with key {key}: {e}")
            return None
    
    def delete_data(self, key: str) -> bool:
        """Delete data from Redis"""
        try:
            result = self.client.delete(key)
            logger.debug(f"Data deleted with key: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting data with key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False
    
    def set_expiry(self, key: str, seconds: int) -> bool:
        """Set expiry time for existing key"""
        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error setting expiry for key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -1
    
    # ==================== KYC SPECIFIC OPERATIONS ====================
    
    def store_user_kyc_data(self, user_id: str, kyc_data: Dict[str, Any]) -> bool:
        """Store complete KYC data for a user"""
        key = f"kyc:user:{user_id}"
        kyc_data['timestamp'] = datetime.now().isoformat()
        kyc_data['user_id'] = user_id
        kyc_data['last_updated'] = datetime.now().isoformat()
        return self.set_data(key, kyc_data, expiry_seconds=86400 * 30)  # 30 days
    
    def get_user_kyc_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete KYC data for a user"""
        key = f"kyc:user:{user_id}"
        return self.get_data(key)
    
    def store_aadhaar_data(self, aadhaar_number: str, data: Dict[str, Any]) -> bool:
        """Store Aadhaar verification data"""
        key = f"aadhaar:{aadhaar_number}"
        data['verification_timestamp'] = datetime.now().isoformat()
        data['aadhaar_number'] = aadhaar_number
        return self.set_data(key, data, expiry_seconds=3600 * 6)  # 6 hours
    
    def get_aadhaar_data(self, aadhaar_number: str) -> Optional[Dict[str, Any]]:
        """Retrieve Aadhaar verification data"""
        key = f"aadhaar:{aadhaar_number}"
        return self.get_data(key)
    
    def store_pan_data(self, pan_number: str, data: Dict[str, Any]) -> bool:
        """Store PAN verification data"""
        key = f"pan:{pan_number}"
        data['verification_timestamp'] = datetime.now().isoformat()
        data['pan_number'] = pan_number
        return self.set_data(key, data, expiry_seconds=3600 * 6)  # 6 hours
    
    def get_pan_data(self, pan_number: str) -> Optional[Dict[str, Any]]:
        """Retrieve PAN verification data"""
        key = f"pan:{pan_number}"
        return self.get_data(key)
    
    def store_otp_data(self, phone_number: str, otp: str, expiry_minutes: int = 5) -> bool:
        """Store OTP data with expiry"""
        key = f"otp:{phone_number}"
        otp_data = {
            'otp': otp,
            'created_at': datetime.now().isoformat(),
            'phone_number': phone_number,
            'attempts': 0
        }
        return self.set_data(key, otp_data, expiry_seconds=expiry_minutes * 60)
    
    def verify_otp(self, phone_number: str, provided_otp: str) -> Dict[str, Any]:
        """Verify OTP for a phone number with attempt tracking"""
        key = f"otp:{phone_number}"
        stored_data = self.get_data(key)
        
        if not stored_data:
            return {'success': False, 'reason': 'OTP not found or expired'}
        
        attempts = stored_data.get('attempts', 0) + 1
        stored_data['attempts'] = attempts
        
        if attempts > 3:
            self.delete_data(key)
            return {'success': False, 'reason': 'Maximum attempts exceeded'}
        
        self.set_data(key, stored_data, expiry_seconds=self.get_ttl(key))
        
        if stored_data.get('otp') == provided_otp:
            self.delete_data(key)
            logger.info(f"OTP verified successfully for: {phone_number}")
            return {'success': True, 'reason': 'OTP verified successfully'}
        
        return {'success': False, 'reason': 'Invalid OTP', 'attempts_remaining': 3 - attempts}
    
    def store_session_data(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Store user session data"""
        key = f"session:{session_id}"
        session_data['created_at'] = datetime.now().isoformat()
        session_data['last_activity'] = datetime.now().isoformat()
        return self.set_data(key, session_data, expiry_seconds=3600 * 24)  # 24 hours
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data and update last activity"""
        key = f"session:{session_id}"
        session_data = self.get_data(key)
        
        if session_data:
            session_data['last_activity'] = datetime.now().isoformat()
            self.set_data(key, session_data, expiry_seconds=self.get_ttl(key))
        
        return session_data
    
    def add_to_blacklist(self, identifier: str, reason: str, blacklist_type: str = "general") -> bool:
        """Add identifier to blacklist with type classification"""
        key = f"blacklist:{blacklist_type}:{identifier}"
        blacklist_data = {
            'identifier': identifier,
            'reason': reason,
            'type': blacklist_type,
            'blacklisted_at': datetime.now().isoformat()
        }
        return self.set_data(key, blacklist_data)
    
    def is_blacklisted(self, identifier: str, blacklist_type: str = "general") -> Dict[str, Any]:
        """Check if identifier is blacklisted with details"""
        key = f"blacklist:{blacklist_type}:{identifier}"
        blacklist_data = self.get_data(key)
        
        if blacklist_data:
            return {
                'is_blacklisted': True,
                'reason': blacklist_data.get('reason'),
                'blacklisted_at': blacklist_data.get('blacklisted_at')
            }
        
        return {'is_blacklisted': False}
    
    # ==================== UTILITY OPERATIONS ====================
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern"""
        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting keys by pattern {pattern}: {e}")
            return []
    
    def get_keys_count_by_pattern(self, pattern: str) -> int:
        """Get count of keys matching a pattern"""
        try:
            return len(self.client.keys(pattern))
        except Exception as e:
            logger.error(f"Error counting keys by pattern {pattern}: {e}")
            return 0
    
    def bulk_delete_by_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error bulk deleting keys by pattern {pattern}: {e}")
            return 0

# Global Redis operations instance
redis_ops = RedisOperations()
