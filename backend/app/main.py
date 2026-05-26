from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Mock settings
class MockSettings:
    environment = "development"
    upload_dir = "uploads"
    redis_host = "localhost"
    redis_port = 6379
    redis_db = 0
    redis_password = None

settings = MockSettings()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting IntelliKYC API...")
    
    # Create upload directory
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory: {upload_path}")
    
    # Test Redis connection
    try:
        import redis
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        r.ping()
        logger.info("✅ Redis connection verified")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
    
    logger.info("🚀 IntelliKYC API started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down IntelliKYC API...")

# Initialize FastAPI app
app = FastAPI(
    title="IntelliKYC API",
    version="1.0.0",
    description="AI-Powered KYC Verification System",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "🎉 IntelliKYC API is running",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/api/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
async def health_check():
    try:
        redis_status = "not configured"
        try:
            import redis
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True
            )
            r.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "disconnected"
        
        return {
            "status": "healthy",
            "service": "IntelliKYC API",
            "timestamp": datetime.now().isoformat(),
            "redis": redis_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "aadhaar"
):
    """Upload and process identity document"""
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        content = await file.read()
        file_size = len(content)
        
        # Validate file size (10MB limit)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Max size: 10MB"
            )
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Allowed: JPEG, PNG, PDF"
            )
        
        # Save file
        document_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{document_id}.{file_extension}"
        
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"📄 Document uploaded: {document_id}")
        
        return {
            "document_id": document_id,
            "message": "Document uploaded successfully",
            "document_type": document_type,
            "file_size": file_size,
            "status": "uploaded",
            "filename": unique_filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/verification/start")
async def start_verification_session(user_id: str = None):
    """Start a new KYC verification session"""
    try:
        session_id = str(uuid.uuid4())
        user_id = user_id or str(uuid.uuid4())
        
        logger.info(f"🔄 Verification session started: {session_id}")
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "status": "started",
            "next_step": "document_upload",
            "message": "Verification session started successfully"
        }
        
    except Exception as e:
        logger.error(f"Session start failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# FIXED: Proper uvicorn configuration
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # ← Import string instead of app object
        host="0.0.0.0",
        port=8000,
        reload=True
    )
# Add these imports to your existing main.py
from services.document_service import document_processor

# Add this new endpoint after your existing upload endpoint
@app.post("/api/v1/documents/{document_id}/process")
async def process_document(document_id: str):
    """Process uploaded document with OCR and field extraction"""
    try:
        # Get document info from database
        doc_data = db.get_document_data(document_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Process the document
        result = document_processor.process_document(
            document_id=document_id,
            file_path=doc_data.get('file_path', ''),
            document_type=doc_data.get('document_type', 'aadhaar')
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Update your upload endpoint to store document metadata
@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "aadhaar"
):
    # ... existing upload code ...
    
    # After saving the file, store metadata in database
    doc_metadata = {
        "document_id": document_id,
        "file_path": str(file_path),
        "document_type": document_type,
        "status": "uploaded",
        "file_size": file_size,
        "original_filename": file.filename
    }
    db.set_document_data(document_id, doc_metadata)
    
    return {
        "document_id": document_id,
        "message": "Document uploaded successfully",
        "next_step": f"/api/v1/documents/{document_id}/process"
    }

# Add this import to your existing main.py
from services.ocr_service_minimal import ocr_service
from services.document_service import document_processor

# Add this endpoint after your upload endpoint
@app.post("/api/v1/documents/{document_id}/process")
async def process_document(document_id: str):
    """Process uploaded document with OCR and field extraction"""
    try:
        # Get document info (you'll need to implement document storage)
        # For now, reconstruct the file path
        upload_dir = Path("uploads")
        
        # Find the document file
        document_files = list(upload_dir.glob(f"{document_id}.*"))
        if not document_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = str(document_files[0])
        
        # Process with OCR
        if not ocr_service:
            raise HTTPException(status_code=500, detail="OCR service not initialized")
        
        ocr_result = ocr_service.extract_text(file_path)
        if not ocr_result:
            raise HTTPException(status_code=500, detail="OCR processing failed")
        
        # Extract fields based on document type (simple extraction)
        extracted_fields = extract_document_fields(ocr_result['text'], 'aadhaar')
        
        return {
            "document_id": document_id,
            "status": "processed",
            "ocr_result": ocr_result,
            "extracted_fields": extracted_fields
        }
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def extract_document_fields(text: str, document_type: str) -> dict:
    """Simple field extraction logic"""
    import re
    fields = {}
    
    if document_type == "aadhaar":
        # Extract Aadhaar number
        aadhaar_match = re.search(r'\b\d{4}\s*\d{4}\s*\d{4}\b', text)
        if aadhaar_match:
            fields['aadhaar_number'] = re.sub(r'\s', '', aadhaar_match.group())
        
        # Extract name (look for patterns before DOB or after "Name")
        name_patterns = [
            r'Name[:\s]+([A-Za-z\s]+?)(?:\n|DOB|Date)',
            r'([A-Za-z\s]{10,40})\s*(?:DOB|Date of Birth)'
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, text, re.IGNORECASE)
            if name_match:
                fields['name'] = name_match.group(1).strip()
                break
        
        # Extract DOB
        dob_patterns = [
            r'DOB[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Date of Birth[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        for pattern in dob_patterns:
            dob_match = re.search(pattern, text, re.IGNORECASE)
            if dob_match:
                fields['date_of_birth'] = dob_match.group(1)
                break
    
    return fields
