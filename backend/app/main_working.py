from fastapi import FastAPI, HTTPException, UploadFile, File, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import uuid
import logging
import os
import json
from datetime import datetime
from pathlib import Path

# Import enhanced face liveness service
from services.face_liveness_service_real import face_liveness_service

# Import your existing services
from services.ocr_service_real import initialize_ocr_service, get_ocr_service
from services.field_extraction import field_extractor
from services.validation_service import kyc_validator
from services.fraud_detection_service import fraud_detector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced configuration
class Settings:
    app_name = "IntelliKYC"
    environment = "development"
    upload_dir = "uploads"
    max_file_size_mb = 10
    ocr_space_api_key = "K87844805588957"
    use_easyocr = True

settings = Settings()

# Enhanced Pydantic Models
class ValidationRequest(BaseModel):
    fields: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "fields": {
                    "aadhaar_number": "180012001301",
                    "date_of_birth": "09/12/1989",
                    "name": "Surprit Kaur"
                }
            }
        }

class FaceLivenessRequest(BaseModel):
    video_frames: List[str]  # Base64 encoded frames
    
class HandGestureLivenessRequest(BaseModel):
    frames: List[str]
    timestamps: Optional[List[float]] = None
    frame_count: int
    original_fps: int = 30
    challenge_type: str = "hand_gestures"

class CombinedLivenessRequest(BaseModel):
    face_frames: List[str]
    hand_gesture_data: Dict[str, Any]

class KYCDecisionRequest(BaseModel):
    liveness_result: Dict[str, Any]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting IntelliKYC API with Enhanced Face Liveness System...")
    
    # Create upload directory
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Upload directory: {upload_path}")
    
    # Initialize OCR service
    try:
        initialize_ocr_service(
            ocr_space_api_key=settings.ocr_space_api_key,
            use_easyocr=settings.use_easyocr
        )
        logger.info("✅ Real OCR service initialized successfully")
    except Exception as e:
        logger.error(f"❌ OCR service initialization failed: {e}")
    
    # Initialize enhanced face liveness service
    try:
        # Test the face liveness service
        face_liveness_service.initiate_liveness_check()
        logger.info("✅ Enhanced Face Liveness service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Face Liveness service initialization failed: {e}")
    
    # Test Redis (optional)
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available: {e}")
    
    logger.info("🎉 IntelliKYC API ready with Enhanced Face Liveness Pipeline!")
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="3.0.0",
    description="AI-Powered KYC Verification System with Enhanced Face Liveness, Hand Gestures, and Combined Verification",
    lifespan=lifespan
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handler for better debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"Validation failed for body: {body.decode('utf-8')}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "received_body": body.decode('utf-8')}
    )

@app.get("/")
async def root():
    return {
        "message": f"🎉 {settings.app_name} API is running with Enhanced Liveness Pipeline",
        "version": "3.0.0",
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/api/health",
        "features": "OCR + Validation + AI Fraud Detection + Enhanced Face Liveness + Hand Gestures",
        "ai_services": "IBM Granite + AWS Bedrock Nova + MediaPipe + Face Validators",
        "liveness_modes": ["Face Validation", "Hand Gestures", "Combined Verification"]
    }

