"""
Simplified Free Multi-Engine OCR Processor for IntelliKYC
Uses EasyOCR + OCR.space (both free, no system dependencies!)
"""

import json
import base64
import requests
from typing import Dict, List, Optional
import sys
import os
import io
from PIL import Image

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ai_config import AIConfig
from utils.image_utils import ImageProcessor

class FreeMultiOCRProcessor:
    """Simplified free multi-engine OCR processor with fallback support"""

    def __init__(self):
        """Initialize available free OCR engines"""
        self.engines = {}
        self._initialize_engines()

    def _initialize_engines(self):
        """Initialize simplified free OCR engines"""
        
        # Initialize EasyOCR (Primary - Best accuracy, works offline)
        try:
            import easyocr
            self.engines['easyocr'] = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("✅ EasyOCR initialized successfully")
        except ImportError:
            print("⚠️ EasyOCR not available - install with: pip install easyocr")
        except Exception as e:
            print(f"⚠️ EasyOCR initialization failed: {e}")

        # Initialize OCR.space API (Secondary - Free API, 25k/month)
        if AIConfig.OCR_SPACE_API_KEY and AIConfig.OCR_SPACE_API_KEY != 'FREE_API_KEY':
            self.engines['ocr_space'] = True
            print("✅ OCR.space API initialized successfully")
        else:
            print("⚠️ OCR.space API key not configured")
            print("   Get free key at: https://ocr.space/ocrapi")

        # Mock engine always available (Fallback - Always works)
        self.engines['mock'] = True
        print("✅ Mock OCR engine available")

        print(f"📊 Total OCR engines available: {len(self.engines)}")

    def extract_text_from_document(self, image_data: bytes, document_type: str = 'aadhaar') -> Dict:
        """
        Extract text using simplified free OCR engines with fallback
        """
        print(f"🔍 Starting simplified multi-engine OCR for {document_type.upper()} document")

        # Preprocess image for better OCR
        preprocessing_result = ImageProcessor.preprocess_document_image(image_data)
        if not preprocessing_result['success']:
            return {
                'success': False,
                'error': 'Image preprocessing failed',
                'extracted_text': '',
                'confidence_score': 0.0
            }

        # Try engines in order of preference
        for engine_name in AIConfig.OCR_ENGINES:
            if engine_name in self.engines:
                print(f"📄 Trying {engine_name.upper()} OCR...")
                
                try:
                    if engine_name == 'easyocr':
                        result = self._extract_with_easyocr(
                            preprocessing_result['processed_image'], 
                            document_type
                        )
                    elif engine_name == 'ocr_space':
                        result = self._extract_with_ocr_space(
                            preprocessing_result['processed_image'], 
                            document_type
                        )
                    else:  # mock
                        result = self._extract_with_mock(
                            preprocessing_result['processed_image'], 
                            document_type
                        )

                    if result['success']:
                        result['image_quality'] = preprocessing_result['quality_metrics']
                        result['ocr_engine'] = engine_name.upper()
                        print(f"✅ {engine_name.upper()} OCR successful!")
                        return result
                    else:
                        print(f"❌ {engine_name.upper()} OCR failed: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    print(f"❌ {engine_name.upper()} OCR error: {str(e)}")

        # All engines failed
        return {
            'success': False,
            'error': 'All OCR engines failed',
            'extracted_text': '',
            'confidence_score': 0.0
        }

    def _extract_with_easyocr(self, image_data: bytes, document_type: str) -> Dict:
        """Extract text using EasyOCR (Primary engine - works offline)"""
        try:
            # Convert bytes to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            
            # EasyOCR expects PIL image or numpy array
            import numpy as np
            image_array = np.array(pil_image)
            
            # Perform OCR
            reader = self.engines['easyocr']
            results = reader.readtext(image_array, detail=1)
            
            # Process results
            if not results:
                return {
                    'success': False,
                    'error': 'EasyOCR found no text in image'
                }
            
            extracted_text = ' '.join([result[1] for result in results])
            confidence_scores = [result[2] for result in results]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # Extract fields
            field_extractions = self._extract_document_fields(extracted_text, document_type)
            
            return {
                'success': True,
                'extracted_text': extracted_text,
                'confidence_score': avg_confidence,
                'field_extractions': field_extractions
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"EasyOCR failed: {str(e)}"
            }

    def _extract_with_ocr_space(self, image_data: bytes, document_type: str) -> Dict:
        """Extract text using OCR.space free API (Secondary engine)"""
        try:
            # Encode image as base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare API request
            payload = {
                'apikey': AIConfig.OCR_SPACE_API_KEY,
                'base64Image': f'data:image/jpeg;base64,{encoded_image}',
                'language': 'eng',
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2  # Engine 2 is usually more accurate
            }
            
            # Make API request with timeout
            response = requests.post(AIConfig.OCR_SPACE_URL, data=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('IsErroredOnProcessing'):
                    return {
                        'success': False,
                        'error': f"OCR.space error: {result.get('ErrorMessage', 'Unknown error')}"
                    }
                
                # Extract text
                parsed_results = result.get('ParsedResults', [])
                if parsed_results:
                    extracted_text = parsed_results[0].get('ParsedText', '').strip()
                    
                    if not extracted_text:
                        return {
                            'success': False,
                            'error': 'OCR.space found no text in image'
                        }
                    
                    # OCR.space doesn't provide confidence, estimate based on text quality
                    confidence_score = min(0.9, max(0.5, len(extracted_text.strip()) / 100))
                    
                    # Extract fields
                    field_extractions = self._extract_document_fields(extracted_text, document_type)
                    
                    return {
                        'success': True,
                        'extracted_text': extracted_text,
                        'confidence_score': confidence_score,
                        'field_extractions': field_extractions
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No parsed results from OCR.space'
                    }
            else:
                return {
                    'success': False,
                    'error': f'OCR.space API error: HTTP {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'OCR.space API timeout (30s)'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'OCR.space API request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"OCR.space failed: {str(e)}"
            }

    def _extract_with_mock(self, image_data: bytes, document_type: str) -> Dict:
        """Mock OCR extraction (Fallback - always works for testing)"""
        extracted_text = self._get_mock_text(document_type)
        field_extractions = self._extract_document_fields(extracted_text, document_type)
        
        return {
            'success': True,
            'extracted_text': extracted_text,
            'confidence_score': 0.87,
            'field_extractions': field_extractions
        }

    def _get_mock_text(self, document_type: str) -> str:
        """Get realistic mock text based on document type"""
        if document_type == 'aadhaar':
            return '''Government of India
            Aadhaar
            2345 6789 0124
            Name: Rajesh Kumar
            DOB: 15/08/1985
            Male
            Address: 123 Main Street, Mumbai, Maharashtra 400001
            Issue Date: 15/01/2020'''
        else:  # PAN
            return '''Income Tax Department
            Government of India
            Permanent Account Number
            ABCDE1234F
            Name: Rajesh Kumar
            Father's Name: Suresh Kumar
            Date of Birth: 15/08/1985
            Signature'''

    def _extract_document_fields(self, text: str, document_type: str) -> Dict:
        """Extract specific fields based on document type"""
        import re
        fields = {}
        text_lower = text.lower()

        if document_type == 'aadhaar':
            # Extract Aadhaar number (12 digits with or without spaces)
            aadhaar_patterns = [
                r'\b(\d{4}\s?\d{4}\s?\d{4})\b',
                r'\b(\d{12})\b'
            ]
            for pattern in aadhaar_patterns:
                aadhaar_match = re.search(pattern, text)
                if aadhaar_match:
                    fields['aadhaar_number'] = aadhaar_match.group(1).replace(' ', '')
                    break

            # Extract name (after "name:")
            name_patterns = [
                r'name[:\s]+([a-zA-Z\s]+?)(?:\n|\s{2,}|dob|date)',
                r'name[:\s]+([a-zA-Z\s]+?)$'
            ]
            for pattern in name_patterns:
                name_match = re.search(pattern, text_lower)
                if name_match:
                    fields['name'] = name_match.group(1).strip().title()
                    break

            # Extract DOB patterns
            dob_patterns = [
                r'dob[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})',
                r'date\s+of\s+birth[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})',
                r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b'
            ]
            for pattern in dob_patterns:
                dob_match = re.search(pattern, text_lower)
                if dob_match:
                    fields['date_of_birth'] = dob_match.group(1)
                    break

            # Extract gender
            if 'male' in text_lower and 'female' not in text_lower:
                fields['gender'] = 'Male'
            elif 'female' in text_lower:
                fields['gender'] = 'Female'

        elif document_type == 'pan':
            # Extract PAN number (5 letters, 4 digits, 1 letter)
            pan_pattern = r'\b([A-Z]{5}\d{4}[A-Z])\b'
            pan_match = re.search(pan_pattern, text.upper())
            if pan_match:
                fields['pan_number'] = pan_match.group(1)

            # Extract name
            name_patterns = [
                r'name[:\s]+([a-zA-Z\s]+?)(?:\n|\s{2,}|father|dob|date)',
                r'name[:\s]+([a-zA-Z\s]+?)$'
            ]
            for pattern in name_patterns:
                name_match = re.search(pattern, text_lower)
                if name_match:
                    fields['name'] = name_match.group(1).strip().title()
                    break

            # Extract father's name
            father_patterns = [
                r'father[\'s]*\s*name[:\s]+([a-zA-Z\s]+?)(?:\n|\s{2,}|dob|date)',
                r'father[:\s]+([a-zA-Z\s]+?)(?:\n|\s{2,}|dob|date)'
            ]
            for pattern in father_patterns:
                father_match = re.search(pattern, text_lower)
                if father_match:
                    fields['father_name'] = father_match.group(1).strip().title()
                    break

            # Extract DOB
            dob_patterns = [
                r'dob[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})',
                r'date\s+of\s+birth[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})',
                r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b'
            ]
            for pattern in dob_patterns:
                dob_match = re.search(pattern, text_lower)
                if dob_match:
                    fields['date_of_birth'] = dob_match.group(1)
                    break

        return fields

    def get_available_engines(self) -> List[str]:
        """Get list of available OCR engines"""
        return list(self.engines.keys())

    def get_engine_status(self) -> Dict[str, bool]:
        """Get status of all OCR engines"""
        return {engine: True for engine in self.engines.keys()}

    def get_engine_info(self) -> Dict[str, Dict]:
        """Get detailed information about each engine"""
        info = {}
        
        if 'easyocr' in self.engines:
            info['easyocr'] = {
                'name': 'EasyOCR',
                'type': 'Offline',
                'cost': 'Free',
                'accuracy': 'High',
                'status': 'Available'
            }
        
        if 'ocr_space' in self.engines:
            info['ocr_space'] = {
                'name': 'OCR.space',
                'type': 'API',
                'cost': 'Free (25k/month)',
                'accuracy': 'Medium',
                'status': 'Available'
            }
        
        if 'mock' in self.engines:
            info['mock'] = {
                'name': 'Mock OCR',
                'type': 'Testing',
                'cost': 'Free',
                'accuracy': 'Mock Data',
                'status': 'Available'
            }
        
        return info
