from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class AadhaarSchema(BaseModel):
    """Aadhaar data structure for KYC verification"""
    aadhaar_number: str = Field(..., description="12-digit Aadhaar number")
    name: str = Field(..., min_length=2, max_length=100)
    father_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: str = Field(..., description="Date in DD/MM/YYYY format")
    gender: str = Field(..., description="Male/Female/Other")
    address: str = Field(..., min_length=10, max_length=500)
    phone_number: Optional[str] = Field(None, description="10-digit mobile number")
    email: Optional[str] = Field(None, description="Email address")
    photo_path: Optional[str] = Field(None, description="Path to photo file")
    verification_status: str = Field(default="pending", description="pending/verified/rejected")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    @validator('aadhaar_number')
    def validate_aadhaar_number(cls, v):
        # Remove spaces and hyphens
        cleaned = re.sub(r'[-\s]', '', v)
        if not re.match(r'^\d{12}$', cleaned):
            raise ValueError('Aadhaar number must be 12 digits')
        return cleaned
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None:
            cleaned = re.sub(r'[-\s+]', '', v)
            if not re.match(r'^[6-9]\d{9}$', cleaned):
                raise ValueError('Phone number must be a valid 10-digit Indian mobile number')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v.lower() not in ['male', 'female', 'other']:
            raise ValueError('Gender must be Male, Female, or Other')
        return v.title()
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', v):
            raise ValueError('Date of birth must be in DD/MM/YYYY format')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage"""
        data = self.dict()
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AadhaarSchema':
        """Create instance from dictionary"""
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
