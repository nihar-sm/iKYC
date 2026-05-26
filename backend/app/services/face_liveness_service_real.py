"""
Real Face Liveness Service with MediaPipe Integration and Face Validators

Combines hand gesture detection with comprehensive face liveness validation
"""

import cv2
import numpy as np
import base64
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import time
import uuid

# Configure logging
logger = logging.getLogger(__name__)

# Global scope variable declaration
MEDIAPIPE_AVAILABLE = False
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    logger.info("✅ MediaPipe successfully imported")
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("❌ MediaPipe not available. Install with: pip install mediapipe")

@dataclass
class LivenessResult:
    """Data class for liveness detection results"""
    is_live: bool
    confidence: float
    liveness_score: float
    challenges_passed: int
    total_challenges: int
    analysis_time: float
    indicators: List[str]
    error_message: str = ""

class RealFaceLivenessDetector:
    """Real face liveness detector with MediaPipe hand gesture recognition"""
    
    def __init__(self):
        """Initialize MediaPipe components"""
        self.mp_hands = None
        self.mp_face_detection = None
        self.hands = None
        self.face_detection = None
        
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_hands = mp.solutions.hands
                self.mp_face_detection = mp.solutions.face_detection
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.6,
                    min_tracking_confidence=0.5
                )
                self.face_detection = self.mp_face_detection.FaceDetection(
                    model_selection=0,
                    min_detection_confidence=0.6
                )
                logger.info("✅ Real Face Liveness Detector initialized with MediaPipe")
            except Exception as e:
                logger.error(f"Failed to initialize MediaPipe: {e}")
                self.mp_hands = None
                self.hands = None
                self.face_detection = None
        else:
            logger.info("⚠️ MediaPipe not available - using enhanced mock detection")

    def initiate_liveness_check(self) -> Dict[str, Any]:
        """Initialize liveness detection session"""
        try:
            session_data = {
                "valid": True,
                "session_id": str(uuid.uuid4()),
                "initialized_at": datetime.now().isoformat(),
                "challenges": {
                    "right_hand_raise": True,
                    "left_hand_raise": True,
                    "face_detection": True
                },
                "status": "ready",
                "instructions": [
                    "Look directly at the camera",
                    "Raise your right hand when prompted",
                    "Raise your left hand when prompted",
                    "Keep your face visible throughout"
                ],
                "mediapipe_available": MEDIAPIPE_AVAILABLE
            }
            
            logger.info("✅ Liveness check session initiated successfully")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to initiate liveness check: {e}")
            return {
                "valid": False,
                "error": f"Liveness initialization failed: {str(e)}",
                "status": "failed",
                "session_id": None,
                "mediapipe_available": MEDIAPIPE_AVAILABLE
            }

    def process_liveness_sequence(self, video_frames: Union[List[str], List[np.ndarray]]) -> Dict[str, Any]:
        """Process video frames to perform face liveness detection"""
        start_time = time.time()
        
        try:
            # Handle different input types
            if isinstance(video_frames, list) and len(video_frames) > 0:
                if isinstance(video_frames[0], str):
                    decoded_frames = self._decode_frames(video_frames)
                else:
                    decoded_frames = video_frames
            else:
                decoded_frames = []
            
            if not decoded_frames:
                return self._create_error_result("No valid frames provided", start_time)
            
            if not MEDIAPIPE_AVAILABLE or not self.face_detection:
                return self._mock_face_liveness_result(decoded_frames, start_time)
            
            # Initialize detection counters
            face_detections = 0
            total_frames = len(decoded_frames)
            
            # Process each frame
            for i, frame in enumerate(decoded_frames):
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    face_results = self.face_detection.process(rgb_frame)
                    if face_results.detections:
                        face_detections += 1
                except Exception as e:
                    logger.warning(f"Frame {i} processing failed: {e}")
                    continue
            
            # Calculate confidence scores
            face_confidence = face_detections / total_frames if total_frames > 0 else 0
            face_liveness_passed = face_confidence >= 0.7
            overall_confidence = face_confidence
            
            # Bonus for sufficient frames
            if total_frames >= 20:
                overall_confidence = min(1.0, overall_confidence + 0.1)
            
            is_live = face_liveness_passed and overall_confidence >= 0.6
            
            result = {
                "valid": is_live,
                "overall_confidence": round(overall_confidence, 3),
                "face_confidence": round(face_confidence, 3),
                "face_detections": face_detections,
                "total_frames": total_frames,
                "verification_type": "face_liveness",
                "analysis_time": round(time.time() - start_time, 3),
                "challenges_passed": 1 if face_liveness_passed else 0,
                "total_challenges": 1,
                "indicators": self._generate_face_indicators(
                    face_liveness_passed, face_detections, total_frames, is_live
                )
            }
            
            logger.info(f"Face liveness analysis completed: {'PASSED' if is_live else 'FAILED'} "
                       f"(confidence: {overall_confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Face liveness sequence processing failed: {e}")
            return self._create_error_result(f"Face liveness processing failed: {str(e)}", start_time)

    def analyze_video_frames(self, video_data: Dict[str, Any]) -> LivenessResult:
        """Analyze video frames for hand gestures - MAIN METHOD FOR HAND DETECTION"""
        start_time = time.time()
        
        try:
            frames = video_data.get('frames', [])
            timestamps = video_data.get('timestamps', [])
            challenge_type = video_data.get('challenge_type', 'standard')
            
            if not frames:
                return self._create_failed_result(start_time, "No video frames provided")
            
            # Decode frames
            decoded_frames = self._decode_frames(frames) if isinstance(frames[0], str) else frames
            if not decoded_frames:
                return self._create_failed_result(start_time, "Frame decoding failed")
            
            logger.info(f"📊 Analyzing {len(decoded_frames)} frames for hand gestures...")
            
            if not MEDIAPIPE_AVAILABLE or not self.hands:
                return self._enhanced_mock_detection(decoded_frames, start_time)
            
            # Analyze gestures based on challenge type
            if challenge_type == "timed_hand_gestures" and timestamps:
                return self._analyze_timed_gestures(decoded_frames, timestamps, start_time)
            else:
                return self._analyze_standard_gestures(decoded_frames, start_time)
                
        except Exception as e:
            logger.error(f"Hand gesture analysis failed: {e}")
            return self._create_failed_result(start_time, str(e))

    def _analyze_timed_gestures(self, frames: List[np.ndarray], 
                               timestamps: List[float], start_time: float) -> LivenessResult:
        """Analyze frames with timing validation for sustained gestures"""
        right_hand_periods = []
        left_hand_periods = []
        face_detections = 0
        
        for i, frame in enumerate(frames):
            timestamp = timestamps[i] if i < len(timestamps) else 0
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Hand detection
                hands_result = self.hands.process(rgb_frame)
                right_hand_raised = False
                left_hand_raised = False
                
                if hands_result.multi_hand_landmarks and hands_result.multi_handedness:
                    for hand_landmarks, handedness in zip(hands_result.multi_hand_landmarks,
                                                         hands_result.multi_handedness):
                        if self._is_hand_raised(hand_landmarks):
                            hand_label = handedness.classification[0].label
                            if hand_label == 'Right':
                                right_hand_raised = True
                            elif hand_label == 'Left':
                                left_hand_raised = True
                
                if right_hand_raised:
                    right_hand_periods.append(timestamp)
                if left_hand_raised:
                    left_hand_periods.append(timestamp)
                
                # Face detection
                if self.face_detection:
                    face_result = self.face_detection.process(rgb_frame)
                    if face_result.detections:
                        face_detections += 1
                        
            except Exception as e:
                logger.warning(f"Frame processing error: {e}")
                continue
        
        # Analyze sustained periods
        right_hand_sustained = self._has_sustained_period(right_hand_periods, 5.0)
        left_hand_sustained = self._has_sustained_period(left_hand_periods, 5.0)
        face_consistently_present = face_detections >= (len(frames) * 0.7)
        
        challenges_passed = sum([right_hand_sustained, left_hand_sustained])
        base_confidence = challenges_passed / 2.0
        
        # Apply bonuses/penalties
        timing_bonus = 0.1 if challenges_passed == 2 else 0
        face_bonus = 0.1 if face_consistently_present else -0.2
        confidence = min(1.0, max(0.0, base_confidence + timing_bonus + face_bonus))
        
        is_live = challenges_passed >= 2 and face_consistently_present
        
        indicators = self._generate_timed_indicators(
            right_hand_sustained, left_hand_sustained, face_consistently_present, len(frames)
        )
        
        return LivenessResult(
            is_live=is_live,
            confidence=round(confidence, 3),
            liveness_score=round(confidence, 3),
            challenges_passed=challenges_passed,
            total_challenges=2,
            analysis_time=round(time.time() - start_time, 3),
            indicators=indicators
        )

    def _analyze_standard_gestures(self, frames: List[np.ndarray], start_time: float) -> LivenessResult:
        """Standard gesture analysis without timing requirements"""
        right_hand_detected = self._detect_hand_raise(frames, 'Right')
        left_hand_detected = self._detect_hand_raise(frames, 'Left')
        face_detected = self._detect_face_presence(frames)
        
        challenges_passed = sum([right_hand_detected, left_hand_detected])
        base_confidence = challenges_passed / 2.0
        
        # Apply face detection bonus/penalty
        face_bonus = 0.1 if face_detected else -0.2
        confidence = min(1.0, max(0.0, base_confidence + face_bonus))
        
        is_live = challenges_passed >= 1 and face_detected
        
        indicators = self._generate_standard_indicators(
            right_hand_detected, left_hand_detected, face_detected, frames
        )
        
        return LivenessResult(
            is_live=is_live,
            confidence=round(confidence, 3),
            liveness_score=round(confidence, 3),
            challenges_passed=challenges_passed,
            total_challenges=2,
            analysis_time=round(time.time() - start_time, 3),
            indicators=indicators
        )

    def _is_hand_raised(self, hand_landmarks) -> bool:
        """Check if hand is raised based on wrist and finger positions"""
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        return (wrist.y > middle_tip.y) and (wrist.y > index_tip.y)

    def _has_sustained_period(self, timestamps: List[float], required_duration: float) -> bool:
        """Check if timestamps show a sustained period of required duration"""
        if len(timestamps) < 2:
            return False
        
        consecutive_periods = []
        current_start = timestamps[0]
        current_end = timestamps[0]
        
        for i in range(1, len(timestamps)):
            if timestamps[i] - timestamps[i-1] <= 0.5:  # Allow 0.5s gaps
                current_end = timestamps[i]
            else:
                consecutive_periods.append(current_end - current_start)
                current_start = timestamps[i]
                current_end = timestamps[i]
        
        consecutive_periods.append(current_end - current_start)
        return any(period >= required_duration for period in consecutive_periods)

    def _detect_hand_raise(self, frames: List[np.ndarray], hand_type: str) -> bool:
        """Generic hand raise detection"""
        if not MEDIAPIPE_AVAILABLE or not self.hands:
            return False
        
        hand_detections = 0
        total_hand_frames = 0
        
        for frame in frames:
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                
                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                         results.multi_handedness):
                        if handedness.classification[0].label == hand_type:
                            total_hand_frames += 1
                            if self._is_hand_raised(hand_landmarks):
                                hand_detections += 1
            except Exception as e:
                logger.warning(f"Hand detection error: {e}")
                continue
        
        if total_hand_frames > 0:
            detection_ratio = hand_detections / total_hand_frames
            return detection_ratio >= 0.25
        return False

    def _detect_face_presence(self, frames: List[np.ndarray]) -> bool:
        """Detect consistent face presence"""
        if not MEDIAPIPE_AVAILABLE or not self.face_detection:
            return True  # Assume face present in mock mode
        
        face_detections = 0
        sampled_frames = frames[::2]  # Sample every other frame for efficiency
        
        for frame in sampled_frames:
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_detection.process(rgb_frame)
                if results.detections:
                    face_detections += 1
            except Exception as e:
                logger.warning(f"Face detection error: {e}")
                continue
        
        threshold = max(1, len(sampled_frames) * 0.5)
        return face_detections >= threshold

    def _decode_frames(self, frames: List[str]) -> List[np.ndarray]:
        """Decode base64 frames to numpy arrays"""
        decoded_frames = []
        for i, frame_data in enumerate(frames):
            try:
                if frame_data.startswith('data:image'):
                    # Handle data URL format
                    frame_data = frame_data.split(',')[1]
                
                frame_bytes = base64.b64decode(frame_data)
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                if frame is not None and frame.size > 0:
                    decoded_frames.append(frame)
            except Exception as e:
                logger.warning(f"Failed to decode frame {i}: {e}")
                continue
        return decoded_frames

    def _create_error_result(self, error_msg: str, start_time: float) -> Dict[str, Any]:
        """Create error result for liveness sequence"""
        return {
            "valid": False,
            "overall_confidence": 0.0,
            "error": error_msg,
            "verification_type": "face_liveness",
            "analysis_time": round(time.time() - start_time, 3)
        }

    def _create_failed_result(self, start_time: float, error_msg: str) -> LivenessResult:
        """Create a failed result with error message"""
        return LivenessResult(
            is_live=False,
            confidence=0.0,
            liveness_score=0.0,
            challenges_passed=0,
            total_challenges=2,
            analysis_time=round(time.time() - start_time, 3),
            indicators=[f"❌ {error_msg}"],
            error_message=error_msg
        )

    def _generate_face_indicators(self, face_passed: bool, detections: int,
                                total_frames: int, is_live: bool) -> List[str]:
        """Generate indicators for face liveness"""
        indicators = []
        if face_passed:
            indicators.append(f"✅ Face detected in {detections}/{total_frames} frames")
        else:
            indicators.append(f"❌ Face not consistently detected ({detections}/{total_frames} frames)")
        
        indicators.append(f"📹 Processed {total_frames} frames for face liveness")
        indicators.append(f"🎯 Face liveness: {'PASSED' if is_live else 'FAILED'}")
        return indicators

    def _generate_timed_indicators(self, right_sustained: bool, left_sustained: bool,
                                 face_present: bool, frame_count: int) -> List[str]:
        """Generate indicators for timed gesture analysis"""
        indicators = []
        if right_sustained:
            indicators.append("✅ Right hand raised and sustained for 5+ seconds")
        else:
            indicators.append("❌ Right hand not sustained for required 5 seconds")
        
        if left_sustained:
            indicators.append("✅ Left hand raised and sustained for 5+ seconds")
        else:
            indicators.append("❌ Left hand not sustained for required 5 seconds")
        
        if face_present:
            indicators.append("✅ Face consistently visible throughout challenges")
        else:
            indicators.append("❌ Face not consistently visible during test")
        
        indicators.append(f"📹 Analyzed {frame_count} frames with timing validation")
        return indicators

    def _generate_standard_indicators(self, right_hand: bool, left_hand: bool,
                                    face: bool, frames: List) -> List[str]:
        """Generate detailed analysis indicators for standard gestures"""
        indicators = []
        
        if right_hand:
            indicators.append("✅ Right hand raise gesture detected successfully")
        else:
            indicators.append("❌ Right hand raise gesture not detected clearly")
        
        if left_hand:
            indicators.append("✅ Left hand raise gesture detected successfully")
        else:
            indicators.append("❌ Left hand raise gesture not detected clearly")
        
        if face:
            indicators.append("✅ Face presence confirmed throughout recording")
        else:
            indicators.append("❌ Face not consistently visible")
        
        indicators.append(f"📹 Processed {len(frames)} video frames")
        
        if len(frames) < 15:
            indicators.append("⚠️ Recording may be too short - record for 6-8 seconds")
        
        return indicators

    def _mock_face_liveness_result(self, frames: List[np.ndarray], start_time: float) -> Dict[str, Any]:
        """Mock face liveness result when MediaPipe is not available"""
        import random
        
        frame_count = len(frames)
        has_sufficient_frames = frame_count >= 15
        
        # Simulate realistic success rates
        if has_sufficient_frames:
            is_live = random.random() > 0.2
            confidence = random.uniform(0.75, 0.95) if is_live else random.uniform(0.2, 0.5)
        else:
            is_live = random.random() > 0.7
            confidence = random.uniform(0.3, 0.6) if is_live else random.uniform(0.1, 0.4)
        
        return {
            "valid": is_live,
            "overall_confidence": round(confidence, 3),
            "face_confidence": round(confidence, 3),
            "verification_type": "face_liveness_mock",
            "analysis_time": round(time.time() - start_time, 3),
            "indicators": [
                "🎭 DEMO MODE: Face liveness simulation",
                f"📹 Mock analysis of {frame_count} frames",
                f"✨ Demo face liveness: {'PASSED' if is_live else 'FAILED'}"
            ],
            "mock_mode": True
        }

    def _enhanced_mock_detection(self, frames: List[np.ndarray], start_time: float) -> LivenessResult:
        """Enhanced mock detection for testing without MediaPipe"""
        import random
        
        frame_count = len(frames)
        has_sufficient_frames = frame_count >= 15
        
        # Simulate realistic success rates based on frame count
        success_rate = 0.8 if has_sufficient_frames else 0.3
        is_live = random.random() < success_rate
        confidence = random.uniform(0.7, 0.95) if is_live else random.uniform(0.2, 0.5)
        challenges_passed = 2 if is_live else random.randint(0, 1)
        
        indicators = [
            "🎭 DEMO MODE: Right hand gesture simulation",
            "🎭 DEMO MODE: Left hand gesture simulation",
            "🎭 DEMO MODE: Face detection simulation",
            f"📹 Analyzed {frame_count} frames in demo mode"
        ]
        
        if not has_sufficient_frames:
            indicators.append("⚠️ Recording appears too short for reliable analysis")
        
        result_msg = "✨ Demo: Liveness verification PASSED" if is_live else "❌ Demo: Liveness verification FAILED"
        indicators.append(result_msg)
        
        return LivenessResult(
            is_live=is_live,
            confidence=round(confidence, 3),
            liveness_score=round(confidence, 3),
            challenges_passed=challenges_passed,
            total_challenges=2,
            analysis_time=round(time.time() - start_time, 3),
            indicators=indicators
        )


