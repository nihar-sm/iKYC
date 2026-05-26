"""
Test Simplified Free OCR Setup
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from ocr.free_multi_ocr import FreeMultiOCRProcessor
from config.ai_config import AIConfig

def test_simplified_ocr_setup():
    print("🧪 Testing Simplified Free OCR Setup")
    print("=" * 50)

    # Test configuration
    print("📋 Configuration Check:")
    try:
        print(f"OCR Engines: {AIConfig.OCR_ENGINES}")
        print(f"OCR.space API Key: {'✓ Set' if AIConfig.OCR_SPACE_API_KEY != 'FREE_API_KEY' else '❌ Not set (optional)'}")
        print(f"OCR.space URL: {AIConfig.OCR_SPACE_URL}")
        print(f"OCR Confidence Threshold: {AIConfig.OCR_CONFIDENCE_THRESHOLD}")
        print(f"Supported Formats: {AIConfig.OCR_SUPPORTED_FORMATS}")
    except AttributeError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Make sure ai_config.py has all required OCR configuration attributes")
        return False

    # Initialize OCR processor
    print("\n🔧 Initializing Simplified OCR Engines...")
    try:
        ocr_processor = FreeMultiOCRProcessor()
    except Exception as e:
        print(f"❌ OCR Processor initialization failed: {e}")
        return False

    # Check available engines
    available_engines = ocr_processor.get_available_engines()
    engine_info = ocr_processor.get_engine_info()

    print(f"\n📊 Available Engines: {available_engines}")
    print("🔧 Engine Details:")
    for engine, info in engine_info.items():
        print(f"   • {info['name']}: {info['type']}, {info['cost']}, Accuracy: {info['accuracy']}")

    # Test with mock image
    print("\n🖼️ Testing with mock image...")
    try:
        from PIL import Image
        import io

        # Create test image
        img = Image.new('RGB', (800, 600), color='white')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        mock_image_data = img_byte_arr.getvalue()

        # Test OCR
        result = ocr_processor.extract_text_from_document(mock_image_data, 'aadhaar')

        if result['success']:
            print(f"✅ OCR Test Successful!")
            print(f"   Engine Used: {result['ocr_engine']}")
            print(f"   Confidence: {result['confidence_score']:.3f}")
            print(f"   Text Preview: {result['extracted_text'][:100]}...")
            
            if 'field_extractions' in result and result['field_extractions']:
                print(f"   Extracted Fields: {list(result['field_extractions'].keys())}")
        else:
            print(f"❌ OCR Test Failed: {result.get('error', 'Unknown error')}")
            return False

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install required packages: pip install Pillow")
        return False
    except Exception as e:
        print(f"❌ OCR Test Error: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 Simplified Free OCR Setup Test Complete!")

    # Recommendations
    print("\n💡 Recommendations:")
    if 'easyocr' in available_engines:
        print("✅ EasyOCR is your primary engine - works offline!")
    else:
        print("💡 Consider installing EasyOCR: pip install easyocr")
        
    if 'ocr_space' not in available_engines:
        print("💡 Consider getting free OCR.space API key for backup")
        print("   Get it at: https://ocr.space/ocrapi")
    else:
        print("✅ OCR.space API configured as backup")
        
    print("🚀 Your OCR system is ready for production!")
    return True

if __name__ == "__main__":
    success = test_simplified_ocr_setup()
    if not success:
        print("\n❌ Setup test failed. Please fix the issues above.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