@app.get("/api/health")
async def health_check():
    """Enhanced health check with proper capability testing"""
    # Test OCR service
    ocr_status = "not_initialized"
    try:
        ocr_service = get_ocr_service()
        ocr_status = f"ready ({len(ocr_service.engines)} engines)"
    except Exception as e:
        ocr_status = f"error: {str(e)}"

    # Test fraud detection service  
    fraud_status = "initialized"
    try:
        fraud_detector.thresholds
        fraud_status = "ready"
    except Exception as e:
        fraud_status = f"error: {str(e)}"

    # Test enhanced liveness detection service with detailed capability checking
    liveness_status = "initialized"
    face_validation_available = False
    hand_gestures_available = False
    combined_mode_available = False
    
    try:
        # Test face liveness capability
        face_test = face_liveness_service.initiate_liveness_check()
        face_validation_available = face_test.get("valid", False)
        
        # Test hand gesture capability with proper test data
        test_video_data = {
            "frames": ["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="],  # 1x1 pixel base64
            "challenge_type": "standard"
        }
        
        hand_test = face_liveness_service.process_hand_gesture_sequence(test_video_data)
        # Check if method executed without critical errors
        hand_gestures_available = (
            "error" not in hand_test or 
            "not available" not in str(hand_test.get("error", "")).lower()
        )
        
        # Combined mode requires both face and hand gestures to work
        combined_mode_available = face_validation_available and hand_gestures_available
        
        # Set overall status based on available capabilities
        if combined_mode_available:
            liveness_status = "ready (face + hand gestures)"
        elif face_validation_available:
            liveness_status = "ready (face validation only)"
        elif hand_gestures_available:
            liveness_status = "ready (hand gestures only)"
        else:
            liveness_status = "limited functionality"
            
    except Exception as e:
        logger.error(f"Liveness service test failed: {e}")
        liveness_status = f"error: {str(e)}"
        face_validation_available = False
        hand_gestures_available = False
        combined_mode_available = False

    return {
        "status": "healthy",
        "service": f"{settings.app_name} API",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "ocr_service": ocr_status,
        "fraud_detection": fraud_status,
        "liveness_detection": liveness_status,
        "enhanced_features": {
            "face_validation": face_validation_available,
            "hand_gestures": hand_gestures_available,
            "combined_verification": combined_mode_available
        }
    }