class LiveFaceValidators:
    """Mock LiveFaceValidators class for compatibility"""
    
    def __init__(self):
        self.initialized = True
        logger.info("✅ LiveFaceValidators initialized (mock)")

    def initiate_live_liveness_check(self) -> Dict[str, Any]:
        """Mock initiate liveness check"""
        return {
            "valid": True,
            "session_id": str(uuid.uuid4()),
            "status": "ready",
            "mock_mode": True,
            "timestamp": datetime.now().isoformat()
        }

    def process_live_liveness_sequence(self, video_frames: Union[List[str], List[np.ndarray]]) -> Dict[str, Any]:
        """Mock process liveness sequence"""
        import random
        
        frame_count = len(video_frames) if video_frames else 0
        has_frames = frame_count > 0
        
        is_live = random.random() > 0.3 if has_frames else False
        confidence = random.uniform(0.7, 0.95) if is_live else random.uniform(0.2, 0.5)
        
        return {
            "valid": is_live,
            "overall_confidence": round(confidence, 3),
            "liveness_score": round(confidence, 3),
            "verification_type": "face_validation_mock",
            "frame_count": frame_count,
            "mock_mode": True
        }


class FaceLivenessServiceReal:
    """Enhanced Face Liveness Service with integrated validators"""
    
    def __init__(self):
        # Try to import face validators, use mock if not available
        try:
            from face_validators import LiveFaceValidators as ExternalValidators
            self.validator = ExternalValidators()
            logger.info("✅ External LiveFaceValidators loaded")
        except ImportError:
            logger.warning("face_validators not found, using mock validator")
            self.validator = LiveFaceValidators()
        
        self.hand_detector = RealFaceLivenessDetector()
        logger.info("✅ FaceLivenessServiceReal initialized with both validators")

    def initiate_liveness_check(self) -> Dict[str, Any]:
        """Start liveness verification process"""
        return self.validator.initiate_live_liveness_check()

    def process_liveness_sequence(self, video_frames: Union[List[str], List[np.ndarray]]) -> Dict[str, Any]:
        """Process collected frames for liveness verification"""
        return self.validator.process_live_liveness_sequence(video_frames)

    def process_hand_gesture_sequence(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process hand gesture liveness verification - FIXED: Single implementation"""
        try:
            if not hasattr(self.hand_detector, 'analyze_video_frames'):
                return {
                    "valid": False,
                    "error": "Hand gesture analysis method not available",
                    "verification_type": "hand_gesture_liveness"
                }
            
            result = self.hand_detector.analyze_video_frames(video_data)
            
            # Convert LivenessResult to dict format
            return {
                "valid": result.is_live,
                "overall_confidence": result.confidence,
                "liveness_score": result.liveness_score,
                "challenges_passed": result.challenges_passed,
                "total_challenges": result.total_challenges,
                "analysis_time": result.analysis_time,
                "indicators": result.indicators,
                "error_message": result.error_message,
                "verification_type": "hand_gesture_liveness"
            }
            
        except Exception as e:
            logger.error(f"Hand gesture processing failed: {e}")
            return {
                "valid": False,
                "error": f"Hand gesture analysis failed: {str(e)}",
                "verification_type": "hand_gesture_liveness",
                "analysis_time": 0.0
            }

    def process_combined_liveness(self, face_frames: Union[List[str], List[np.ndarray]],
                                 hand_gesture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process both face and hand gesture liveness verification"""
        try:
            # Process face liveness
            face_result = self.process_liveness_sequence(face_frames)
            
            # Process hand gesture liveness
            hand_result = self.process_hand_gesture_sequence(hand_gesture_data)
            
            # Combine results with weighted scoring
            face_confidence = face_result.get("overall_confidence", 0.0)
            hand_confidence = hand_result.get("overall_confidence", 0.0)
            combined_confidence = (face_confidence * 0.6) + (hand_confidence * 0.4)
            
            both_valid = face_result.get("valid", False) and hand_result.get("valid", False)
            
            return {
                "valid": both_valid,
                "overall_confidence": round(combined_confidence, 3),
                "face_liveness": face_result,
                "hand_gesture_liveness": hand_result,
                "combined_score": round(combined_confidence, 3),
                "verification_type": "combined_liveness",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Combined liveness processing failed: {e}")
            return {
                "valid": False,
                "error": f"Combined liveness analysis failed: {str(e)}",
                "verification_type": "combined_liveness",
                "timestamp": datetime.now().isoformat()
            }

    def validate_kyc_decision(self, liveness_result: Dict[str, Any]) -> Dict[str, Any]:
        """Make KYC pass/fail decision based on liveness results"""
        timestamp = datetime.now().isoformat()
        
        if not liveness_result.get("valid", False):
            return {
                "kyc_status": "FAILED",
                "reason": "Liveness verification failed",
                "confidence": liveness_result.get("overall_confidence", 0.0),
                "verification_type": liveness_result.get("verification_type", "unknown"),
                "timestamp": timestamp
            }
        
        # Extract key metrics
        overall_confidence = liveness_result.get("overall_confidence", 0.0)
        verification_type = liveness_result.get("verification_type", "standard")
        
        # Enhanced decision matrix based on verification type
        if verification_type == "combined_liveness":
            return self._evaluate_combined_kyc(overall_confidence, verification_type, timestamp)
        else:
            return self._evaluate_standard_kyc(overall_confidence, verification_type, timestamp)

    def _evaluate_combined_kyc(self, confidence: float, verification_type: str, 
                             timestamp: str) -> Dict[str, Any]:
        """Evaluate KYC for combined liveness verification"""
        if confidence >= 0.85:
            return {
                "kyc_status": "PASSED",
                "confidence": confidence,
                "verification_type": verification_type,
                "risk_level": "LOW",
                "timestamp": timestamp
            }
        elif confidence >= 0.7:
            return {
                "kyc_status": "REVIEW_REQUIRED",
                "confidence": confidence,
                "verification_type": verification_type,
                "risk_level": "MEDIUM",
                "reason": "Manual review recommended - moderate confidence",
                "timestamp": timestamp
            }
        else:
            return {
                "kyc_status": "FAILED",
                "reason": "Insufficient combined liveness confidence",
                "confidence": confidence,
                "verification_type": verification_type,
                "risk_level": "HIGH",
                "timestamp": timestamp
            }

    def _evaluate_standard_kyc(self, confidence: float, verification_type: str, 
                             timestamp: str) -> Dict[str, Any]:
        """Evaluate KYC for standard liveness verification"""
        if confidence >= 0.8:
            return {
                "kyc_status": "PASSED",
                "confidence": confidence,
                "verification_type": verification_type,
                "risk_level": "LOW",
                "timestamp": timestamp
            }
        elif confidence >= 0.6:
            return {
                "kyc_status": "REVIEW_REQUIRED",
                "confidence": confidence,
                "verification_type": verification_type,
                "risk_level": "MEDIUM",
                "reason": "Manual review recommended - moderate confidence",
                "timestamp": timestamp
            }
        else:
            return {
                "kyc_status": "FAILED",
                "reason": "Insufficient liveness confidence",
                "confidence": confidence,
                "verification_type": verification_type,
                "risk_level": "HIGH",
                "timestamp": timestamp
            }


# Global service instances
real_liveness_detector = RealFaceLivenessDetector()
face_liveness_service = FaceLivenessServiceReal()

# For backwards compatibility
face_liveness_service_real = face_liveness_service

if __name__ == "__main__":
    print("Face Liveness Service initialized successfully")
