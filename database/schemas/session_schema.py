from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

class SessionSchema(BaseModel):
    """Session data structure for user sessions"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = Field(None, description="Associated user ID")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    current_step: str = Field(default="welcome", description="Current KYC step")
    session_data: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    last_activity: Optional[datetime] = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(default=None)
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(hours=24)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
    
    def extend_session(self, hours: int = 1):
        """Extend session expiry time"""
        self.expires_at = datetime.now() + timedelta(hours=hours)
        self.update_activity()
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage"""
        data = self.dict()
        datetime_fields = ['created_at', 'last_activity', 'expires_at']
        for field in datetime_fields:
            if data.get(field):
                data[field] = data[field].isoformat()
        return data
