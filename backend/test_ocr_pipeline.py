import asyncio
import requests
import json
import os
from pathlib import Path
import time
from typing import Dict, List, Any

class OCRPipelineTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
    
    def test_server_health(self) -> bool:
        """Test if the API server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                print("✅ API server is healthy")
                return True
            else:
                print(f"❌ API server unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API server: {e}")
            return False
    
    def upload_document(self, file_path: str, document_type: str = "aadhaar") -> Dict[str, Any]:
        """Upload a document to the API"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'document_type': document_type}
                
                response = requests.post(
                    f"{self.base_url}/api/v1/documents/upload",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful: {result['document_id']}")
                return result
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return {"error": f"Upload failed: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Upload exception: {e}")
            return {"error": str(e)}
    
    def process_document(self, document_id: str) -> Dict[str, Any]:
        """Process uploaded document with OCR"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/documents/{document_id}/process",
                timeout=60  # OCR can take time
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ OCR processing successful for {document_id}")
                return result
            else:
                print(f"❌ OCR processing failed: {response.status_code} - {response.text}")
                return {"error": f"Processing failed: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Processing exception: {e}")
            return {"error": str(e)}
    
    def test_single_document(self, file_path: str, document_type: str, expected_fields: Dict[str, str] = None) -> Dict[str, Any]:
        """Test complete pipeline for a single document"""
        print(f"\n🧪 Testing: {os.path.basename(file_path)}")
        
        test_result = {
            "file": os.path.basename(file_path),
            "document_type": document_type,
            "timestamp": time.time(),
            "upload_success": False,
            "ocr_success": False,
            "fields_extracted": {},
            "accuracy_score": 0.0,
            "errors": []
        }
        
        # Step 1: Upload document
        upload_result = self.upload_document(file_path, document_type)
        if "error" in upload_result:
            test_result["errors"].append(f"Upload error: {upload_result['error']}")
            return test_result
        
        test_result["upload_success"] = True
        document_id = upload_result["document_id"]
        
        # Step 2: Process with OCR
        time.sleep(2)  # Brief pause between upload and processing
        ocr_result = self.process_document(document_id)
        
        if "error" in ocr_result:
            test_result["errors"].append(f"OCR error: {ocr_result['error']}")
            return test_result
        
        test_result["ocr_success"] = True
        test_result["ocr_engine"] = ocr_result.get("ocr_result", {}).get("engine", "unknown")
        test_result["ocr_confidence"] = ocr_result.get("ocr_result", {}).get("confidence", 0.0)
        test_result["extracted_text"] = ocr_result.get("ocr_result", {}).get("text", "")
        test_result["fields_extracted"] = ocr_result.get("extracted_fields", {})
        
        # Step 3: Validate extracted fields
        if expected_fields:
            test_result["accuracy_score"] = self.calculate_accuracy(
                test_result["fields_extracted"], 
                expected_fields
            )
        
        return test_result
    
    def calculate_accuracy(self, extracted: Dict[str, str], expected: Dict[str, str]) -> float:
        """Calculate accuracy score based on expected vs extracted fields"""
        if not expected:
            return 1.0
        
        correct_fields = 0
        total_fields = len(expected)
        
        for key, expected_value in expected.items():
            extracted_value = extracted.get(key, "").strip()
            if extracted_value and expected_value.lower() in extracted_value.lower():
                correct_fields += 1
        
        return correct_fields / total_fields if total_fields > 0 else 0.0
    
    def test_document_directory(self, directory_path: str, document_type: str) -> List[Dict[str, Any]]:
        """Test all documents in a directory"""
        directory = Path(directory_path)
        results = []
        
        if not directory.exists():
            print(f"❌ Directory not found: {directory_path}")
            return results
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff'}
        test_files = [
            f for f in directory.glob("*") 
            if f.suffix.lower() in image_extensions
        ]
        
        print(f"\n📁 Testing {len(test_files)} files in {directory.name}")
        
        for file_path in test_files:
            result = self.test_single_document(str(file_path), document_type)
            results.append(result)
            self.test_results.append(result)
        
        return results
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        total_tests = len(self.test_results)
        successful_uploads = sum(1 for r in self.test_results if r["upload_success"])
        successful_ocr = sum(1 for r in self.test_results if r["ocr_success"])
        
        # Calculate average accuracy
        accuracy_scores = [r["accuracy_score"] for r in self.test_results if r["accuracy_score"] > 0]
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        
        # Calculate average confidence
        confidences = [r.get("ocr_confidence", 0) for r in self.test_results if r.get("ocr_confidence")]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Engine usage statistics
        engine_usage = {}
        for result in self.test_results:
            engine = result.get("ocr_engine", "unknown")
            engine_usage[engine] = engine_usage.get(engine, 0) + 1
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "upload_success_rate": successful_uploads / total_tests,
                "ocr_success_rate": successful_ocr / total_tests,
                "average_accuracy": avg_accuracy,
                "average_confidence": avg_confidence
            },
            "engine_statistics": engine_usage,
            "detailed_results": self.test_results,
            "timestamp": time.time()
        }
        
        return report
    
    def save_report(self, filename: str = "ocr_test_report.json"):
        """Save test report to file"""
        report = self.generate_test_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Test report saved to: {filename}")
        return report

# Main testing function
def run_ocr_tests():
    """Run comprehensive OCR pipeline tests"""
    tester = OCRPipelineTester()
    
    # Step 1: Check server health
    if not tester.test_server_health():
        print("❌ Server not available. Please start your FastAPI application first.")
        return
    
    # Step 2: Test sample documents
    print("\n" + "="*60)
    print("🧪 STARTING OCR PIPELINE TESTS")
    print("="*60)
    
    # Test Aadhaar documents
    if os.path.exists("test_documents/aadhaar"):
        print("\n📋 Testing Aadhaar Documents...")
        aadhaar_results = tester.test_document_directory("test_documents/aadhaar", "aadhaar")
    
    # Test PAN documents  
    if os.path.exists("test_documents/pan"):
        print("\n📋 Testing PAN Documents...")
        pan_results = tester.test_document_directory("test_documents/pan", "pan")
    
    # Test invalid documents
    if os.path.exists("test_documents/invalid"):
        print("\n📋 Testing Invalid Documents...")
        invalid_results = tester.test_document_directory("test_documents/invalid", "aadhaar")
    
    # Generate and save report
    print("\n" + "="*60)
    print("📊 GENERATING TEST REPORT")
    print("="*60)
    
    report = tester.save_report()
    
    # Print summary
    summary = report["summary"]
    print(f"\n📈 TEST SUMMARY:")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Upload Success Rate: {summary['upload_success_rate']:.1%}")
    print(f"   OCR Success Rate: {summary['ocr_success_rate']:.1%}")
    print(f"   Average Accuracy: {summary['average_accuracy']:.1%}")
    print(f"   Average Confidence: {summary['average_confidence']:.1%}")
    
    print(f"\n🔧 ENGINE USAGE:")
    for engine, count in report["engine_statistics"].items():
        print(f"   {engine}: {count} documents")

if __name__ == "__main__":
    run_ocr_tests()

