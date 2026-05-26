"""
Contact Information Validators (Phone, OTP)
"""

import re
from datetime import datetime, timedelta
from typing import Dict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.validation_config import ValidationConfig
from utils.common_utils import ValidationUtils

class ContactValidators:
    """Validators for contact information"""
    
    @staticmethod
    def validate_phone_number(phone_number: str) -> Dict:
        """
        Validate Indian phone number
        
        Rules:
        - Must be 10 digits
        - Must start with [6-9]
        - Can optionally include +91 or 0 prefix
        """
        
        # Clean input
        phone_clean = ValidationUtils.clean_numeric_input(phone_number) if phone_number else ""
        
        # Empty check
        if not phone_clean:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="phone_number",
                error="Phone number cannot be empty",
                error_code="EMPTY_PHONE"
            )
        
        # Remove country code prefixes
        if phone_clean.startswith('91') and len(phone_clean) == 12:
            phone_clean = phone_clean[2:]
        elif phone_clean.startswith('0') and len(phone_clean) == 11:
            phone_clean = phone_clean[1:]
        
        # Length validation
        if len(phone_clean) != ValidationConfig.PHONE_LENGTH:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="phone_number",
                error=f"Phone number must be exactly {ValidationConfig.PHONE_LENGTH} digits",
                error_code="INVALID_PHONE_LENGTH"
            )
        
        # Pattern validation: Must start with 6-9
        phone_pattern = r"^[6-9][0-9]{9}$"
        if not re.match(phone_pattern, phone_clean):
            return ValidationUtils.create_validation_response(
                valid=False,
                field="phone_number",
                error="Phone number must start with 6, 7, 8, or 9",
                error_code="INVALID_PHONE_FORMAT"
            )
        
        # Invalid patterns check
        invalid_patterns = [
            "0000000000", "1111111111", "2222222222", "3333333333",
            "4444444444", "5555555555", "9999999999", "1234567890"
        ]
        
        if phone_clean in invalid_patterns:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="phone_number",
                error="Phone number appears to be invalid",
                error_code="INVALID_PHONE_PATTERN"
            )
        
        # Success response
        return ValidationUtils.create_validation_response(
            valid=True,
            field="phone_number",
            message="Phone number validation successful",
            data={
                "cleaned_value": phone_clean,
                "formatted_value": ValidationUtils.format_phone_number(phone_clean),
                "country_code": "+91"
            }
        )
    
    @staticmethod
    def generate_otp(phone_number: str, redis_client=None) -> Dict:
        """
        Generate OTP for phone number verification
        
        Args:
            phone_number: Validated phone number
            redis_client: Redis client for OTP storage
        """
        
        # First validate phone number
        phone_validation = ContactValidators.validate_phone_number(phone_number)
        if not phone_validation['valid']:
            return phone_validation
        
        phone_clean = phone_validation.get('cleaned_value', '')
        
        # Generate OTP
        otp = ValidationUtils.generate_otp(ValidationConfig.OTP_LENGTH)
        otp_key = f"otp:{phone_clean}"
        
        # Store OTP (in Redis or mock storage)
        if redis_client:
            try:
                # Store OTP with expiry
                redis_client.set(otp_key, otp, ex=ValidationConfig.OTP_VALIDITY_MINUTES * 60)
                
                return ValidationUtils.create_validation_response(
                    valid=True,
                    field="otp_generation",
                    message="OTP generated and sent successfully",
                    data={
                        "phone_number": phone_clean,
                        "otp_length": ValidationConfig.OTP_LENGTH,
                        "validity_minutes": ValidationConfig.OTP_VALIDITY_MINUTES,
                        "otp": otp  # In production, don't return OTP in response
                    }
                )
                
            except Exception as e:
                return ValidationUtils.create_validation_response(
                    valid=False,
                    field="otp_generation",
                    error=f"Failed to generate OTP: {str(e)}",
                    error_code="OTP_GENERATION_ERROR"
                )
        else:
            # Mock OTP generation (for testing)
            return ValidationUtils.create_validation_response(
                valid=True,
                field="otp_generation",
                message="OTP generated successfully (mock mode)",
                data={
                    "phone_number": phone_clean,
                    "otp": otp,  # Return for testing
                    "validity_minutes": ValidationConfig.OTP_VALIDITY_MINUTES
                }
            )
    
    @staticmethod
    def verify_otp(phone_number: str, otp_input: str, redis_client=None) -> Dict:
        """
        Verify OTP for phone number
        
        Args:
            phone_number: Phone number
            otp_input: OTP entered by user
            redis_client: Redis client for OTP retrieval
        """
        
        # Clean inputs
        phone_clean = ValidationUtils.clean_numeric_input(phone_number)
        otp_clean = ValidationUtils.clean_numeric_input(otp_input)
        
        # Basic validation
        if not phone_clean or not otp_clean:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="otp_verification",
                error="Phone number and OTP cannot be empty",
                error_code="EMPTY_OTP_FIELDS"
            )
        
        if len(otp_clean) != ValidationConfig.OTP_LENGTH:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="otp_verification",
                error=f"OTP must be exactly {ValidationConfig.OTP_LENGTH} digits",
                error_code="INVALID_OTP_LENGTH"
            )
        
        otp_key = f"otp:{phone_clean}"
        
        # Verify OTP
        if redis_client:
            try:
                stored_otp = redis_client.get(otp_key)
                
                if not stored_otp:
                    return ValidationUtils.create_validation_response(
                        valid=False,
                        field="otp_verification",
                        error="OTP has expired or was not generated",
                        error_code="OTP_EXPIRED"
                    )
                
                stored_otp_str = stored_otp.decode('utf-8')
                
                if stored_otp_str == otp_clean:
                    # OTP verified - delete it
                    redis_client.delete(otp_key)
                    
                    return ValidationUtils.create_validation_response(
                        valid=True,
                        field="otp_verification",
                        message="OTP verified successfully",
                        data={
                            "phone_number": phone_clean,
                            "verified_at": datetime.now().isoformat()
                        }
                    )
                else:
                    return ValidationUtils.create_validation_response(
                        valid=False,
                        field="otp_verification",
                        error="Invalid OTP entered",
                        error_code="INVALID_OTP"
                    )
                    
            except Exception as e:
                return ValidationUtils.create_validation_response(
                    valid=False,
                    field="otp_verification",
                    error=f"OTP verification error: {str(e)}",
                    error_code="OTP_VERIFICATION_ERROR"
                )
        else:
            # Mock OTP verification (always accept "123456" for testing)
            if otp_clean == "123456":
                return ValidationUtils.create_validation_response(
                    valid=True,
                    field="otp_verification",
                    message="OTP verified successfully (mock mode)",
                    data={
                        "phone_number": phone_clean,
                        "verified_at": datetime.now().isoformat()
                    }
                )
            else:
                return ValidationUtils.create_validation_response(
                    valid=False,
                    field="otp_verification",
                    error="Invalid OTP (use 123456 for testing)",
                    error_code="INVALID_OTP_MOCK"
                )
