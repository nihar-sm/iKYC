import requests
import easyocr
import logging
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger(__name__)

class OCREngine:
    def process(self, image_path: str) -> Dict[str, Any]:
        raise NotImplementedError

class EasyOCREngine(OCREngine):
    def __init__(self):
        self.reader = easyocr.Reader(['en'])
    
    def process(self, image_path: str) -> Dict[str, Any]:
        try:
            results = self.reader.readtext(image_path)
            text = ' '.join([item[1] for item in results])
            confidence = sum([item[2] for item in results]) / len(results) if results else 0
            
            return {
                "text": text,
                "confidence": confidence,
                "engine": "EasyOCR",
                "raw_results": results
            }
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            raise

class OCRSpaceEngine(OCREngine):
    def process(self, image_path: str) -> Dict[str, Any]:
        try:
            with open(image_path, 'rb') as f:
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files={'file': f},
                    data={'apikey': settings.ocr_space_api_key}
                )
            
            result = response.json()
            if result.get('OCRExitCode') == 1:
                text = result['ParsedResults'][0]['ParsedText']
                return {
                    "text": text,
                    "confidence": 0.9,  # OCR.space doesn't provide confidence
                    "engine": "OCRSpace",
                    "raw_results": result
                }
            else:
                raise Exception(f"OCR.space error: {result.get('ErrorMessage')}")
                
        except Exception as e:
            logger.error(f"OCRSpace failed: {e}")
            raise

class OCROrchestrator:
    def __init__(self):
        self.engines = [
            EasyOCREngine(),
            OCRSpaceEngine()
        ]
    
    def extract_text(self, image_path: str) -> Optional[Dict[str, Any]]:
        for engine in self.engines:
            try:
                result = engine.process(image_path)
                if result['confidence'] > 0.5:  # Minimum confidence threshold
                    logger.info(f"OCR successful with {result['engine']}")
                    return result
            except Exception as e:
                logger.warning(f"OCR engine failed: {e}")
                continue
        
        logger.error("All OCR engines failed")
        return None

ocr_service = OCROrchestrator()
