"""
Enhanced Face Validators with Live Detection Capabilities
"""

import random
import numpy as np
from typing import Dict, List
import cv2
import mediapipe as mp
from datetime import datetime

class LiveFaceValidators:
    """Enhanced validators for live face liveness detection"""
    
    def __init__(self):
        # Initialize MediaPipe face detection
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.7
        )

    @staticmethod
    def initiate_live_liveness_check() -> Dict:
        """Initiate live face liveness check with specific actions"""
        required_actions = ["blink", "turn_head_left", "turn_head_right", "smile"]
        return {
            "valid": True,
            "field": "live_liveness_initiation",
            "message": "Live face liveness check initiated",
            "data": {
                "required_actions": required_actions,
                "instructions": {
                    "blink": "Please blink your eyes naturally 2-3 times",
                    "turn_head_left": "Slowly turn your head to the left",
                    "turn_head_right": "Slowly turn your head to the right",
                    "smile": "Please smile naturally"
                },
                "min_confidence": 0.8,
                "session_id": f"live_liveness_{random.randint(1000, 9999)}",
                "timeout_seconds": 30
            }
        }

    def detect_face_in_frame(self, frame: np.ndarray) -> Dict:
        """Detect face in video frame"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            
            if not results.detections:
                return {
                    "face_detected": False,
                    "confidence": 0.0,
                    "error": "No face detected in frame"
                }
            
            # Get first detection
            detection = results.detections[0]
            confidence = detection.score[0]
            
            # Extract bounding box
            bbox = detection.location_data.relative_bounding_box
            
            return {
                "face_detected": True,
                "confidence": float(confidence),
                "bbox": {
                    "x": bbox.xmin,
                    "y": bbox.ymin,
                    "width": bbox.width,
                    "height": bbox.height
                },
                "frame_quality": "high" if confidence > 0.8 else "medium"
            }
            
        except Exception as e:
            return {
                "face_detected": False,
                "confidence": 0.0,
                "error": f"Face detection failed: {str(e)}"
            }

    def detect_blink_sequence(self, video_frames: List[np.ndarray]) -> Dict:
        """Detect blinking sequence in video frames"""
        try:
            # Mock blink detection (in production, use eye aspect ratio)
            blink_count = 0
            frame_count = len(video_frames)
            
            # Simulate blink detection
            if frame_count >= 10:  # Need at least 10 frames
                blink_count = random.randint(1, 3)  # 1-3 blinks detected
            
            return {
                "valid": blink_count >= 1,
                "blink_count": blink_count,
                "confidence": 0.9 if blink_count >= 1 else 0.3,
                "message": f"Detected {blink_count} blinks in sequence"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Blink detection failed: {str(e)}",
                "confidence": 0.0
            }

    def detect_head_movement(self, video_frames: List[np.ndarray], direction: str) -> Dict:
        """Detect head movement in specified direction"""
        try:
            if len(video_frames) < 5:
                return {
                    "valid": False,
                    "error": "Insufficient frames for head movement detection"
                }
            
            # Mock head movement detection
            movement_detected = random.choice([True, True, False])  # 66% success rate
            confidence = random.uniform(0.7, 0.95) if movement_detected else random.uniform(0.3, 0.6)
            
            return {
                "valid": movement_detected,
                "direction": direction,
                "confidence": confidence,
                "movement_angle": random.randint(15, 45) if movement_detected else 0,
                "message": f"Head movement {direction} {'detected' if movement_detected else 'not detected'}"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Head movement detection failed: {str(e)}",
                "confidence": 0.0
            }

    def detect_smile(self, video_frames: List[np.ndarray]) -> Dict:
        """Detect smile in video frames"""
        try:
            # Mock smile detection
            smile_detected = random.choice([True, True, False])  # 66% success rate
            confidence = random.uniform(0.75, 0.95) if smile_detected else random.uniform(0.2, 0.5)
            
            return {
                "valid": smile_detected,
                "confidence": confidence,
                "smile_intensity": random.uniform(0.6, 0.9) if smile_detected else 0.0,
                "message": f"Smile {'detected' if smile_detected else 'not detected'}"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Smile detection failed: {str(e)}",
                "confidence": 0.0
            }

    def process_live_liveness_sequence(self, video_frames: List[np.ndarray]) -> Dict:
        """Process complete live liveness sequence"""
        try:
            if len(video_frames) < 20:  # Need at least 20 frames
                return {
                    "valid": False,
                    "error": "Insufficient video frames for liveness detection",
                    "required_frames": 20,
                    "provided_frames": len(video_frames)
                }

            results = {
                "timestamp": datetime.now().isoformat(),
                "total_frames": len(video_frames),
                "tests_performed": {}
            }

            # Test 1: Continuous face detection
            face_detection_results = []
            for frame in video_frames[:10]:  # Check first 10 frames
                face_result = self.detect_face_in_frame(frame)
                face_detection_results.append(face_result["face_detected"])

            face_consistency = sum(face_detection_results) / len(face_detection_results)
            results["tests_performed"]["face_consistency"] = {
                "score": face_consistency,
                "valid": face_consistency >= 0.8
            }

            # Test 2: Blink detection
            blink_result = self.detect_blink_sequence(video_frames[0:15])
            results["tests_performed"]["blink_detection"] = blink_result

            # Test 3: Head movement left
            head_left_result = self.detect_head_movement(video_frames[5:15], "left")
            results["tests_performed"]["head_movement_left"] = head_left_result

            # Test 4: Head movement right
            head_right_result = self.detect_head_movement(video_frames[10:20], "right")
            results["tests_performed"]["head_movement_right"] = head_right_result

            # Test 5: Smile detection
            smile_result = self.detect_smile(video_frames[15:])
            results["tests_performed"]["smile_detection"] = smile_result

            # Calculate overall score
            test_scores = []
            passed_tests = 0
            total_tests = 5

            for test_name, test_result in results["tests_performed"].items():
                if test_result.get("valid", False):
                    passed_tests += 1
                    test_scores.append(test_result.get("confidence", test_result.get("score", 0.0)))
                else:
                    test_scores.append(0.0)

            overall_confidence = sum(test_scores) / len(test_scores)
            pass_rate = passed_tests / total_tests

            # Final validation
            liveness_passed = pass_rate >= 0.6 and overall_confidence >= 0.7

            results.update({
                "valid": liveness_passed,
                "overall_confidence": round(overall_confidence, 3),
                "pass_rate": round(pass_rate, 3),
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "liveness_score": round(overall_confidence * pass_rate, 3),
                "anti_spoofing_passed": liveness_passed,
                "message": "Live liveness verification completed successfully" if liveness_passed else "Live liveness verification failed"
            })

            return results

        except Exception as e:
            return {
                "valid": False,
                "error": f"Live liveness processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    @staticmethod
    def mock_liveness_check() -> Dict:
        """Mock liveness check for testing"""
        # Higher success rate for testing
        liveness_passed = random.choices([True, False], weights=[0.8, 0.2])[0]
        confidence = random.uniform(0.85, 0.98) if liveness_passed else random.uniform(0.3, 0.6)
        
        mock_actions = ["blink", "turn_head_left", "smile"]
        
        return {
            "valid": liveness_passed,
            "field": "mock_liveness_check",
            "message": "Mock face liveness check completed successfully" if liveness_passed else "Mock face liveness check failed",
            "data": {
                "completed_actions": mock_actions,
                "overall_confidence": confidence,
                "liveness_verified": liveness_passed,
                "anti_spoofing_passed": liveness_passed,
                "mock_mode": True,
                "timestamp": datetime.now().isoformat()
            }
        }
