"""
AI Orchestrator for IntelliKYC Document Processing
Coordinates EasyOCR, Groq LLM (text + vision), and image utilities.
"""

from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr.free_multi_ocr import FreeMultiOCRProcessor
from ibm.granite_client import GraniteAIProcessor     # Groq text analysis
from aws.bedrock_client import BedrockTitanProcessor   # Groq vision analysis
from utils.image_utils import ImageProcessor

class AIDocumentProcessor:
    """Main AI orchestrator for document processing and fraud detection"""

    def __init__(self):
        """Initialize all AI processors"""
        self.free_multi_ocr = FreeMultiOCRProcessor()  # NEW - Simplified free multi-engine OCR
        self.granite_ai = GraniteAIProcessor()
        self.bedrock_titan = BedrockTitanProcessor()
        self.image_processor = ImageProcessor()

    def process_document(self, image_data: bytes, document_type: str,
                        customer_info: Dict = None) -> Dict:
        """
        Complete document processing pipeline (Updated with Simplified Free OCR)
        """
        print(f"🔍 Starting AI processing for {document_type.upper()} document")

        results = {
            'document_type': document_type,
            'processing_steps': {},
            'final_analysis': {},
            'timestamp': self._get_timestamp()
        }

        try:
            # Step 1: Image preprocessing and quality analysis
            print("📸 Step 1: Image preprocessing...")
            preprocessing_result = self.image_processor.preprocess_document_image(image_data)
            results['processing_steps']['image_preprocessing'] = preprocessing_result

            if not preprocessing_result['success']:
                results['final_analysis'] = {
                    'status': 'FAILED',
                    'reason': 'Image preprocessing failed',
                    'fraud_score': 1.0
                }
                return results

            # Step 2: Simplified Free Multi-Engine OCR text extraction (UPDATED)
            print("📄 Step 2: Simplified free multi-engine OCR text extraction...")
            ocr_result = self.free_multi_ocr.extract_text_from_document(
                image_data,  # Use original image data
                document_type
            )
            results['processing_steps']['ocr_extraction'] = ocr_result

            if not ocr_result['success']:
                results['final_analysis'] = {
                    'status': 'FAILED',
                    'reason': 'OCR extraction failed',
                    'fraud_score': 0.8
                }
                return results

            # Step 3: Tampering detection
            print("🔒 Step 3: Tampering detection...")
            tampering_result = self.image_processor.detect_tampering_signs(image_data)
            results['processing_steps']['tampering_detection'] = tampering_result

            # Step 4: Groq semantic analysis
            print("🧠 Step 4: Groq semantic analysis...")
            semantic_result = self.granite_ai.analyze_document_semantics(
                ocr_result['extracted_text'],
                document_type
            )
            results['processing_steps']['semantic_analysis'] = semantic_result

            # Step 5: Groq fraud detection
            print("🚨 Step 5: Groq fraud detection...")
            fraud_result = self.granite_ai.detect_fraud_patterns(
                ocr_result['extracted_text'],
                ocr_result.get('field_extractions', {})
            )
            results['processing_steps']['fraud_detection'] = fraud_result

            # Step 6: Groq risk analysis
            print("⚖️ Step 6: Groq risk analysis...")
            risk_result = self.bedrock_titan.analyze_document_risk(
                ocr_result['extracted_text'],
                ocr_result.get('confidence_score', 0.0)
            )
            results['processing_steps']['risk_analysis'] = risk_result

            # Step 7: Groq authenticity validation
            print("✅ Step 7: Groq authenticity validation...")
            document_data = {
                'extracted_text': ocr_result['extracted_text'],
                'ocr_confidence': ocr_result.get('confidence_score', 0.0),
                'image_quality': preprocessing_result.get('quality_metrics', {}),
                'field_extractions': ocr_result.get('field_extractions', {})
            }
            authenticity_result = self.bedrock_titan.validate_document_authenticity(document_data)
            results['processing_steps']['authenticity_validation'] = authenticity_result

            # Step 8: Cross-validation between IBM and AWS
            print("🔗 Step 8: Cross-validation...")
            if fraud_result['success'] and risk_result['success']:
                cross_validation = self.bedrock_titan.cross_validate_with_ibm(
                    fraud_result,
                    {'risk_analysis': risk_result.get('risk_analysis', {}),
                     'authenticity_analysis': authenticity_result.get('authenticity_analysis', {})}
                )
                results['processing_steps']['cross_validation'] = cross_validation

            # Step 9: Field validation against customer info
            print("📋 Step 9: Field validation...")
            if customer_info:
                field_validation = self._validate_extracted_fields(
                    ocr_result.get('field_extractions', {}),
                    customer_info,
                    document_type
                )
                results['processing_steps']['field_validation'] = field_validation

            # Step 10: Generate final analysis
            print("🎯 Step 10: Generating final analysis...")
            final_analysis = self._generate_final_analysis(results['processing_steps'])
            results['final_analysis'] = final_analysis

            print(f"✅ AI processing completed: {final_analysis['status']}")
            return results

        except Exception as e:
            print(f"❌ AI processing failed: {str(e)}")
            results['final_analysis'] = {
                'status': 'ERROR',
                'reason': f'Processing error: {str(e)}',
                'fraud_score': 0.9
            }
            return results

    def _validate_extracted_fields(self, extracted_fields: Dict, customer_info: Dict,
                                  document_type: str) -> Dict:
        """Validate extracted fields against provided customer information"""
        validation_results = {
            'matched_fields': [],
            'mismatched_fields': [],
            'missing_fields': [],
            'validation_score': 0.0
        }

        # Define expected fields based on document type
        if document_type == 'aadhaar':
            expected_fields = ['name', 'date_of_birth', 'aadhaar_number']
        else:  # PAN
            expected_fields = ['name', 'date_of_birth', 'pan_number']

        matched_count = 0
        total_checks = 0

        for field in expected_fields:
            customer_value = customer_info.get(field, '').lower().strip()
            extracted_value = extracted_fields.get(field, '').lower().strip()

            if not extracted_value:
                validation_results['missing_fields'].append(field)
            elif customer_value and extracted_value:
                total_checks += 1
                if self._fuzzy_match(customer_value, extracted_value):
                    validation_results['matched_fields'].append(field)
                    matched_count += 1
                else:
                    validation_results['mismatched_fields'].append({
                        'field': field,
                        'customer_value': customer_value,
                        'extracted_value': extracted_value
                    })

        # Calculate validation score
        validation_results['validation_score'] = matched_count / total_checks if total_checks > 0 else 0.0
        return validation_results

    def _fuzzy_match(self, value1: str, value2: str, threshold: float = 0.8) -> bool:
        """Fuzzy string matching for field validation"""
        # Simple fuzzy matching (can be enhanced with libraries like fuzzywuzzy)
        value1 = value1.replace(' ', '').replace('/', '').replace('-', '')
        value2 = value2.replace(' ', '').replace('/', '').replace('-', '')

        if value1 == value2:
            return True

        # Check if one contains the other (for partial matches)
        if len(value1) > 5 and len(value2) > 5:
            return value1 in value2 or value2 in value1

        return False

    def _generate_final_analysis(self, processing_steps: Dict) -> Dict:
        """Generate final comprehensive analysis"""
        # Collect all scores and indicators
        scores = []
        fraud_indicators = []
        confidence_scores = []

        # OCR results
        ocr_result = processing_steps.get('ocr_extraction', {})
        if ocr_result.get('success'):
            ocr_confidence = ocr_result.get('confidence_score', 0.0)
            confidence_scores.append(ocr_confidence)
            if ocr_confidence < 0.7:
                fraud_indicators.append('low_ocr_confidence')

        # Tampering detection
        tampering_result = processing_steps.get('tampering_detection', {})
        if tampering_result.get('success'):
            tampering_score = tampering_result.get('tampering_score', 0.0)
            scores.append(tampering_score)
            if tampering_result.get('is_likely_tampered', False):
                fraud_indicators.append('tampering_detected')

        # IBM Granite fraud detection
        fraud_result = processing_steps.get('fraud_detection', {})
        if fraud_result.get('success'):
            fraud_score = fraud_result.get('fraud_score', 0.0)
            scores.append(fraud_score)
            if fraud_score > 0.5:
                fraud_indicators.append('ai_fraud_detection')

        # AWS Bedrock risk analysis
        risk_result = processing_steps.get('risk_analysis', {})
        if risk_result.get('success'):
            risk_analysis = risk_result.get('risk_analysis', {})
            risk_score = risk_analysis.get('overall_risk_score', 0.0)
            scores.append(risk_score)
            if risk_score > 0.5:
                fraud_indicators.append('high_risk_detected')

        # Cross-validation results
        cross_validation = processing_steps.get('cross_validation', {})
        if cross_validation.get('success'):
            consensus_analysis = cross_validation.get('consensus_analysis', {})
            consensus_fraud_score = consensus_analysis.get('fraud_score', 0.0)
            scores.append(consensus_fraud_score)
            agreement_level = consensus_analysis.get('agreement_level', 'LOW')
            if agreement_level == 'LOW':
                fraud_indicators.append('ai_disagreement')

        # Field validation
        field_validation = processing_steps.get('field_validation', {})
        if field_validation:
            validation_score = field_validation.get('validation_score', 0.0)
            if validation_score < 0.8:
                fraud_indicators.append('field_mismatch')
            scores.append(1.0 - validation_score)

        # Calculate overall fraud score
        overall_fraud_score = sum(scores) / len(scores) if scores else 0.0
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Determine final status
        if overall_fraud_score > 0.7 or 'tampering_detected' in fraud_indicators:
            status = 'REJECTED'
            risk_level = 'HIGH'
        elif overall_fraud_score > 0.4 or len(fraud_indicators) > 2:
            status = 'MANUAL_REVIEW'
            risk_level = 'MEDIUM'
        elif overall_confidence > 0.8 and overall_fraud_score < 0.3:
            status = 'APPROVED'
            risk_level = 'LOW'
        else:
            status = 'MANUAL_REVIEW'
            risk_level = 'MEDIUM'

        return {
            'status': status,
            'overall_fraud_score': round(overall_fraud_score, 3),
            'overall_confidence': round(overall_confidence, 3),
            'risk_level': risk_level,
            'fraud_indicators': fraud_indicators,
            'processing_quality': 'HIGH' if len(processing_steps) >= 7 else 'PARTIAL',
            'recommendation': self._get_recommendation(status, fraud_indicators),
            'summary': self._generate_summary(status, overall_fraud_score, fraud_indicators)
        }

    def _get_recommendation(self, status: str, fraud_indicators: List[str]) -> str:
        """Generate processing recommendation"""
        if status == 'APPROVED':
            return 'Document verified successfully. Proceed with KYC completion.'
        elif status == 'REJECTED':
            return 'Document rejected due to fraud indicators. Request new documents.'
        else:
            return f'Manual review required. Check: {", ".join(fraud_indicators[:3])}'

    def _generate_summary(self, status: str, fraud_score: float, indicators: List[str]) -> str:
        """Generate processing summary"""
        if status == 'APPROVED':
            return f'Document passed all AI verification checks with fraud score {fraud_score:.2f}'
        elif status == 'REJECTED':
            return f'Document failed verification due to: {", ".join(indicators[:2])}'
        else:
            return f'Document requires review - fraud score {fraud_score:.2f}, issues: {len(indicators)}'

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_ocr_engines_status(self) -> Dict:
        """Get status of all OCR engines"""
        return {
            'available_engines': self.free_multi_ocr.get_available_engines(),
            'engine_status': self.free_multi_ocr.get_engine_status(),
            'engine_info': self.free_multi_ocr.get_engine_info()
        }


