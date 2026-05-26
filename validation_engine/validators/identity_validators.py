"""
Identity Document Validators for Indian KYC (Aadhaar, PAN) with Redis Integration
"""

import re
import json
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.validation_config import ValidationConfig
from utils.common_utils import ValidationUtils

class IdentityValidators:
    """Validators for Indian identity documents with Redis database integration"""
    
    @staticmethod
    def validate_aadhaar(aadhaar_number: str, redis_client=None) -> Dict:
        """
        Validate Aadhaar number with simple rules + Redis database lookup
        
        Rules:
        - Must be exactly 12 digits
        - Cannot be all same digits (111111111111)
        - Cannot be obvious patterns (123456789012)
        - Must exist in Redis database
        
        Args:
            aadhaar_number (str): Aadhaar number to validate
            redis_client: Redis client instance from teammate
            
        Returns:
            Dict: Validation result
        """
        
        # Clean input
        aadhaar_clean = ValidationUtils.clean_numeric_input(aadhaar_number) if aadhaar_number else ""
        
        # Empty check
        if not aadhaar_clean:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="aadhaar_number",
                error="Aadhaar number cannot be empty",
                error_code="EMPTY_AADHAAR"
            )
        
        # Length validation
        if len(aadhaar_clean) != ValidationConfig.AADHAAR_LENGTH:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="aadhaar_number",
                error=f"Aadhaar must be exactly {ValidationConfig.AADHAAR_LENGTH} digits. Provided: {len(aadhaar_clean)} digits",
                error_code="INVALID_AADHAAR_LENGTH"
            )
        
        # Same digits check
        if len(set(aadhaar_clean)) == 1:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="aadhaar_number",
                error="Aadhaar cannot be all same digits (e.g., 111111111111)",
                error_code="SAME_DIGITS_AADHAAR"
            )
        
        # Invalid patterns check
        invalid_patterns = [
            "000000000000", "111111111111", "222222222222", "333333333333",
            "444444444444", "555555555555", "666666666666", "777777777777",
            "888888888888", "999999999999", "123456789012", "987654321098"
        ]
        
        if aadhaar_clean in invalid_patterns:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="aadhaar_number",
                error="Aadhaar number appears to be an invalid test pattern",
                error_code="INVALID_AADHAAR_PATTERN"
            )
        
        # Redis database lookup
        if redis_client:
            try:
                redis_key = f"aadhaar:{aadhaar_clean}"
                
                if redis_client.exists(redis_key):
                    aadhaar_data_json = redis_client.get(redis_key)
                    
                    if aadhaar_data_json:
                        try:
                            aadhaar_data = json.loads(aadhaar_data_json.decode('utf-8'))
                            
                            return ValidationUtils.create_validation_response(
                                valid=True,
                                field="aadhaar_number",
                                message="Aadhaar validated successfully",
                                data={
                                    "cleaned_value": aadhaar_clean,
                                    "formatted_value": f"{aadhaar_clean[:4]} {aadhaar_clean[4:8]} {aadhaar_clean[8:12]}",
                                    "database_status": "FOUND",
                                    "database_data": aadhaar_data
                                }
                            )
                            
                        except json.JSONDecodeError:
                            return ValidationUtils.create_validation_response(
                                valid=False,
                                field="aadhaar_number",
                                error="Database data format error",
                                error_code="DATABASE_FORMAT_ERROR"
                            )
                else:
                    return ValidationUtils.create_validation_response(
                        valid=False,
                        field="aadhaar_number",
                        error="Aadhaar number not found in database",
                        error_code="AADHAAR_NOT_FOUND"
                    )
                    
            except Exception as e:
                return ValidationUtils.create_validation_response(
                    valid=False,
                    field="aadhaar_number",
                    error=f"Database connection error: {str(e)}",
                    error_code="DATABASE_ERROR"
                )
        else:
            # No Redis client provided - basic validation only
            return ValidationUtils.create_validation_response(
                valid=True,
                field="aadhaar_number",
                message="Aadhaar format validation successful (database check skipped)",
                data={
                    "cleaned_value": aadhaar_clean,
                    "formatted_value": f"{aadhaar_clean[:4]} {aadhaar_clean[4:8]} {aadhaar_clean[8:12]}",
                    "database_status": "NOT_CHECKED"
                }
            )
    
    @staticmethod
    def validate_pan(pan_number: str, redis_client=None) -> Dict:
        """
        Validate PAN number with format rules + Redis database lookup
        
        Rules:
        - Must match format: 5 letters + 4 digits + 1 letter (ABCDE1234F)
        - All letters must be uppercase
        - Must exist in Redis database
        
        Args:
            pan_number (str): PAN number to validate
            redis_client: Redis client instance from teammate
            
        Returns:
            Dict: Validation result
        """
        
        # Clean input
        pan_clean = str(pan_number).replace(" ", "").upper() if pan_number else ""
        
        # Empty check
        if not pan_clean:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="pan_number",
                error="PAN number cannot be empty",
                error_code="EMPTY_PAN"
            )
        
        # Length validation
        if len(pan_clean) != ValidationConfig.PAN_LENGTH:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="pan_number",
                error=f"PAN must be exactly {ValidationConfig.PAN_LENGTH} characters. Provided: {len(pan_clean)} characters",
                error_code="INVALID_PAN_LENGTH"
            )
        
        # Format validation
        pan_pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
        if not re.match(pan_pattern, pan_clean):
            return ValidationUtils.create_validation_response(
                valid=False,
                field="pan_number",
                error="PAN format invalid. Must be 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)",
                error_code="INVALID_PAN_FORMAT"
            )
        
        # Dummy patterns check
        dummy_patterns = ["AAAAA0000A", "ZZZZZ9999Z", "ABCDE0000F", "PQRST9999U"]
        if pan_clean in dummy_patterns:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="pan_number",
                error="PAN appears to be a test/dummy pattern",
                error_code="DUMMY_PAN_PATTERN"
            )
        
        # Redis database lookup
        if redis_client:
            try:
                redis_key = f"pan:{pan_clean}"
                
                if redis_client.exists(redis_key):
                    pan_data_json = redis_client.get(redis_key)
                    
                    if pan_data_json:
                        try:
                            pan_data = json.loads(pan_data_json.decode('utf-8'))
                            
                            return ValidationUtils.create_validation_response(
                                valid=True,
                                field="pan_number",
                                message="PAN validated successfully",
                                data={
                                    "cleaned_value": pan_clean,
                                    "formatted_value": pan_clean,
                                    "database_status": "FOUND",
                                    "database_data": pan_data
                                }
                            )
                            
                        except json.JSONDecodeError:
                            return ValidationUtils.create_validation_response(
                                valid=False,
                                field="pan_number",
                                error="Database data format error",
                                error_code="DATABASE_FORMAT_ERROR"
                            )
                else:
                    return ValidationUtils.create_validation_response(
                        valid=False,
                        field="pan_number",
                        error="PAN number not found in database",
                        error_code="PAN_NOT_FOUND"
                    )
                    
            except Exception as e:
                return ValidationUtils.create_validation_response(
                    valid=False,
                    field="pan_number",
                    error=f"Database connection error: {str(e)}",
                    error_code="DATABASE_ERROR"
                )
        else:
            # No Redis client provided - basic validation only
            return ValidationUtils.create_validation_response(
                valid=True,
                field="pan_number",
                message="PAN format validation successful (database check skipped)",
                data={
                    "cleaned_value": pan_clean,
                    "formatted_value": pan_clean,
                    "database_status": "NOT_CHECKED"
                }
            )
    
    @staticmethod
    def cross_validate_aadhaar_pan(aadhaar_result: Dict, pan_result: Dict) -> Dict:
        """
        Cross-validate Aadhaar and PAN for consistency
        
        Args:
            aadhaar_result (Dict): Result from Aadhaar validation
            pan_result (Dict): Result from PAN validation
            
        Returns:
            Dict: Cross-validation result
        """
        
        if not aadhaar_result.get("valid") or not pan_result.get("valid"):
            return ValidationUtils.create_validation_response(
                valid=False,
                field="cross_validation",
                error="Both Aadhaar and PAN must be individually valid for cross-validation",
                error_code="PREREQUISITE_VALIDATION_FAILED"
            )
        
        # Extract database data if available
        aadhaar_data = aadhaar_result.get("database_data", {})
        pan_data = pan_result.get("database_data", {})
        
        consistency_checks = {
            "name_match": False,
            "dob_match": False,
            "both_active": False
        }
        
        issues = []
        
        # Check name consistency (if both have database data)
        if aadhaar_data and pan_data:
            aadhaar_name = aadhaar_data.get("name", "").lower().strip()
            pan_name = pan_data.get("name", "").lower().strip()
            
            if aadhaar_name and pan_name:
                # Simple name matching (can be enhanced with fuzzy matching)
                consistency_checks["name_match"] = aadhaar_name == pan_name
                if not consistency_checks["name_match"]:
                    issues.append("Name mismatch between Aadhaar and PAN")
            
            # Check DOB consistency
            aadhaar_dob = aadhaar_data.get("dob", "")
            pan_dob = pan_data.get("dob", "")
            
            if aadhaar_dob and pan_dob:
                consistency_checks["dob_match"] = aadhaar_dob == pan_dob
                if not consistency_checks["dob_match"]:
                    issues.append("Date of birth mismatch between Aadhaar and PAN")
            
            # Check if both are active
            aadhaar_status = aadhaar_data.get("status", "").upper()
            pan_status = pan_data.get("status", "").upper()
            
            consistency_checks["both_active"] = aadhaar_status == "ACTIVE" and pan_status == "ACTIVE"
            if not consistency_checks["both_active"]:
                issues.append("One or both documents are not in active status")
        
        # Overall cross-validation result
        overall_valid = len(issues) == 0
        
        return ValidationUtils.create_validation_response(
            valid=overall_valid,
            field="cross_validation",
            message="Cross-validation completed" if overall_valid else f"Cross-validation issues: {'; '.join(issues)}",
            data={
                "consistency_checks": consistency_checks,
                "issues": issues,
                "aadhaar_valid": aadhaar_result["valid"],
                "pan_valid": pan_result["valid"],
                "database_cross_check": bool(aadhaar_data and pan_data)
            }
        )

