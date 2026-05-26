import logging
from pathlib import Path
from typing import Dict, Any, Optional
from services.ocr_service import ocr_service
from core.database import db

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.ocr = ocr_service
    
    def process_document(self, document_id: str, file_path: str, document_type: str) -> Dict[str, Any]:
        """Process uploaded document through OCR and validation"""
        try:
            logger.info(f"Processing document {document_id}")
            
            # Step 1: OCR Processing
            ocr_result = self.ocr.extract_text(file_path)
            if not ocr_result:
                raise Exception("OCR processing failed")
            
            # Step 2: Extract fields based on document type
            extracted_fields = self._extract_fields(ocr_result['text'], document_type)
            
            # Step 3: Store results
            processing_result = {
                "document_id": document_id,
                "status": "processed",
                "ocr_result": ocr_result,
                "extracted_fields": extracted_fields,
                "document_type": document_type
            }
            
            db.set_document_data(document_id, processing_result)
            
            logger.info(f"Document {document_id} processed successfully")
            return processing_result
            
        except Exception as e:
            logger.error(f"Document processing failed for {document_id}: {e}")
            error_result = {
                "document_id": document_id,
                "status": "failed",
                "error": str(e)
            }
            db.set_document_data(document_id, error_result)
            return error_result
    
    def _extract_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract specific fields based on document type"""
        import re
        
        fields = {}
        
        if document_type == "aadhaar":
            # Extract Aadhaar number (12 digits)
            aadhaar_match = re.search(r'\b\d{4}\s*\d{4}\s*\d{4}\b', text)
            if aadhaar_match:
                fields['aadhaar_number'] = re.sub(r'\s', '', aadhaar_match.group())
            
            # Extract name (usually after "Name:" or before "DOB:")
            name_patterns = [
                r'Name[:\s]+([A-Za-z\s]+)',
                r'([A-Za-z\s]+)\s+DOB',
                r'([A-Za-z\s]+)\s+\d{2}[/-]\d{2}[/-]\d{4}'
            ]
            for pattern in name_patterns:
                name_match = re.search(pattern, text)
                if name_match:
                    fields['name'] = name_match.group(1).strip()
                    break
            
            # Extract DOB
            dob_match = re.search(r'DOB[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})', text)
            if dob_match:
                fields['date_of_birth'] = dob_match.group(1)
        
        elif document_type == "pan":
            # Extract PAN number
            pan_match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', text)
            if pan_match:
                fields['pan_number'] = pan_match.group()
            
            # Extract name
            name_match = re.search(r'([A-Za-z\s]+)\s+[A-Z]{5}[0-9]{4}[A-Z]{1}', text)
            if name_match:
                fields['name'] = name_match.group(1).strip()
        
        return fields

document_processor = DocumentProcessor()
