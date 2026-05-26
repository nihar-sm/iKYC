import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .redis_client.operations import redis_ops
from .schemas.aadhaar_schema import AadhaarSchema
from .schemas.pan_schema import PANSchema
from .schemas.user_schema import UserSchema
from .schemas.session_schema import SessionSchema

logger = logging.getLogger(__name__)

class DataManager:
    """Main data access layer for KYC system"""
    
    def __init__(self):
        self.redis_ops = redis_ops
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, user_data: UserSchema) -> bool:
        """Create a new user record"""
        try:
            return self.redis_ops.store_user_kyc_data(user_data.user_id, user_data.to_dict())
        except Exception as e:
            logger.error(f"Error creating user {user_data.user_id}: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record"""
        try:
            return self.redis_ops.get_user_kyc_data(user_id)
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            return None
    
    def update_user_kyc_status(self, user_id: str, status: str) -> bool:
        """Update user KYC status"""
        try:
            user_data = self.get_user(user_id)
            if user_data:
                user_data['kyc_status'] = status
                user_data['last_updated'] = datetime.now().isoformat()
                return self.redis_ops.store_user_kyc_data(user_id, user_data)
            return False
        except Exception as e:
            logger.error(f"Error updating KYC status for user {user_id}: {e}")
            return False
    
    # ==================== AADHAAR OPERATIONS ====================
    
    def store_aadhaar_record(self, aadhaar_data: AadhaarSchema) -> bool:
        """Store Aadhaar verification data"""
        try:
            return self.redis_ops.store_aadhaar_data(
                aadhaar_data.aadhaar_number,
                aadhaar_data.to_dict()
            )
        except Exception as e:
            logger.error(f"Error storing Aadhaar record: {e}")
            return False
    
    def get_aadhaar_record(self, aadhaar_number: str) -> Optional[Dict[str, Any]]:
        """Retrieve Aadhaar record"""
        try:
            return self.redis_ops.get_aadhaar_data(aadhaar_number)
        except Exception as e:
            logger.error(f"Error retrieving Aadhaar record: {e}")
            return None
    
    # ==================== PAN OPERATIONS ====================
    
    def store_pan_record(self, pan_data: PANSchema) -> bool:
        """Store PAN verification data"""
        try:
            return self.redis_ops.store_pan_data(
                pan_data.pan_number,
                pan_data.to_dict()
            )
        except Exception as e:
            logger.error(f"Error storing PAN record: {e}")
            return False
    
    def get_pan_record(self, pan_number: str) -> Optional[Dict[str, Any]]:
        """Retrieve PAN record"""
        try:
            return self.redis_ops.get_pan_data(pan_number)
        except Exception as e:
            logger.error(f"Error retrieving PAN record: {e}")
            return None
    
    # ==================== SESSION OPERATIONS ====================
    
    def create_session(self, session_data: SessionSchema) -> bool:
        """Create a new user session"""
        try:
            return self.redis_ops.store_session_data(
                session_data.session_id,
                session_data.to_dict()
            )
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    # ==================== OTP OPERATIONS ====================
    
    def generate_and_store_otp(self, phone_number: str) -> Optional[str]:
        """Generate and store OTP for phone verification"""
        import random
        try:
            otp = str(random.randint(100000, 999999))
            if self.redis_ops.store_otp_data(phone_number, otp):
                logger.info(f"OTP generated for phone: {phone_number}")
                return otp
            return None
        except Exception as e:
            logger.error(f"Error generating OTP for phone {phone_number}: {e}")
            return None
    
    def verify_phone_otp(self, phone_number: str, provided_otp: str) -> Dict[str, Any]:
        """Verify OTP for phone number"""
        try:
            return self.redis_ops.verify_otp(phone_number, provided_otp)
        except Exception as e:
            logger.error(f"Error verifying OTP for phone {phone_number}: {e}")
            return {'success': False, 'reason': 'System error'}
    
    # ==================== BLACKLIST OPERATIONS ====================
    
    def add_to_blacklist(self, identifier: str, reason: str = "Fraudulent activity") -> bool:
        """Add identifier to blacklist"""
        try:
            return self.redis_ops.add_to_blacklist(identifier, reason)
        except Exception as e:
            logger.error(f"Error adding {identifier} to blacklist: {e}")
            return False
    
    def check_blacklist(self, identifier: str) -> Dict[str, Any]:
        """Check if identifier is blacklisted"""
        try:
            return self.redis_ops.is_blacklisted(identifier)
        except Exception as e:
            logger.error(f"Error checking blacklist for {identifier}: {e}")
            return {'is_blacklisted': False}
    
    # ==================== STATISTICS ====================
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            return {
                'total_users': self.redis_ops.get_keys_count_by_pattern("kyc:user:*"),
                'aadhaar_records': self.redis_ops.get_keys_count_by_pattern("aadhaar:*"),
                'pan_records': self.redis_ops.get_keys_count_by_pattern("pan:*"),
                'active_sessions': self.redis_ops.get_keys_count_by_pattern("session:*"),
                'blacklisted_items': self.redis_ops.get_keys_count_by_pattern("blacklist:*"),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

# Global data manager instance
data_manager = DataManager()
