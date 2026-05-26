import requests
import json
from typing import Dict, Any, Optional

class IntelliKYCClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def upload_document(self, file, document_type: str = "aadhaar"):
        """Upload document with proper file handling and error handling"""
        try:
            # Fix 1: Proper multipart file formatting
            files = {"file": (file.name, file, file.type)}
            data = {"document_type": document_type}

            # Fix 2: Add timeout and better error handling
            response = requests.post(
                f"{self.base_url}/api/v1/documents/upload",
                files=files,
                data=data,
                timeout=30
            )

            # Fix 3: Check response status
            if response.status_code == 200:
                return response.json()
            else:
                try:
                    error_data = response.json()
                    return {"error": error_data.get("detail", f"Server error {response.status_code}")}
                except:
                    return {"error": f"Server error {response.status_code}: {response.text}"}

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to backend server. Is it running on http://localhost:8000?"}
        except requests.exceptions.Timeout:
            return {"error": "Upload timed out. Please try again."}
        except Exception as e:
            return {"error": f"Upload failed: {str(e)}"}

    def process_document(self, document_id: str):
        """Process document with error handling"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/documents/{document_id}/process",
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Processing failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Processing error: {str(e)}"}

    def validate_fields(self, fields: Dict[str, Any]):
        """Direct field validation with error handling"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/validation/validate-fields",
                json={"fields": fields},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Validation failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Validation error: {str(e)}"}

    def analyze_fraud(self, text: str, image_path: str, document_type: str = "aadhaar"):
        """Direct fraud analysis with error handling"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/fraud/analyze",
                json={
                    "text": text,
                    "image_path": image_path,
                    "document_type": document_type
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Fraud analysis failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Fraud analysis error: {str(e)}"}

    def get_fraud_status(self):
        """Get fraud detection service status"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/fraud/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status check failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Status check error: {str(e)}"}

    def analyze_liveness(self, video_data: dict):
        """Analyze face liveness with real video data (hand gestures)"""
        try:
            print(f"📤 Sending {len(video_data.get('frames', []))} frames for hand gesture analysis...")
            response = requests.post(
                f"{self.base_url}/api/v1/liveness/analyze",
                json=video_data,
                timeout=120  # Longer timeout for video processing
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Hand gesture liveness analysis response received")
                return result
            else:
                try:
                    error_data = response.json()
                    return {"error": error_data.get("detail", f"Server error {response.status_code}")}
                except:
                    return {"error": f"Server error {response.status_code}"}

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to backend server. Is it running?"}
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Video may be too large."}
        except Exception as e:
            return {"error": f"Analysis error: {str(e)}"}

    # NEW METHODS FOR ENHANCED FACE VALIDATION
    
    def initiate_face_liveness_check(self):
        """Initiate face liveness verification session"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/liveness/face/initiate",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Face liveness session initiated")
                return result
            else:
                return {"error": f"Failed to initiate face liveness: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Face liveness initiation error: {str(e)}"}

    def analyze_face_liveness_sequence(self, video_frames: list):
        """Analyze face liveness sequence (blink, smile, head movements)"""
        try:
            print(f"📤 Sending {len(video_frames)} frames for face liveness analysis...")
            response = requests.post(
                f"{self.base_url}/api/v1/liveness/face/analyze",
                json={"video_frames": video_frames},
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Face liveness analysis response received")
                return result
            else:
                try:
                    error_data = response.json()
                    return {"error": error_data.get("detail", f"Server error {response.status_code}")}
                except:
                    return {"error": f"Server error {response.status_code}"}

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to backend server. Is it running?"}
        except requests.exceptions.Timeout:
            return {"error": "Face liveness analysis timed out"}
        except Exception as e:
            return {"error": f"Face liveness analysis error: {str(e)}"}

    def analyze_combined_liveness(self, face_frames: list, hand_gesture_data: dict):
        """Analyze combined face + hand gesture liveness"""
        try:
            payload = {
                "face_frames": face_frames,
                "hand_gesture_data": hand_gesture_data
            }
            
            print(f"📤 Sending combined liveness data for analysis...")
            response = requests.post(
                f"{self.base_url}/api/v1/liveness/combined/analyze",
                json=payload,
                timeout=180  # Longer timeout for combined analysis
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Combined liveness analysis completed")
                return result
            else:
                try:
                    error_data = response.json()
                    return {"error": error_data.get("detail", f"Server error {response.status_code}")}
                except:
                    return {"error": f"Server error {response.status_code}"}

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to backend server. Is it running?"}
        except requests.exceptions.Timeout:
            return {"error": "Combined liveness analysis timed out"}
        except Exception as e:
            return {"error": f"Combined liveness analysis error: {str(e)}"}

    def validate_kyc_decision(self, liveness_result: dict):
        """Get KYC decision based on liveness results"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/kyc/validate-decision",
                json={"liveness_result": liveness_result},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ KYC decision received: {result.get('kyc_status', 'Unknown')}")
                return result
            else:
                return {"error": f"KYC decision failed: {response.status_code}"}

        except Exception as e:
            return {"error": f"KYC decision error: {str(e)}"}

    def process_with_liveness(self, document_id: str, liveness_video: Optional[str] = None, 
                            face_liveness_result: Optional[dict] = None):
        """Complete KYC with enhanced liveness verification and error handling"""
        try:
            payload = {}
            if liveness_video:
                payload["liveness_video"] = liveness_video
            if face_liveness_result:
                payload["face_liveness_result"] = face_liveness_result

            response = requests.post(
                f"{self.base_url}/api/v1/documents/{document_id}/process-with-liveness",
                json=payload,
                timeout=120  # Longer timeout for complete processing
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Complete KYC with liveness processing completed")
                return result
            else:
                return {"error": f"Complete processing failed: {response.status_code}"}

        except Exception as e:
            return {"error": f"Complete processing error: {str(e)}"}

    def get_liveness_service_status(self):
        """Get liveness detection service status"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/liveness/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Liveness status check failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Liveness status check error: {str(e)}"}

    # UTILITY METHODS
    
    def encode_frames_for_api(self, frames: list):
        """Helper method to encode frames for API transmission"""
        import base64
        import cv2
        import numpy as np
        
        encoded_frames = []
        for frame in frames:
            try:
                if isinstance(frame, np.ndarray):
                    # Resize frame for efficiency
                    resized_frame = cv2.resize(frame, (640, 480))
                    # Encode as JPEG
                    _, buffer = cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    # Convert to base64
                    encoded_frame = base64.b64encode(buffer).decode('utf-8')
                    encoded_frames.append(encoded_frame)
            except Exception as e:
                print(f"Warning: Failed to encode frame: {e}")
                continue
        
        return encoded_frames

    def health_check(self):
        """Check overall system health"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Health check failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Health check error: {str(e)}"}

# Global client instance
api_client = IntelliKYCClient()
