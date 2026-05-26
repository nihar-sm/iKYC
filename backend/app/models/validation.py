from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

class AadhaarValidation(BaseModel):
    number: str
    is_valid_format: bool
    is_valid_checksum: bool
    masked_number: str
    validation_errors: List[str] = []
    
    @validator('number')
    def validate_aadhaar_format(cls, v):
        # Remove spaces and hyphens
        clean_number = re.sub(r'[\s-]', '', v)
        if not re.match(r'^\d{12}$', clean_number):
            raise ValueError('Aadhaar number must be 12 digits')
        return clean_number

class PANValidation(BaseModel):
    number: str
    is_valid_format: bool
    entity_type: Optional[str] = None
    validation_errors: List[str] = []
    
    @validator('number')
    def validate_pan_format(cls, v):
        # PAN format: ABCDE1234F
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', v.upper()):
            raise ValueError('Invalid PAN format')
        return v.upper()

class PhoneValidation(BaseModel):
    number: str
    is_valid_format: bool
    country_code: str = "+91"
    formatted_number: str
    validation_errors: List[str] = []
    
    @validator('number')
    def validate_phone_format(cls, v):
        # Remove all non-digits
        clean_number = re.sub(r'\D', '', v)
        # Indian mobile number validation
        if not re.match(r'^[6-9]\d{9}$', clean_number[-10:]):
            raise ValueError('Invalid Indian mobile number')
        return clean_number

class AddressValidation(BaseModel):
    raw_address: str
    parsed_components: Dict[str, str]
    confidence_score: float
    validation_errors: List[str] = []

class FaceValidationResult(BaseModel):
    session_id: str
    liveness_score: float
    is_live: bool
    face_quality_score: float
    anti_spoofing_result: Dict[str, Any]
    verification_steps: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
