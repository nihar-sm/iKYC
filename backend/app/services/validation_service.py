import re
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    field: str
    is_valid: bool
    confidence: float
    error_message: str = ""
    suggestions: List[str] = None

class IndianKYCValidator:
    """Comprehensive validation for Indian KYC documents"""
    
    def __init__(self):
        # Verhoeff algorithm tables for Aadhaar validation
        self.verhoeff_d = [
            [0,1,2,3,4,5,6,7,8,9],
            [1,2,3,4,0,6,7,8,9,5],
            [2,3,4,0,1,7,8,9,5,6],
            [3,4,0,1,2,8,9,5,6,7],
            [4,0,1,2,3,9,5,6,7,8],
            [5,9,8,7,6,0,4,3,2,1],
            [6,5,9,8,7,1,0,4,3,2],
            [7,6,5,9,8,2,1,0,4,3],
            [8,7,6,5,9,3,2,1,0,4],
            [9,8,7,6,5,4,3,2,1,0]
        ]
        
        self.verhoeff_p = [
            [0,1,2,3,4,5,6,7,8,9],
            [1,5,7,6,2,8,3,0,9,4],
            [5,8,0,3,7,9,6,1,4,2],
            [8,9,1,6,0,4,3,5,2,7],
            [9,4,5,3,1,2,6,8,7,0],
            [4,2,8,6,5,7,3,9,0,1],
            [2,7,9,3,8,0,6,4,1,5],
            [7,0,4,6,9,1,3,2,5,8]
        ]
        
        self.verhoeff_inv = [0,4,3,2,1,5,6,7,8,9]
        
    def validate_all_fields(self, extracted_fields: Dict[str, Any], document_type: str = "aadhaar") -> Dict[str, ValidationResult]:
        """Validate all extracted fields"""
        
        results = {}
        
        # Validate Aadhaar number
        if 'aadhaar_number' in extracted_fields:
            results['aadhaar_number'] = self.validate_aadhaar(extracted_fields['aadhaar_number'])
        
        # Validate PAN number
        if 'pan_number' in extracted_fields:
            results['pan_number'] = self.validate_pan(extracted_fields['pan_number'])
        
        # Validate name
        if 'name' in extracted_fields:
            results['name'] = self.validate_name(extracted_fields['name'])
        
        # Validate date of birth
        if 'date_of_birth' in extracted_fields:
            results['date_of_birth'] = self.validate_date_of_birth(extracted_fields['date_of_birth'])
        
        # Validate address
        if 'address' in extracted_fields:
            results['address'] = self.validate_address(extracted_fields['address'])
        
        # Validate phone number
        if 'phone' in extracted_fields:
            results['phone'] = self.validate_phone(extracted_fields['phone'])
        
        return results
    
    def validate_aadhaar(self, aadhaar_number: str) -> ValidationResult:
        """Validate Aadhaar number using Verhoeff algorithm"""
        try:
            # Clean the number
            aadhaar_clean = re.sub(r'\D', '', str(aadhaar_number))
            
            # Check length
            if len(aadhaar_clean) != 12:
                return ValidationResult(
                    field="aadhaar_number",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Aadhaar number must be exactly 12 digits",
                    suggestions=["Check if all digits are captured correctly"]
                )
            
            # Check starting digit (cannot be 0 or 1)
            if aadhaar_clean[0] in ('0', '1'):
                return ValidationResult(
                    field="aadhaar_number",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Aadhaar number cannot start with 0 or 1",
                    suggestions=["Verify the first digit of the Aadhaar number"]
                )
            
            # Verhoeff checksum validation
            is_checksum_valid = self._verhoeff_validate(aadhaar_clean)
            
            if is_checksum_valid:
                return ValidationResult(
                    field="aadhaar_number",
                    is_valid=True,
                    confidence=0.95,
                    error_message=""
                )
            else:
                return ValidationResult(
                    field="aadhaar_number",
                    is_valid=False,
                    confidence=0.3,
                    error_message="Invalid Aadhaar checksum",
                    suggestions=["Verify all digits are correct", "Check for OCR misreading"]
                )
                
        except Exception as e:
            logger.error(f"Aadhaar validation error: {e}")
            return ValidationResult(
                field="aadhaar_number",
                is_valid=False,
                confidence=0.0,
                error_message=f"Validation error: {str(e)}"
            )
    
    def validate_pan(self, pan_number: str) -> ValidationResult:
        """Validate PAN number format and structure"""
        try:
            pan_clean = str(pan_number).strip().upper()
            
            # PAN pattern: 5 letters + 4 digits + 1 letter
            pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
            
            if not re.match(pan_pattern, pan_clean):
                return ValidationResult(
                    field="pan_number",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Invalid PAN format (should be ABCDE1234F)",
                    suggestions=["Check for correct letter-digit sequence", "Verify all characters are readable"]
                )
            
            # Additional PAN rules
            # 4th character indicates entity type
            entity_indicators = {
                'P': 'Individual',
                'C': 'Company', 
                'H': 'HUF',
                'F': 'Firm',
                'A': 'AOP',
                'T': 'Trust',
                'B': 'BOI',
                'L': 'Local Authority',
                'J': 'Artificial Judicial Person',
                'G': 'Government'
            }
            
            entity_type = entity_indicators.get(pan_clean[3], 'Unknown')
            
            return ValidationResult(
                field="pan_number",
                is_valid=True,
                confidence=0.95,
                error_message="",
                suggestions=[f"Entity type: {entity_type}"]
            )
            
        except Exception as e:
            logger.error(f"PAN validation error: {e}")
            return ValidationResult(
                field="pan_number",
                is_valid=False,
                confidence=0.0,
                error_message=f"Validation error: {str(e)}"
            )
    
    def validate_name(self, name: str) -> ValidationResult:
        """Validate person name"""
        try:
            name_clean = str(name).strip()
            
            # Check length
            if len(name_clean) < 2:
                return ValidationResult(
                    field="name",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Name too short",
                    suggestions=["Check if complete name is captured"]
                )
            
            if len(name_clean) > 100:
                return ValidationResult(
                    field="name",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Name too long",
                    suggestions=["Check for extra text captured with name"]
                )
            
            # Check for reasonable word count (1-5 words typical)
            words = name_clean.split()
            if len(words) > 6:
                return ValidationResult(
                    field="name",
                    is_valid=False,
                    confidence=0.4,
                    error_message="Too many words in name",
                    suggestions=["Check if address or other info mixed with name"]
                )
            
            # Check for valid characters (letters, spaces, common punctuation)
            if not re.match(r'^[A-Za-z\s\.\-\']+$', name_clean):
                return ValidationResult(
                    field="name",
                    is_valid=False,
                    confidence=0.2,
                    error_message="Invalid characters in name",
                    suggestions=["Remove numbers or special characters"]
                )
            
            return ValidationResult(
                field="name",
                is_valid=True,
                confidence=0.9,
                error_message=""
            )
            
        except Exception as e:
            return ValidationResult(
                field="name",
                is_valid=False,
                confidence=0.0,
                error_message=f"Validation error: {str(e)}"
            )
    
    def validate_date_of_birth(self, dob: str) -> ValidationResult:
        """Validate date of birth"""
        try:
            dob_str = str(dob).strip()
            
            # Try different date formats
            date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y']
            parsed_date = None
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(dob_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                return ValidationResult(
                    field="date_of_birth",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Invalid date format",
                    suggestions=["Supported formats: DD/MM/YYYY, DD-MM-YYYY"]
                )
            
            # Handle 2-digit years
            if parsed_date.year < 100:
                if parsed_date.year < 30:  # Assume 20xx
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                else:  # Assume 19xx
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
            
            # Validate date range
            current_year = datetime.now().year
            if parsed_date.year < 1900:
                return ValidationResult(
                    field="date_of_birth",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Date too old (before 1900)",
                    suggestions=["Check year is correct"]
                )
            
            if parsed_date.year > current_year:
                return ValidationResult(
                    field="date_of_birth",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Future date not allowed",
                    suggestions=["Check year is correct"]
                )
            
            # Check reasonable age (0-150 years)
            age = current_year - parsed_date.year
            if age > 150:
                return ValidationResult(
                    field="date_of_birth",
                    is_valid=False,
                    confidence=0.1,
                    error_message="Age too high (>150 years)",
                    suggestions=["Verify the year"]
                )
            
            return ValidationResult(
                field="date_of_birth",
                is_valid=True,
                confidence=0.95,
                error_message="",
                suggestions=[f"Calculated age: {age} years"]
            )
            
        except Exception as e:
            return ValidationResult(
                field="date_of_birth",
                is_valid=False,
                confidence=0.0,
                error_message=f"Validation error: {str(e)}"
            )
    
    def validate_address(self, address: str) -> ValidationResult:
        """Validate address format"""
        try:
            addr_clean = str(address).strip()
            
            if len(addr_clean) < 10:
                return ValidationResult(
                    field="address",
                    is_valid=False,
                    confidence=0.3,
                    error_message="Address too short",
                    suggestions=["Check if complete address is captured"]
                )
            
            # Look for Indian pincode
            pincode_match = re.search(r'\b\d{6}\b', addr_clean)
            has_pincode = bool(pincode_match)
            
            # Look for state names
            indian_states = [
                'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
                'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
                'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya',
                'mizoram', 'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim',
                'tamil nadu', 'telangana', 'tripura', 'uttar pradesh', 'uttarakhand',
                'west bengal', 'delhi'
            ]
            
            has_state = any(state in addr_clean.lower() for state in indian_states)
            
            confidence = 0.6
            if has_pincode:
                confidence += 0.2
            if has_state:
                confidence += 0.2
            
            suggestions = []
            if not has_pincode:
                suggestions.append("Pincode not found")
            if not has_state:
                suggestions.append("State name not clearly identified")
            
            return ValidationResult(
                field="address",
                is_valid=True,
                confidence=min(confidence, 0.95),
                error_message="",
                suggestions=suggestions
            )
            
        except Exception as e:
            return ValidationResult(
                field="address",
                is_valid=False,
                confidence=0.0,
                error_message=f"Validation error: {str(e)}"
            )
    
    def validate_phone(self, phone: str) -> ValidationResult:
        """Validate Indian phone number"""
        try:
            phone_clean = re.sub(r'\D', '', str(phone))
            
            # Indian mobile number: starts with 6,7,8,9 and has 10 digits
            if len(phone_clean) == 10 and phone_clean[0] in '6789':
                return ValidationResult(
                    field="phone",
                    is_valid=True,
                    confidence=0.95,
                    error_message=""
                )
            elif len(phone_clean) == 11 and phone_clean.startswith('0'):
                # Remove leading 0 and check again
                return self.validate_phone(phone_clean[1:])
            elif len(phone_clean) == 12 and phone_clean.startswith('91'):
                # Remove country code and check
                return self.validate_phone(phone_clean[2:])
            else:
                return ValidationResult(
                    field="phone",
                    is_valid=False,
                    confidence=0.0,
                    error_message="Invalid Indian mobile number format",
                    suggestions=["Should be 10 digits starting with 6,7,8,9"]
                )
                
        except Exception as e:
            return ValidationResult(
                field="phone",
                is_valid=False,
                confidence=0.0,
                error_message=f"Validation error: {str(e)}"
            )
    
    def _verhoeff_validate(self, number: str) -> bool:
        """Validate number using Verhoeff algorithm"""
        try:
            c = 0
            num_list = [int(x) for x in reversed(number)]
            
            for i, digit in enumerate(num_list):
                c = self.verhoeff_d[c][self.verhoeff_p[i % 8][digit]]
            
            return c == 0
            
        except Exception as e:
            logger.error(f"Verhoeff validation error: {e}")
            return False
    
    def get_validation_summary(self, validation_results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Get summary of validation results"""
        total_fields = len(validation_results)
        valid_fields = sum(1 for r in validation_results.values() if r.is_valid)
        avg_confidence = sum(r.confidence for r in validation_results.values()) / total_fields if total_fields > 0 else 0
        
        # Determine overall status
        if valid_fields == total_fields:
            overall_status = "VALID"
        elif valid_fields == 0:
            overall_status = "INVALID"
        else:
            overall_status = "PARTIAL"
        
        return {
            "overall_status": overall_status,
            "total_fields": total_fields,
            "valid_fields": valid_fields,
            "invalid_fields": total_fields - valid_fields,
            "average_confidence": round(avg_confidence, 2),
            "validation_score": round((valid_fields / total_fields) * 100, 1) if total_fields > 0 else 0
        }

# Global validator instance
kyc_validator = IndianKYCValidator()