# Test function for identity validators
def test_identity_validators():
    """Test identity validators with various cases"""
    
    print("🆔 Testing Identity Validators")
    print("=" * 40)
    
    # Create mock Redis client for testing
    from utils.common_utils import MockRedisClient
    mock_redis = MockRedisClient()
    
    print("\n1️⃣ Testing Aadhaar Validation")
    print("-" * 30)
    
    aadhaar_test_cases = [
        # Valid cases (exist in mock database)
        ("234567890124", True),   # Valid + exists in DB
        ("345678901235", True),   # Valid + exists in DB
        
        # Invalid cases
        ("", False),              # Empty
        ("12345678901", False),   # Too short
        ("111111111111", False),  # All same digits
        ("123456789012", False),  # Sequential pattern
        ("999999999999", False),  # Not in database
    ]
    
    for aadhaar, expected_valid in aadhaar_test_cases:
        result = IdentityValidators.validate_aadhaar(aadhaar, mock_redis)
        status = "✅ PASS" if result['valid'] == expected_valid else "❌ FAIL"
        print(f"{status} | Aadhaar: '{aadhaar}' -> Valid: {result['valid']}")
        if not result['valid']:
            print(f"     Error: {result['error']}")
        elif result['valid'] and result.get('database_data'):
            print(f"     Data: {result['database_data']['name']}")
    
    print("\n2️⃣ Testing PAN Validation")
    print("-" * 30)
    
    pan_test_cases = [
        # Valid cases (exist in mock database)
        ("ABCDE1234F", True),     # Valid + exists in DB
        ("fghij5678k", True),     # Valid (will be uppercase) + exists in DB
        
        # Invalid cases
        ("", False),              # Empty
        ("ABCDE123F", False),     # Too short
        ("12345ABCDF", False),    # Wrong pattern
        ("AAAAA0000A", False),    # Dummy pattern
        ("ZZZZZ9999Z", False),    # Not in database
    ]
    
    for pan, expected_valid in pan_test_cases:
        result = IdentityValidators.validate_pan(pan, mock_redis)
        status = "✅ PASS" if result['valid'] == expected_valid else "❌ FAIL"
        print(f"{status} | PAN: '{pan}' -> Valid: {result['valid']}")
        if not result['valid']:
            print(f"     Error: {result['error']}")
        elif result['valid'] and result.get('database_data'):
            print(f"     Data: {result['database_data']['name']}")
    
    print("\n3️⃣ Testing Cross-Validation")
    print("-" * 30)
    
    # Test cross-validation
    valid_aadhaar = IdentityValidators.validate_aadhaar("234567890124", mock_redis)
    valid_pan = IdentityValidators.validate_pan("ABCDE1234F", mock_redis)
    
    cross_result = IdentityValidators.cross_validate_aadhaar_pan(valid_aadhaar, valid_pan)
    print(f"✅ Cross-validation: {cross_result['valid']} - {cross_result['message']}")
    
    if cross_result.get('data'):
        checks = cross_result['data']['consistency_checks']
        print(f"     Name match: {checks['name_match']}")
        print(f"     DOB match: {checks['dob_match']}")
        print(f"     Both active: {checks['both_active']}")
    
    print("\n4️⃣ Testing Without Redis Client")
    print("-" * 30)
    
    # Test without Redis client (format validation only)
    result_aadhaar = IdentityValidators.validate_aadhaar("234567890124")
    result_pan = IdentityValidators.validate_pan("ABCDE1234F")
    
    print(f"✅ Aadhaar without Redis: {result_aadhaar['valid']} - {result_aadhaar['message']}")
    print(f"✅ PAN without Redis: {result_pan['valid']} - {result_pan['message']}")
    
    print("\n" + "=" * 40)
    print("🎉 Identity validation testing completed!")

if __name__ == "__main__":
    test_identity_validators()
