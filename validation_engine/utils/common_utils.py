"""
Common utilities for validation engine
"""
import re
import random
from datetime import datetime
from typing import Dict, Any

class ValidationUtils:
    """Utility functions for validation"""
    
    @staticmethod
    def clean_numeric_input(input_str: str) -> str:
        """Clean numeric input by removing non-digits"""
        if not input_str:
            return ""
        return re.sub(r'\D', '', str(input_str))
    
    @staticmethod
    def clean_text_input(input_str: str) -> str:
        """Clean text input by removing extra spaces"""
        if not input_str:
            return ""
        return re.sub(r'\s+', ' ', str(input_str).strip())
    
    @staticmethod
    def create_validation_response(valid: bool, field: str, message: str = "", 
                                 error: str = "", error_code: str = "", data: Dict = None) -> Dict:
        """Create standardized validation response"""
        response = {
            "valid": valid,
            "field": field,
            "timestamp": datetime.now().isoformat()
        }
        
        if valid:
            response["message"] = message
            if data:
                response["data"] = data
        else:
            response["error"] = error
            if error_code:
                response["error_code"] = error_code
        
        return response
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate numeric OTP"""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """Format phone number for display"""
        if len(phone) == 10:
            return f"{phone[:3]} {phone[3:6]} {phone[6:]}"
        return phone

class MockRedisClient:
    """Mock Redis client for testing"""
    
    def __init__(self):
        self.data = {
            # Sample Aadhaar data
            "aadhaar:234567890124": json.dumps({
                "name": "Test User",
                "dob": "15-08-1990",
                "status": "ACTIVE"
            }),
            # Sample PAN data
            "pan:ABCDE1234F": json.dumps({
                "name": "Test User", 
                "dob": "15-08-1990",
                "status": "ACTIVE"
            })
        }
    
    def get(self, key: str):
        """Mock get method"""
        return self.data.get(key, "").encode('utf-8') if self.data.get(key) else None
    
    def set(self, key: str, value: str, ex: int = None):
        """Mock set method"""
        self.data[key] = value
        return True
    
    def exists(self, key: str) -> bool:
        """Mock exists method"""
        return key in self.data
    
    def delete(self, key: str) -> bool:
        """Mock delete method"""
        if key in self.data:
            del self.data[key]
            return True
        return False

import json  # Add this import at the top
