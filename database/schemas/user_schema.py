from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class UserSchema(BaseModel):
    """User data structure for KYC system"""
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., description="User email address")
    phone_number: str = Field(..., description="10-digit mobile number")
    kyc_status: str = Field(default="pending", description="pending/in_progress/verified/rejected")
    documents_submitted: List[str] = Field(default_factory=list, description="List of submitted documents")
    verification_steps_completed: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    @validator('email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        cleaned = re.sub(r'[-\s+]', '', v)
        if not re.match(r'^[6-9]\d{9}$', cleaned):
            raise ValueError('Phone number must be a valid 10-digit Indian mobile number')
        return cleaned
    
    @validator('kyc_status')
    def validate_kyc_status(cls, v):
        valid_statuses = ['pending', 'in_progress', 'verified', 'rejected']
        if v not in valid_statuses:
            raise ValueError(f'KYC status must be one of: {valid_statuses}')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
    
    def add_document(self, document_type: str):
        """Add a document to submitted documents list"""
        if document_type not in self.documents_submitted:
            self.documents_submitted.append(document_type)
            self.update_timestamp()
    
    def complete_verification_step(self, step: str):
        """Mark a verification step as completed"""
        if step not in self.verification_steps_completed:
            self.verification_steps_completed.append(step)
            self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage"""
        data = self.dict()
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        if data.get('updated_at'):
            data['updated_at'] = data['updated_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserSchema':
        """Create instance from dictionary"""
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at') and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