# Test function for the complete AI pipeline
def test_ai_pipeline():
    """Test the complete AI document processing pipeline with Simplified Free OCR"""
    print("🧪 Testing IntelliKYC AI Document Processing Pipeline (Simplified Free OCR Edition)")
    print("=" * 75)

    # Initialize AI processor
    ai_processor = AIDocumentProcessor()

    # Display OCR engine status
    ocr_status = ai_processor.get_ocr_engines_status()
    print(f"📊 Available OCR Engines: {ocr_status['available_engines']}")
    print(f"🔧 Engine Details:")
    for engine, info in ocr_status['engine_info'].items():
        print(f"   • {info['name']}: {info['type']}, {info['cost']}, Accuracy: {info['accuracy']}")

    # Mock document data (in real implementation, this would be actual image bytes)
    mock_image_data = b"mock_aadhaar_image_data"

    # Mock customer information for validation
    mock_customer_info = {
        'name': 'Rajesh Kumar',
        'date_of_birth': '15-08-1985',
        'aadhaar_number': '234567890124'
    }

    # Test Aadhaar processing
    print("\n📋 Testing Aadhaar Document Processing")
    print("-" * 40)
    aadhaar_result = ai_processor.process_document(
        mock_image_data,
        'aadhaar',
        mock_customer_info
    )

    print(f"📊 Final Status: {aadhaar_result['final_analysis']['status']}")
    print(f"🎯 Fraud Score: {aadhaar_result['final_analysis']['overall_fraud_score']:.3f}")
    print(f"📈 Confidence: {aadhaar_result['final_analysis']['overall_confidence']:.3f}")
    print(f"⚠️ Risk Level: {aadhaar_result['final_analysis']['risk_level']}")

    # Test PAN processing  
    print("\n📋 Testing PAN Document Processing")  
    print("-" * 40)
    mock_pan_info = {
        'name': 'Rajesh Kumar',
        'date_of_birth': '15-08-1985',
        'pan_number': 'ABCDE1234F'
    }

    pan_result = ai_processor.process_document(
        mock_image_data,
        'pan',
        mock_pan_info
    )

    print(f"📊 Final Status: {pan_result['final_analysis']['status']}")
    print(f"🎯 Fraud Score: {pan_result['final_analysis']['overall_fraud_score']:.3f}")
    print(f"📈 Confidence: {pan_result['final_analysis']['overall_confidence']:.3f}")
    print(f"⚠️ Risk Level: {pan_result['final_analysis']['risk_level']}")

    print("\n" + "=" * 75)
    print("🎉 Simplified Free OCR AI Pipeline Testing Completed!")
    print("🚀 Ready for integration with validation engine and API!")


if __name__ == "__main__":
    test_ai_pipeline()
