from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class VerificationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    DOCUMENT_VERIFICATION = "document_verification"
    FACE_VERIFICATION = "face_verification"
    CONTACT_VERIFICATION = "contact_verification"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class KYCSession(BaseModel):
    session_id: str
    user_id: str
    status: VerificationStatus = VerificationStatus.PENDING
    current_step: str
    steps_completed: List[str] = []
    documents_uploaded: List[str] = []
    verification_results: Dict[str, Any] = {}
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

class PersonalInfo(BaseModel):
    name: str
    date_of_birth: str
    gender: Optional[str] = None
    address: Optional[str] = None
    phone: str
    email: Optional[str] = None

class KYCProfile(BaseModel):
    user_id: str
    personal_info: PersonalInfo
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    last_verification_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
