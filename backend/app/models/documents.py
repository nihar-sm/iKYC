from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    AADHAAR = "aadhaar"
    PAN = "pan"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FAILED = "failed"

class DocumentUpload(BaseModel):
    document_id: Optional[str] = None
    user_id: str
    document_type: DocumentType
    file_path: str
    original_filename: str
    file_size: int
    status: DocumentStatus = DocumentStatus.UPLOADED
    uploaded_at: datetime = Field(default_factory=datetime.now)

class OCRResult(BaseModel):
    document_id: str
    extracted_text: str
    confidence: float
    fields: Dict[str, Any]
    engine_used: str
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.now)

class DocumentValidationResult(BaseModel):
    document_id: str
    is_valid: bool
    validation_score: float
    issues: List[str] = []
    validated_fields: Dict[str, Any]
    tamper_detection: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
