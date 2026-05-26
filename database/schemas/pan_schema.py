from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class PANSchema(BaseModel):
    """PAN card data structure for KYC verification"""
    pan_number: str = Field(..., description="10-character PAN number")
    name: str = Field(..., min_length=2, max_length=100)
    father_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: str = Field(..., description="Date in DD/MM/YYYY format")
    verification_status: str = Field(default="pending", description="pending/verified/rejected")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    @validator('pan_number')
    def validate_pan_number(cls, v):
        cleaned = v.upper().replace(' ', '')
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', cleaned):
            raise ValueError('PAN number must be in format ABCDE1234F')
        return cleaned
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', v):
            raise ValueError('Date of birth must be in DD/MM/YYYY format')
        return v
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage"""
        data = self.dict()
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PANSchema':
        """Create instance from dictionary"""
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