# EXISTING ENDPOINTS (Document Upload & Processing)
@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "aadhaar"
):
    """Upload document for KYC processing"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Enhanced file validation
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        content = await file.read()
        if len(content) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
            )
        
        # Save file
        document_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{document_id}.{file_extension}"
        upload_dir = Path(settings.upload_dir)
        file_path = upload_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"📄 Document uploaded: {document_id} ({len(content)} bytes)")
        
        return {
            "document_id": document_id,
            "filename": filename,
            "document_type": document_type,
            "status": "uploaded",
            "file_size": len(content),
            "message": "Document uploaded successfully",
            "next_step": f"POST /api/v1/documents/{document_id}/process"
        }
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/documents/{document_id}/process")
async def process_document(document_id: str):
    """Process uploaded document with Real OCR, field extraction, validation, and AI fraud detection"""
    try:
        # Find document file
        upload_dir = Path(settings.upload_dir)
        document_files = list(upload_dir.glob(f"{document_id}.*"))
        if not document_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = str(document_files[0])
        
        # Get OCR service
        try:
            ocr_service = get_ocr_service()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OCR service not available: {e}")
        
        # Process with Real OCR
        logger.info(f"🔍 Processing document {document_id} with real OCR")
        ocr_result = ocr_service.extract_text(file_path)
        
        if not ocr_result:
            raise HTTPException(status_code=500, detail="OCR processing failed - no text extracted")
        
        # Extract fields with enhanced extraction
        document_type = "aadhaar"
        extracted_fields = field_extractor.extract_fields(
            text=ocr_result['text'],
            document_type=document_type
        )
        
        # Validate extracted fields
        logger.info(f"🔍 Validating extracted fields for {document_id}")
        validation_results = kyc_validator.validate_all_fields(extracted_fields, document_type)
        validation_summary = kyc_validator.get_validation_summary(validation_results)
        
        # Convert ValidationResult objects to dictionaries for JSON response
        validation_dict = {}
        for field, result in validation_results.items():
            validation_dict[field] = {
                "is_valid": result.is_valid,
                "confidence": result.confidence,
                "error_message": result.error_message,
                "suggestions": result.suggestions or []
            }
        
        # AI-Powered Fraud Detection
        logger.info(f"🤖 Running AI fraud detection for {document_id}")
        fraud_analysis = fraud_detector.analyze_document_fraud(
            document_text=ocr_result['text'],
            image_path=file_path,
            document_type=document_type
        )
        
        # Enhanced response with fraud detection
        response = {
            "document_id": document_id,
            "status": "processed_validated_and_analyzed",
            "ocr_result": {
                "text": ocr_result['text'],
                "confidence": ocr_result['confidence'],
                "engine": ocr_result['engine'],
                "processing_time": ocr_result.get('processing_time', 0),
                "success": ocr_result['success']
            },
            "extracted_fields": extracted_fields,
            "field_count": len(extracted_fields),
            "validation_results": validation_dict,
            "validation_summary": validation_summary,
            "fraud_analysis": fraud_analysis,
            "processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Document {document_id} processed with AI fraud detection")
        logger.info(f"🛡️ Fraud Risk: {fraud_analysis['overall_risk_level']} "
                   f"(Score: {fraud_analysis['combined_risk_score']:.2f})")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ENHANCED LIVENESS ENDPOINTS

@app.post("/api/v1/liveness/face/initiate")
async def initiate_face_liveness():
    """Initiate face liveness verification session"""
    try:
        logger.info("🎯 Initiating face liveness verification session")
        result = face_liveness_service.initiate_liveness_check()
        
        logger.info("✅ Face liveness session initiated successfully")
        return {
            "session_data": result,
            "initiated_at": datetime.now().isoformat(),
            "version": "enhanced-v3.0"
        }
    
    except Exception as e:
        logger.error(f"❌ Face liveness initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/liveness/face/analyze")
async def analyze_face_liveness(request: FaceLivenessRequest):
    """Analyze face liveness sequence (blink, smile, head movements)"""
    try:
        logger.info(f"🎯 Received face liveness analysis request with {len(request.video_frames)} frames")
        
        # Convert base64 frames to numpy arrays for processing
        import base64
        import numpy as np
        import cv2
        
        decoded_frames = []
        for frame_data in request.video_frames:
            try:
                frame_bytes = base64.b64decode(frame_data)
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                if frame is not None:
                    decoded_frames.append(frame)
            except Exception as e:
                logger.warning(f"Failed to decode frame: {e}")
                continue
        
        if len(decoded_frames) == 0:
            raise HTTPException(status_code=400, detail="No valid frames provided")
        
        result = face_liveness_service.process_liveness_sequence(decoded_frames)
        
        response = {
            "face_liveness_result": result,
            "analyzed_at": datetime.now().isoformat(),
            "verification_type": "face_validation",
            "version": "enhanced-v3.0"
        }
        
        logger.info(f"✅ Face liveness analysis completed: {'PASSED' if result.get('valid', False) else 'FAILED'}")
        return response
    
    except Exception as e:
        logger.error(f"❌ Face liveness analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/liveness/analyze")
async def analyze_hand_gesture_liveness(request: HandGestureLivenessRequest):
    """Analyze hand gesture liveness (existing functionality enhanced)"""
    try:
        logger.info(f"🎯 Received hand gesture liveness analysis request with {len(request.frames)} frames")
        
        # Convert request to dict format expected by existing service
        video_data = {
            "frames": request.frames,
            "timestamps": request.timestamps or [],
            "frame_count": request.frame_count,
            "original_fps": request.original_fps,
            "challenge_type": request.challenge_type
        }
        
        result = face_liveness_service.process_hand_gesture_sequence(video_data)
        
        response = {
            "liveness_result": {
                "is_live": result.get("valid", False),
                "confidence": result.get("overall_confidence", 0.0),
                "liveness_score": result.get("liveness_score", 0.0),
                "challenges_passed": result.get("challenges_passed", 0),
                "total_challenges": result.get("total_challenges", 2),
                "analysis_time": result.get("analysis_time", 0.0),
                "indicators": result.get("indicators", [])
            },
            "analyzed_at": datetime.now().isoformat(),
            "challenge_type": "hand_gestures",
            "version": "enhanced-v3.0"
        }
        
        logger.info(f"✅ Hand gesture liveness analysis completed: {'PASSED' if result.get('valid', False) else 'FAILED'}")
        return response
    
    except Exception as e:
        logger.error(f"❌ Hand gesture liveness analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/liveness/combined/analyze")
async def analyze_combined_liveness(request: CombinedLivenessRequest):
    """Analyze combined face + hand gesture liveness"""
    try:
        logger.info(f"🎯 Received combined liveness analysis request")
        
        # Convert base64 frames to numpy arrays for face processing
        import base64
        import numpy as np
        import cv2
        
        decoded_face_frames = []
        for frame_data in request.face_frames:
            try:
                frame_bytes = base64.b64decode(frame_data)
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                if frame is not None:
                    decoded_face_frames.append(frame)
            except Exception as e:
                continue
        
        result = face_liveness_service.process_combined_liveness(
            decoded_face_frames, 
            request.hand_gesture_data
        )
        
        response = {
            "combined_liveness_result": result,
            "analyzed_at": datetime.now().isoformat(),
            "verification_type": "combined_liveness",
            "version": "enhanced-v3.0"
        }
        
        logger.info(f"✅ Combined liveness analysis completed: {'PASSED' if result.get('valid', False) else 'FAILED'}")
        return response
    
    except Exception as e:
        logger.error(f"❌ Combined liveness analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/kyc/validate-decision")
async def validate_kyc_decision(request: KYCDecisionRequest):
    """Make KYC decision based on liveness results"""
    try:
        logger.info("🎯 Processing KYC decision validation")
        
        result = face_liveness_service.validate_kyc_decision(request.liveness_result)
        
        response = {
            "kyc_decision": result,
            "decided_at": datetime.now().isoformat(),
            "version": "enhanced-v3.0"
        }
        
        logger.info(f"✅ KYC decision made: {result.get('kyc_status', 'Unknown')}")
        return response
    
    except Exception as e:
        logger.error(f"❌ KYC decision failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/liveness/status")
async def get_liveness_service_status():
    """Get enhanced liveness detection service status"""
    try:
        # Test face liveness service
        face_test = face_liveness_service.initiate_liveness_check()
        face_available = face_test.get("valid", False)
        
        # Test hand gesture service
        hand_available = hasattr(face_liveness_service, 'hand_detector')
        
        status_info = {
            "status": "operational",
            "services_available": {
                "face_validation": face_available,
                "hand_gestures": hand_available,
                "combined_verification": face_available and hand_available
            },
            "verification_modes": [
                "Face Validation (blink, smile, head movements)",
                "Hand Gesture Detection (timed raises)",
                "Combined Verification (face + hand)"
            ],
            "total_services": sum([face_available, hand_available])
        }
        
        return status_info
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "services_available": {
                "face_validation": False,
                "hand_gestures": False,
                "combined_verification": False
            }
        }

# ENHANCED DOCUMENT PROCESSING WITH LIVENESS
@app.post("/api/v1/documents/{document_id}/process-with-liveness")
async def process_document_with_enhanced_liveness(
    document_id: str,
    liveness_video: Optional[str] = None,
    face_liveness_result: Optional[Dict[str, Any]] = None
):
    """Complete KYC processing including enhanced liveness verification"""
    try:
        # Run existing document processing
        doc_result = await process_document(document_id)
        
        # Add liveness verification if data provided
        liveness_result = None
        if face_liveness_result:
            # Use face liveness result
            liveness_result = face_liveness_result
        elif liveness_video:
            # Process hand gesture video
            hand_analysis = await analyze_hand_gesture_liveness({"frames": [liveness_video]})
            liveness_result = hand_analysis["liveness_result"]
        
        # Enhanced response with liveness
        enhanced_response = doc_result.copy()
        enhanced_response["liveness_verification"] = liveness_result
        enhanced_response["status"] = "processed_validated_analyzed_and_verified"
        
        # Enhanced KYC decision
        kyc_decision = _make_enhanced_kyc_decision(
            validation_summary=doc_result.get("validation_summary", {}),
            fraud_analysis=doc_result.get("fraud_analysis", {}),
            liveness_result=liveness_result
        )
        
        enhanced_response["kyc_decision"] = kyc_decision
        
        return enhanced_response
    
    except Exception as e:
        logger.error(f"Complete KYC processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _make_enhanced_kyc_decision(validation_summary: Dict, fraud_analysis: Dict, liveness_result: Optional[Dict]) -> Dict:
    """Enhanced KYC approval decision based on all factors including face liveness"""
    
    # Collect scores
    validation_score = validation_summary.get("validation_score", 0) / 100.0
    fraud_risk_score = 1.0 - fraud_analysis.get("combined_risk_score", 0)  # Invert risk to confidence
    
    # Handle different liveness result formats
    liveness_score = 1.0
    verification_type = "none"
    
    if liveness_result:
        if "overall_confidence" in liveness_result:  # Face liveness
            liveness_score = liveness_result.get("overall_confidence", 0.0)
            verification_type = "face_validation"
        elif "confidence" in liveness_result:  # Hand gesture liveness
            liveness_score = liveness_result.get("confidence", 0.0)
            verification_type = "hand_gestures"
        elif "combined_score" in liveness_result:  # Combined liveness
            liveness_score = liveness_result.get("combined_score", 0.0)
            verification_type = "combined"
    
    # Enhanced weighted final score based on verification type
    if verification_type == "combined":
        final_score = (validation_score * 0.3 + fraud_risk_score * 0.3 + liveness_score * 0.4)
    elif verification_type == "face_validation":
        final_score = (validation_score * 0.35 + fraud_risk_score * 0.35 + liveness_score * 0.3)
    else:  # hand_gestures or none
        final_score = (validation_score * 0.4 + fraud_risk_score * 0.4 + liveness_score * 0.2)
    
    # Enhanced decision logic
    if final_score >= 0.85:
        decision = "APPROVED"
        message = "Enhanced KYC verification successful - user approved"
        risk_level = "LOW"
    elif final_score >= 0.7:
        decision = "CONDITIONALLY_APPROVED"
        message = "KYC approved with conditions - enhanced monitoring recommended"
        risk_level = "LOW_MEDIUM"
    elif final_score >= 0.6:
        decision = "MANUAL_REVIEW"
        message = "Requires manual review before approval"
        risk_level = "MEDIUM"
    else:
        decision = "REJECTED"
        message = "KYC verification failed - user rejected"
        risk_level = "HIGH"
    
    return {
        "decision": decision,
        "final_score": round(final_score, 3),
        "risk_level": risk_level,
        "message": message,
        "verification_type": verification_type,
        "components": {
            "document_validation": validation_score,
            "fraud_detection": fraud_risk_score,
            "liveness_verification": liveness_score
        },
        "decided_at": datetime.now().isoformat()
    }

# EXISTING UTILITY ENDPOINTS
@app.post("/api/v1/validation/validate-fields")
async def validate_fields_directly(request: ValidationRequest):
    """Directly validate extracted fields without document processing"""
    try:
        logger.info(f"🔍 Validating fields: {list(request.fields.keys())}")
        
        validation_results = kyc_validator.validate_all_fields(request.fields)
        validation_summary = kyc_validator.get_validation_summary(validation_results)
        
        # Convert to dict for JSON response
        validation_dict = {}
        for field, result in validation_results.items():
            validation_dict[field] = {
                "is_valid": result.is_valid,
                "confidence": result.confidence,
                "error_message": result.error_message,
                "suggestions": result.suggestions or []
            }
        
        return {
            "validation_results": validation_dict,
            "validation_summary": validation_summary,
            "validated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/fraud/analyze")
async def analyze_fraud_directly(
    text: str,
    image_path: str,
    document_type: str = "aadhaar"
):
    """Direct fraud analysis endpoint"""
    try:
        fraud_analysis = fraud_detector.analyze_document_fraud(text, image_path, document_type)
        return {
            "fraud_analysis": fraud_analysis,
            "analyzed_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Fraud analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/fraud/status")
async def get_fraud_detection_status():
    """Get fraud detection service status and configuration"""
    try:
        status_info = {
            "status": "operational",
            "services_available": {
                "ibm_granite": fraud_detector.granite.enabled,
                "aws_bedrock": fraud_detector.bedrock.enabled
            },
            "thresholds": fraud_detector.thresholds,
            "total_services": sum([
                fraud_detector.granite.enabled,
                fraud_detector.bedrock.enabled
            ])
        }
        return status_info
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "services_available": {
                "ibm_granite": False,
                "aws_bedrock": False
            }
        }

@app.get("/api/v1/ocr/status")
async def get_ocr_status():
    """Get OCR service status and available engines"""
    try:
        ocr_service = get_ocr_service()
        engine_info = []
        for engine in ocr_service.engines:
            engine_info.append({
                "name": engine.__class__.__name__,
                "type": engine.__class__.__name__.replace("Engine", "").replace("OCR", "")
            })
        
        return {
            "status": "operational",
            "total_engines": len(ocr_service.engines),
            "engines": engine_info,
            "fallback_available": True
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "engines": []
        }

@app.post("/api/v1/debug/json")
async def debug_json_input(request: Request):
    """Debug endpoint to see exactly what JSON is received"""
    try:
        body = await request.body()
        json_data = await request.json()
        
        logger.info(f"Raw body: {body.decode('utf-8')}")
        logger.info(f"Parsed JSON: {json_data}")
        
        return {
            "success": True,
            "raw_body": body.decode('utf-8'),
            "parsed_json": json_data,
            "json_type": type(json_data).__name__
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_working:app", host="0.0.0.0", port=8000, reload=True)
