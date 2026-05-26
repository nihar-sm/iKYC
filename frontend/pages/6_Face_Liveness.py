import sys
import os
import streamlit as st
import base64
import cv2
import numpy as np
import time
from datetime import datetime, timedelta
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
import av

# Fix import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from utils.api_client import api_client
except ImportError:
    st.error("Cannot import api_client. Please check project structure.")
    st.stop()

try:
    from face_validators import LiveFaceValidators
    FACE_VALIDATORS_AVAILABLE = True
except ImportError:
    FACE_VALIDATORS_AVAILABLE = False
    st.warning("Face validators not available. Only hand gesture detection will work.")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    st.error("MediaPipe not available. Please install: pip install mediapipe")

# WebRTC Configuration
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

class LivenessVideoTransformer(VideoTransformerBase):
    """Enhanced video transformer with both face validation and hand gesture detection"""
    
    def __init__(self):
        # Face validation setup
        if FACE_VALIDATORS_AVAILABLE:
            self.validator = LiveFaceValidators()
        self.frames_collected = []
        self.current_action = None
        
        # Hand gesture detection setup (existing functionality)
        self.hand_frames = []
        self.state = 'waiting_to_start'
        self.right_hand_start_time = None
        self.left_hand_start_time = None
        self.right_hand_completed = False
        self.left_hand_completed = False
        self.current_time = 0
        self.challenge_start_time = None
        self.max_frames = 600  # 20 seconds at 30fps
        self.frame_count = 0
        
        # Detection mode
        self.detection_mode = 'face_validation'  # 'face_validation' or 'hand_gestures'
        
        # MediaPipe setup for hand detection
        if MEDIAPIPE_AVAILABLE:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )

    def set_current_action(self, action):
        """Set current face validation action"""
        self.current_action = action
        
    def set_detection_mode(self, mode):
        """Set detection mode: 'face_validation' or 'hand_gestures'"""
        self.detection_mode = mode
        if mode == 'hand_gestures':
            self.reset_hand_detection()
        else:
            self.reset_face_validation()

    def reset_face_validation(self):
        """Reset face validation state"""
        self.frames_collected = []
        self.current_action = None

    def reset_hand_detection(self):
        """Reset hand gesture detection state"""
        self.state = 'waiting_to_start'
        self.hand_frames = []
        self.right_hand_start_time = None
        self.left_hand_start_time = None
        self.right_hand_completed = False
        self.left_hand_completed = False
        self.frame_count = 0

    def transform(self, frame):
        """Main video processing function"""
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1
        current_timestamp = time.time()
        
        if self.detection_mode == 'face_validation':
            return self._process_face_validation(img)
        else:
            return self._process_hand_gestures(img, current_timestamp)

    def _process_face_validation(self, img):
        """Process frame for face validation"""
        # Collect frames for analysis
        self.frames_collected.append(img.copy())
        
        # Add overlay instructions
        if self.current_action:
            cv2.putText(img, f"Action: {self.current_action.upper()}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Add action-specific instructions
            instructions = self._get_action_instructions(self.current_action)
            y_offset = 70
            for instruction in instructions:
                cv2.putText(img, instruction, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 25
        else:
            cv2.putText(img, "Select an action to begin", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        # Add frame count
        cv2.putText(img, f"Frames collected: {len(self.frames_collected)}", 
                   (10, img.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def _process_hand_gestures(self, img, current_timestamp):
        """Process frame for hand gesture detection (existing functionality)"""
        # Store frame if recording
        if self.state in ['right_hand', 'left_hand'] and len(self.hand_frames) < self.max_frames:
            self.hand_frames.append({
                'image': img.copy(),
                'timestamp': current_timestamp,
                'frame_number': self.frame_count
            })

        # Process with MediaPipe if available
        right_hand_raised = False
        left_hand_raised = False
        
        if MEDIAPIPE_AVAILABLE:
            rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                    middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                    
                    hand_raised = wrist.y > middle_tip.y
                    if handedness.classification[0].label == 'Right' and hand_raised:
                        right_hand_raised = True
                    elif handedness.classification[0].label == 'Left' and hand_raised:
                        left_hand_raised = True

        # State machine logic (existing functionality)
        if self.state == 'waiting_to_start':
            cv2.putText(img, "Click START to begin hand gesture test", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        elif self.state == 'right_hand':
            if right_hand_raised:
                if self.right_hand_start_time is None:
                    self.right_hand_start_time = current_timestamp
                elapsed = current_timestamp - self.right_hand_start_time
                remaining = max(0, 5.0 - elapsed)
                
                if elapsed >= 5.0:
                    self.right_hand_completed = True
                    self.state = 'left_hand'
                    self.left_hand_start_time = None
                    cv2.putText(img, "RIGHT HAND COMPLETED! Now raise LEFT HAND", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    cv2.putText(img, f"HOLD RIGHT HAND UP: {remaining:.1f}s remaining", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    # Progress bar
                    progress = int((elapsed / 5.0) * 300)
                    cv2.rectangle(img, (10, 80), (310, 100), (100, 100, 100), 2)
                    cv2.rectangle(img, (12, 82), (12 + progress, 98), (0, 255, 0), -1)
            else:
                self.right_hand_start_time = None
                cv2.putText(img, "RAISE YOUR RIGHT HAND and hold for 5 seconds", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            
            cv2.putText(img, "Challenge 1/2: RIGHT HAND", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        elif self.state == 'left_hand':
            if left_hand_raised:
                if self.left_hand_start_time is None:
                    self.left_hand_start_time = current_timestamp
                elapsed = current_timestamp - self.left_hand_start_time
                remaining = max(0, 5.0 - elapsed)
                
                if elapsed >= 5.0:
                    self.left_hand_completed = True
                    self.state = 'completed'
                    cv2.putText(img, "BOTH CHALLENGES COMPLETED! Click ANALYZE", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    cv2.putText(img, f"HOLD LEFT HAND UP: {remaining:.1f}s remaining", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    # Progress bar
                    progress = int((elapsed / 5.0) * 300)
                    cv2.rectangle(img, (10, 80), (310, 100), (100, 100, 100), 2)
                    cv2.rectangle(img, (12, 82), (12 + progress, 98), (0, 255, 0), -1)
            else:
                self.left_hand_start_time = None
                cv2.putText(img, "RAISE YOUR LEFT HAND and hold for 5 seconds", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            
            cv2.putText(img, "Challenge 2/2: LEFT HAND", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        elif self.state == 'completed':
            cv2.putText(img, "CHALLENGES COMPLETED! Click ANALYZE LIVENESS", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Always show instruction at bottom
        cv2.putText(img, "Keep your face visible throughout", (10, img.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def _get_action_instructions(self, action_name):
        """Get specific instructions for each face validation action"""
        instructions = {
            "blink": [
                "Look directly at the camera",
                "Blink your eyes naturally 2-3 times",
                "Keep your face centered"
            ],
            "turn_head_left": [
                "Start facing the camera",
                "Slowly turn your head to the LEFT",
                "Keep your face visible"
            ],
            "turn_head_right": [
                "Start facing the camera", 
                "Slowly turn your head to the RIGHT",
                "Keep your face visible"
            ],
            "smile": [
                "Look directly at the camera",
                "Smile naturally for 2-3 seconds",
                "Keep your face centered"
            ]
        }
        return instructions.get(action_name, ["Follow the instructions"])

    def start_hand_challenge(self):
        """Start hand gesture challenge"""
        self.state = 'right_hand'
        self.hand_frames = []
        self.right_hand_start_time = None
        self.left_hand_start_time = None
        self.right_hand_completed = False
        self.left_hand_completed = False
        self.challenge_start_time = time.time()
        self.frame_count = 0

    def get_face_frames(self):
        """Get collected face validation frames"""
        return self.frames_collected.copy()

    def get_hand_frames(self):
        """Get recorded hand gesture frames"""
        if self.state == 'completed' and self.hand_frames:
            return self.hand_frames
        return None

    def is_hand_challenge_completed(self):
        """Check if hand gesture challenge is completed"""
        return self.state == 'completed'

def make_kyc_decision(result):
    """Make KYC pass/fail decision based on liveness results"""
    if not result.get("valid", False):
        return {"kyc_status": "FAILED", "reason": "Liveness verification failed"}
    
    overall_confidence = result.get("overall_confidence", 0.0)
    pass_rate = result.get("pass_rate", overall_confidence)
    
    if overall_confidence >= 0.8 and pass_rate >= 0.7:
        return {"kyc_status": "PASSED", "confidence": overall_confidence}
    elif overall_confidence >= 0.6 and pass_rate >= 0.6:
        return {"kyc_status": "REVIEW_REQUIRED", "confidence": overall_confidence}
    else:
        return {"kyc_status": "FAILED", "reason": "Insufficient liveness confidence"}

def show_face_liveness_page():
    """Enhanced Face Liveness with both validation types"""
    st.header("👁️ Enhanced Face Liveness Verification")
    
    if not st.session_state.get('processing_results'):
        st.warning("⚠️ Please complete AI processing first")
        if st.button("Go to AI Processing"):
            st.session_state['step'] = 4
            st.rerun()
        return

    # Detection mode selector
    st.subheader("🎯 Choose Verification Method")
    detection_mode = st.selectbox(
        "Select verification type:",
        ["Face Validation (Blink, Smile, Head Movement)", "Hand Gesture Detection", "Combined Verification"],
        key="detection_mode_selector"
    )

    # Initialize video processor
    if 'video_processor' not in st.session_state:
        st.session_state['video_processor'] = LivenessVideoTransformer()
    
    processor = st.session_state['video_processor']

    if detection_mode.startswith("Face Validation"):
        show_face_validation_interface(processor)
    elif detection_mode.startswith("Hand Gesture"):
        show_hand_gesture_interface(processor)
    else:
        show_combined_verification_interface(processor)

def show_face_validation_interface(processor):
    """Show face validation interface"""
    processor.set_detection_mode('face_validation')
    
    st.info("🎥 Complete the required face validation actions")
    
    # Initialize face validation session
    if FACE_VALIDATORS_AVAILABLE:
        if 'liveness_session' not in st.session_state:
            validator = LiveFaceValidators()
            st.session_state.liveness_session = validator.initiate_live_liveness_check()
        
        # Display required actions
        required_actions = st.session_state.liveness_session["data"]["required_actions"]
        st.info(f"Required actions: {', '.join(required_actions)}")
        
        # Action selector
        current_action = st.selectbox("Select current action:", required_actions)
        processor.set_current_action(current_action)
    else:
        st.error("Face validators not available!")
        return

    # Video streaming
    st.subheader("📹 Live Camera Feed")
    webrtc_ctx = webrtc_streamer(
        key="face-validation-liveness",
        video_transformer_factory=lambda: processor,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    # Control buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset Frames", use_container_width=True):
            processor.reset_face_validation()
            st.info("Face validation reset")
    
    with col2:
        frames_count = len(processor.get_face_frames())
        st.metric("Frames Collected", frames_count)
    
    with col3:
        if st.button("🔍 Analyze Face Liveness", type="primary", use_container_width=True):
            frames = processor.get_face_frames()
            if len(frames) > 0:
                with st.spinner("Processing face liveness verification..."):
                    try:
                        if FACE_VALIDATORS_AVAILABLE:
                            result = processor.validator.process_live_liveness_sequence(frames)
                            
                            if result["valid"]:
                                st.success("✅ Face Liveness Verification PASSED!")
                                st.metric("Overall Confidence", f"{result['overall_confidence']:.3f}")
                                st.metric("Pass Rate", f"{result['pass_rate']:.3f}")
                                
                                # KYC Decision
                                kyc_decision = make_kyc_decision(result)
                                st.markdown(f"### KYC Status: **{kyc_decision['kyc_status']}**")
                                
                                # Store results
                                st.session_state['face_liveness_results'] = result
                                st.session_state['kyc_decision'] = kyc_decision
                            else:
                                st.error("❌ Face Liveness Verification FAILED")
                                st.write(result.get("error", "Unknown error"))
                        else:
                            st.error("Face validators not available")
                    except Exception as e:
                        st.error(f"❌ Analysis error: {str(e)}")
            else:
                st.error("❌ No frames collected")

def show_hand_gesture_interface(processor):
    """Show hand gesture interface (existing functionality)"""
    processor.set_detection_mode('hand_gestures')
    
    st.info("🎥 Timed hand gesture liveness verification")
    
    # Instructions
    st.subheader("📋 Challenge Instructions")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤚 Timed Challenges:")
        st.markdown("1. **Raise RIGHT hand** and hold for **5 seconds**")
        st.markdown("2. **Lower right hand, raise LEFT hand** and hold for **5 seconds**")
        st.markdown("3. **Keep your face visible** throughout the entire test")
    
    with col2:
        st.markdown("### 💡 Important:")
        st.markdown("• Each gesture must be held for exactly 5 seconds")
        st.markdown("• Progress bars will show your timing")
        st.markdown("• Don't lower your hand until instructed")
        st.markdown("• Complete both challenges to proceed")

    # Video streaming
    st.subheader("📹 Live Camera Feed")
    webrtc_ctx = webrtc_streamer(
        key="hand-gesture-liveness",
        video_transformer_factory=lambda: processor,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    # Control buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 START CHALLENGE", type="primary", use_container_width=True):
            processor.start_hand_challenge()
            st.success("Challenge started! Raise your RIGHT hand first!")
    
    with col2:
        if st.button("🔄 RESET", use_container_width=True):
            processor.reset_hand_detection()
            st.info("Challenge reset. Click START to begin.")
    
    with col3:
        # Show status
        if processor.state == 'waiting_to_start':
            st.info("Ready to start")
        elif processor.state == 'right_hand':
            st.warning("🤚 Right hand challenge")
        elif processor.state == 'left_hand':
            st.warning("🤚 Left hand challenge")
        elif processor.state == 'completed':
            st.success("✅ Challenges completed!")
    
    with col4:
        if processor.is_hand_challenge_completed():
            if st.button("🔍 ANALYZE LIVENESS", type="primary", use_container_width=True):
                recorded_frames = processor.get_hand_frames()
                if recorded_frames:
                    with st.spinner("👁️ Analyzing timed liveness challenges..."):
                        try:
                            encoded_data = encode_timed_frames_for_api(recorded_frames)
                            result = api_client.analyze_liveness(encoded_data)
                            
                            if result and 'liveness_result' in result:
                                st.session_state['hand_liveness_results'] = result
                                display_liveness_results(result['liveness_result'])
                            else:
                                st.error("❌ Hand gesture liveness analysis failed")
                        except Exception as e:
                            st.error(f"❌ Analysis error: {str(e)}")
                else:
                    st.error("❌ No recorded frames available")

def show_combined_verification_interface(processor):
    """Show combined verification interface"""
    st.info("🎯 Combined Face + Hand Gesture Verification")
    st.markdown("This mode combines both face validation and hand gesture detection for enhanced security.")
    
    # Step-by-step process
    st.subheader("📋 Verification Steps")
    
    # Step 1: Face Validation
    with st.expander("Step 1: Face Validation", expanded=True):
        show_face_validation_interface(processor)
    
    # Step 2: Hand Gesture Detection  
    with st.expander("Step 2: Hand Gesture Detection", expanded=False):
        show_hand_gesture_interface(processor)
    
    # Combined Analysis
    if st.session_state.get('face_liveness_results') and st.session_state.get('hand_liveness_results'):
        st.subheader("🔍 Combined Analysis Results")
        
        face_result = st.session_state['face_liveness_results']
        hand_result = st.session_state['hand_liveness_results']['liveness_result']
        
        # Calculate combined score
        face_confidence = face_result.get('overall_confidence', 0.0)
        hand_confidence = hand_result.get('confidence', 0.0)
        combined_score = (face_confidence * 0.6) + (hand_confidence * 0.4)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Face Validation", f"{face_confidence:.1%}")
        with col2:
            st.metric("Hand Gestures", f"{hand_confidence:.1%}")
        with col3:
            st.metric("Combined Score", f"{combined_score:.1%}")
        
        # Final decision
        if face_result.get('valid', False) and hand_result.get('is_live', False):
            st.success("✅ Combined Verification PASSED!")
            st.markdown("### KYC Status: **APPROVED**")
        else:
            st.error("❌ Combined Verification FAILED")
            st.markdown("### KYC Status: **REJECTED**")

def encode_timed_frames_for_api(recorded_frames):
    """Encode timed video frames with metadata for API transmission"""
    encoded_frames = []
    timestamps = []
    
    for frame_data in recorded_frames[::2]:  # Sample every 2nd frame
        try:
            frame = frame_data['image']
            timestamp = frame_data['timestamp']
            
            resized_frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            encoded_frame = base64.b64encode(buffer).decode('utf-8')
            
            encoded_frames.append(encoded_frame)
            timestamps.append(timestamp)
        except Exception as e:
            continue
    
    return {
        "frames": encoded_frames,
        "timestamps": timestamps,
        "frame_count": len(encoded_frames),
        "original_fps": 30,
        "challenge_type": "timed_hand_gestures",
        "total_duration": timestamps[-1] - timestamps[0] if timestamps else 0
    }

def display_liveness_results(liveness_result):
    """Display timed liveness analysis results"""
    st.subheader("📊 Hand Gesture Liveness Results")
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ LIVE" if liveness_result.get('is_live', False) else "❌ NOT LIVE"
        st.metric("Verification Status", status)
    
    with col2:
        confidence = liveness_result.get('confidence', 0)
        st.metric("Confidence Score", f"{confidence:.1%}")
    
    with col3:
        challenges_passed = liveness_result.get('challenges_passed', 0)
        total_challenges = liveness_result.get('total_challenges', 2)
        st.metric("Challenges Passed", f"{challenges_passed}/{total_challenges}")
    
    # Detailed indicators
    with st.expander("📋 Detailed Analysis"):
        indicators = liveness_result.get('indicators', [])
        for indicator in indicators:
            if "✅" in indicator:
                st.success(indicator)
            elif "❌" in indicator:
                st.error(indicator)
            elif "⚠️" in indicator:
                st.warning(indicator)
            else:
                st.info(indicator)
    
    analysis_time = liveness_result.get('analysis_time', 0)
    if analysis_time > 0:
        st.caption(f"⏱️ Analysis completed in {analysis_time:.1f} seconds")

# Main execution
if __name__ == "__main__":
    st.set_page_config(page_title="Enhanced Liveness Verification", layout="wide")
    
    if 'step' not in st.session_state:
        st.session_state['step'] = 5
    
    if 'processing_results' not in st.session_state:
        st.session_state['processing_results'] = {"status": "completed"}
    
    show_face_liveness_page()
    
    # Navigation buttons
    if st.session_state.get('face_liveness_results') or st.session_state.get('hand_liveness_results'):
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Back to Processing", use_container_width=True):
                st.session_state['step'] = 4
                st.rerun()
        
        with col2:
            if st.button("✅ Continue to Results", type="primary", use_container_width=True):
                st.session_state['step'] = 6
                st.rerun()
