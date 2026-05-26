"""
Test IntelliKYC with Real Aadhaar Images
IMPORTANT: Use only test/sample documents or your own documents for testing
"""

import sys
import os
from pathlib import Path
import json
from typing import Dict

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from ai_orchestrator import AIDocumentProcessor
from ocr.free_multi_ocr import FreeMultiOCRProcessor
from config.ai_config import AIConfig

class RealImageTester:
    """Test with real Aadhaar images"""
    
    def __init__(self):
        self.ai_processor = AIDocumentProcessor()
        self.ocr_processor = FreeMultiOCRProcessor()
        
    def load_image_from_file(self, image_path: str) -> bytes:
        """Load image file and convert to bytes"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Validate file size
            file_size_mb = len(image_data) / (1024 * 1024)
            if file_size_mb > AIConfig.MAX_FILE_SIZE_MB:
                raise ValueError(f"File size {file_size_mb:.2f}MB exceeds limit of {AIConfig.MAX_FILE_SIZE_MB}MB")
                
            print(f"✅ Image loaded successfully: {file_size_mb:.2f}MB")
            return image_data
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Image file not found: {image_path}")
        except Exception as e:
            raise Exception(f"Failed to load image: {str(e)}")

    def test_ocr_only(self, image_path: str, document_type: str = 'aadhaar') -> Dict:
        """Test only OCR extraction without full AI pipeline"""
        print(f"\n🔍 Testing OCR-only extraction from: {Path(image_path).name}")
        print("=" * 60)
        
        # Load image
        image_data = self.load_image_from_file(image_path)
        
        # Run OCR
        result = self.ocr_processor.extract_text_from_document(image_data, document_type)
        
        # Display results
        if result['success']:
            print(f"✅ OCR Success!")
            print(f"🔧 Engine Used: {result.get('ocr_engine', 'Unknown')}")
            print(f"📊 Confidence: {result.get('confidence_score', 0.0):.3f}")
            print(f"\n📄 Extracted Text:")
            print("-" * 40)
            print(result.get('extracted_text', 'No text extracted'))
            print("-" * 40)
            
            # Show extracted fields
            fields = result.get('field_extractions', {})
            if fields:
                print(f"\n🏷️ Extracted Fields:")
                for field, value in fields.items():
                    print(f"  • {field}: {value}")
            else:
                print("\n⚠️ No structured fields extracted")
                
        else:
            print(f"❌ OCR Failed: {result.get('error', 'Unknown error')}")
            
        return result

    def test_full_pipeline(self, image_path: str, customer_info: Dict = None, 
                          document_type: str = 'aadhaar') -> Dict:
        """Test complete AI processing pipeline with real image"""
        print(f"\n🚀 Testing Full AI Pipeline with: {Path(image_path).name}")
        print("=" * 60)
        
        # Load image
        image_data = self.load_image_from_file(image_path)
        
        # Run full pipeline
        result = self.ai_processor.process_document(image_data, document_type, customer_info)
        
        # Display comprehensive results
        self._display_pipeline_results(result)
        
        return result

    def _display_pipeline_results(self, result: Dict):
        """Display comprehensive pipeline results"""
        
        # Processing steps summary
        print(f"\n📋 Processing Steps Summary:")
        steps = result.get('processing_steps', {})
        
        for step_name, step_result in steps.items():
            status = "✅" if step_result.get('success', False) else "❌"
            print(f"  {status} {step_name.replace('_', ' ').title()}")
        
        # Final analysis
        final_analysis = result.get('final_analysis', {})
        print(f"\n🎯 Final Analysis:")
        print("-" * 30)
        print(f"Status: {final_analysis.get('status', 'UNKNOWN')}")
        print(f"Fraud Score: {final_analysis.get('overall_fraud_score', 0.0):.3f}")
        print(f"Confidence: {final_analysis.get('overall_confidence', 0.0):.3f}")
        print(f"Risk Level: {final_analysis.get('risk_level', 'UNKNOWN')}")
        
        # Fraud indicators
        indicators = final_analysis.get('fraud_indicators', [])
        if indicators:
            print(f"\n⚠️ Fraud Indicators:")
            for indicator in indicators:
                print(f"  • {indicator.replace('_', ' ').title()}")
        
        # Recommendation
        recommendation = final_analysis.get('recommendation', '')
        if recommendation:
            print(f"\n💡 Recommendation: {recommendation}")

    def test_multiple_engines(self, image_path: str, document_type: str = 'aadhaar'):
        """Test individual OCR engines separately"""
        print(f"\n🔧 Testing Individual OCR Engines with: {Path(image_path).name}")
        print("=" * 60)
        
        image_data = self.load_image_from_file(image_path)
        
        # Get available engines
        available_engines = self.ocr_processor.get_available_engines()
        original_engines = AIConfig.OCR_ENGINES.copy()
        
        results = {}
        
        for engine in available_engines:
            print(f"\n🧪 Testing {engine.upper()} Engine:")
            print("-" * 30)
            
            # Temporarily set to use only this engine
            AIConfig.OCR_ENGINES = [engine]
            
            try:
                result = self.ocr_processor.extract_text_from_document(image_data, document_type)
                results[engine] = result
                
                if result['success']:
                    print(f"✅ Success! Confidence: {result.get('confidence_score', 0.0):.3f}")
                    text_preview = result.get('extracted_text', '')[:100]
                    print(f"📄 Text Preview: {text_preview}...")
                    
                    fields = result.get('field_extractions', {})
                    print(f"🏷️ Fields Extracted: {len(fields)} fields")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Engine Error: {str(e)}")
                results[engine] = {'success': False, 'error': str(e)}
        
        # Restore original engine configuration
        AIConfig.OCR_ENGINES = original_engines
        
        # Summary comparison
        print(f"\n📊 Engine Comparison Summary:")
        print("-" * 40)
        for engine, result in results.items():
            status = "✅" if result.get('success', False) else "❌"
            confidence = result.get('confidence_score', 0.0)
            print(f"{status} {engine.upper()}: Confidence {confidence:.3f}")
        
        return results

def main():
    """Main testing function"""
    tester = RealImageTester()
    
    # Get image file path from user
    print("🧪 IntelliKYC Real Aadhaar Image Tester")
    print("=" * 50)
    print("⚠️  PRIVACY NOTICE: Only use test/sample documents or your own documents")
    print("⚠️  Do not use other people's real Aadhaar cards for testing")
    print("=" * 50)
    
    # Image path input
    image_path = input("\n📁 Enter path to Aadhaar image file: ").strip().strip('"\'')
    
    if not image_path or not os.path.exists(image_path):
        print("❌ Invalid file path. Please provide a valid image file.")
        return
    
    # Document type
    doc_type = input("📄 Document type (aadhaar/pan) [default: aadhaar]: ").strip().lower() or 'aadhaar'
    
    # Test selection
    print(f"\n🔧 Select test type:")
    print("1. OCR Only (Quick)")
    print("2. Full AI Pipeline (Comprehensive)")
    print("3. Compare All OCR Engines")
    print("4. All Tests")
    
    choice = input("Enter choice (1-4): ").strip()
    
    try:
        if choice == '1' or choice == '4':
            tester.test_ocr_only(image_path, doc_type)
            
        if choice == '3' or choice == '4':
            tester.test_multiple_engines(image_path, doc_type)
            
        if choice == '2' or choice == '4':
            # Optional customer info for validation
            print(f"\n📋 Optional: Provide customer info for field validation")
            print("(Press Enter to skip each field)")
            
            customer_info = {}
            name = input("Name: ").strip()
            if name:
                customer_info['name'] = name
                
            dob = input("Date of Birth (DD/MM/YYYY or DD-MM-YYYY): ").strip()
            if dob:
                customer_info['date_of_birth'] = dob
                
            if doc_type == 'aadhaar':
                aadhaar = input("Aadhaar Number (12 digits): ").strip()
                if aadhaar:
                    customer_info['aadhaar_number'] = aadhaar
            else:
                pan = input("PAN Number: ").strip()
                if pan:
                    customer_info['pan_number'] = pan
                    
            tester.test_full_pipeline(image_path, customer_info, doc_type)
            
    except Exception as e:
        print(f"\n❌ Testing failed: {str(e)}")
        print("💡 Make sure the image file is accessible and in a supported format")

if __name__ == "__main__":
    main()
