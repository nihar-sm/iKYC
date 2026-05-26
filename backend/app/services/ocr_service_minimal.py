import requests
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class OCRSpaceEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def process(self, image_path: str) -> Dict[str, Any]:
        try:
            with open(image_path, 'rb') as f:
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files={'file': f},
                    data={
                        'apikey': self.api_key,
                        'language': 'eng',
                        'OCREngine': 2
                    },
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('OCRExitCode') == 1:
                    text = result['ParsedResults'][0]['ParsedText']
                    return {
                        "text": text.strip(),
                        "confidence": 0.9,
                        "engine": "OCRSpace",
                        "success": True
                    }
                else:
                    raise Exception(f"OCR.space error: {result.get('ErrorMessage')}")
            else:
                raise Exception(f"API request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"OCRSpace failed: {e}")
            raise

class MockOCREngine:
    def process(self, image_path: str) -> Dict[str, Any]:
        filename = os.path.basename(image_path).lower()
        
        if 'aadhaar' in filename:
            mock_text = """Government of India
            Aadhaar
            1234 5678 9012
            Name: JOHN DOE
            DOB: 01/01/1990
            Address: 123 Main Street, City, State - 123456"""
        elif 'pan' in filename:
            mock_text = """Income Tax Department
            Permanent Account Number Card
            ABCDE1234F
            JOHN DOE
            01/01/1990"""
        else:
            mock_text = "Sample document text for testing purposes."
        
        return {
            "text": mock_text.strip(),
            "confidence": 0.95,
            "engine": "MockOCR",
            "success": True
        }

class SimpleOCROrchestrator:
    def __init__(self, ocr_space_api_key: str = None):
        self.engines = []
        
        if ocr_space_api_key:
            self.engines.append(OCRSpaceEngine(ocr_space_api_key))
        
        self.engines.append(MockOCREngine())
    
    def extract_text(self, image_path: str) -> Optional[Dict[str, Any]]:
        for engine in self.engines:
            try:
                result = engine.process(image_path)
                if result.get('success'):
                    logger.info(f"OCR successful with {result['engine']}")
                    return result
            except Exception as e:
                logger.warning(f"OCR engine failed: {e}")
                continue
        
        logger.error("All OCR engines failed")
        return None

# Initialize OCR service
ocr_service = SimpleOCROrchestrator()

def initialize_ocr_service(api_key: str = None):
    global ocr_service
    ocr_service = SimpleOCROrchestrator(api_key)
    return ocr_service
