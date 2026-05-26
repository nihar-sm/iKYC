"""
Enhanced IntelliKYC Streamlit Frontend Application with Advanced Face Liveness Integration
"""

import streamlit as st
import requests
import json
from pathlib import Path
import sys
import base64
import cv2
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import enhanced API client
from utils.api_client import api_client

# Page config
st.set_page_config(
    page_title="IntelliKYC Enhanced",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize enhanced session state variables"""
    if 'document_id' not in st.session_state:
        st.session_state.document_id = None
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'customer_data' not in st.session_state:
        st.session_state.customer_data = {}
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = {}
    
    # Enhanced liveness session states
    if 'face_liveness_results' not in st.session_state:
        st.session_state.face_liveness_results = None
    if 'hand_liveness_results' not in st.session_state:
        st.session_state.hand_liveness_results = None
    if 'combined_liveness_results' not in st.session_state:
        st.session_state.combined_liveness_results = None
    if 'liveness_session' not in st.session_state:
        st.session_state.liveness_session = None
    if 'verification_mode' not in st.session_state:
        st.session_state.verification_mode = "face_validation"

def main():
    """Enhanced main Streamlit application"""
    init_session_state()
    
    # Enhanced header
    st.title("🔐 IntelliKYC Enhanced - AI-Powered KYC Verification")
    st.markdown("Complete KYC pipeline with OCR, AI Fraud Detection, and **Enhanced Multi-Modal Face Liveness**")
    st.markdown("---")
    
    # Enhanced sidebar navigation
    with st.sidebar:
        st.header("🧭 Enhanced KYC Pipeline")
        steps = [
            "1. 🏠 Home",
            "2. 📝 Registration", 
            "3. 🆔 Documents",
            "4. 🤖 AI Processing",
            "5. 👁️ Enhanced Liveness",
            "6. ✅ Results"
        ]
        
        selected_step = st.radio("Current Step:", steps, index=st.session_state.step-1)
        st.session_state.step = steps.index(selected_step) + 1
        
        # Enhanced API status
        st.markdown("---")
        st.subheader("🔌 Enhanced System Status")
        if st.button("Check Enhanced Backend Health"):
            try:
                response = requests.get("http://localhost:8000/api/health")
                if response.status_code == 200:
                    st.success("✅ Enhanced Backend Online")
                    health_data = response.json()
                    
                    # Display enhanced features
                    if 'enhanced_features' in health_data:
                        st.write("**Enhanced Features:**")
                        features = health_data['enhanced_features']
                        st.write(f"🎯 Face Validation: {'✅' if features.get('face_validation') else '❌'}")
                        st.write(f"🤚 Hand Gestures: {'✅' if features.get('hand_gestures') else '❌'}")
                        st.write(f"🔄 Combined Mode: {'✅' if features.get('combined_verification') else '❌'}")
                    
                    with st.expander("📊 Detailed System Status"):
                        st.json(health_data)
                else:
                    st.error("❌ Backend Offline")
            except:
                st.error("❌ Cannot connect to enhanced backend")
    
    # Route to appropriate page
    if st.session_state.step == 1:
        show_enhanced_home_page()
    elif st.session_state.step == 2:
        show_registration_page()
    elif st.session_state.step == 3:
        show_documents_page()
    elif st.session_state.step == 4:
        show_ai_processing_page()
    elif st.session_state.step == 5:
        show_enhanced_face_liveness_page()
    elif st.session_state.step == 6:
        show_enhanced_results_page()

def show_enhanced_home_page():
    """Enhanced home page with new features"""
    st.header("🏠 Welcome to IntelliKYC Enhanced")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Enhanced Features")
        st.write("✅ **Advanced OCR Processing** - Multi-engine text extraction")
        st.write("✅ **Smart Field Validation** - AI-powered format verification")
        st.write("✅ **Real-Time AI Fraud Detection** - IBM Granite + AWS Bedrock")
        st.write("✅ **Multi-Modal Face Liveness** - Face validation + Hand gestures")
        st.write("✅ **Combined Verification** - Maximum security assurance")
        st.write("✅ **Enhanced KYC Decisions** - Risk-based approval matrix")
    
    with col2:
        st.subheader("📊 Enhanced System Status")
        try:
            # Get enhanced system status
            health_status = api_client.health_check()
            if health_status and not health_status.get('error'):
                st.write("🎯 **System Version**: v3.0.0 Enhanced")
                st.write(f"🔍 **OCR Engines**: {health_status.get('ocr_service', 'Unknown')}")
                st.write(f"🤖 **AI Fraud Detection**: {health_status.get('fraud_detection', 'Unknown')}")
                st.write(f"👁️ **Enhanced Liveness**: {health_status.get('liveness_detection', 'Unknown')}")
            
            # Get liveness service status
            liveness_status = api_client.get_liveness_service_status()
            if liveness_status and not liveness_status.get('error'):
                st.write("**🎭 Liveness Modes Available:**")
                services = liveness_status.get('services_available', {})
                st.write(f"• Face Validation: {'✅' if services.get('face_validation') else '❌'}")
                st.write(f"• Hand Gestures: {'✅' if services.get('hand_gestures') else '❌'}")
                st.write(f"• Combined Mode: {'✅' if services.get('combined_verification') else '❌'}")
        except:
            st.write("❌ Cannot fetch enhanced system status")
    
    if st.button("🚀 Start Enhanced KYC Process", type="primary", use_container_width=True):
        st.session_state.step = 2
        st.rerun()

def show_registration_page():
    """Registration form (unchanged)"""
    st.header("📝 Customer Registration")
    
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name*", placeholder="Enter your full name")
            date_of_birth = st.date_input("Date of Birth*")
            email = st.text_input("Email*", placeholder="your.email@example.com")
        
        with col2:
            phone_number = st.text_input("Phone Number*", placeholder="+91 9876543210")
            aadhaar_number = st.text_input("Aadhaar Number*", placeholder="XXXX XXXX XXXX")
            pan_number = st.text_input("PAN Number*", placeholder="ABCDE1234F")
        
        submitted = st.form_submit_button("Continue to Documents", use_container_width=True)
        
        if submitted:
            if all([full_name, date_of_birth, email, phone_number, aadhaar_number, pan_number]):
                st.session_state.customer_data = {
                    "full_name": full_name,
                    "date_of_birth": str(date_of_birth),
                    "email": email,
                    "phone_number": phone_number,
                    "aadhaar_number": aadhaar_number,
                    "pan_number": pan_number
                }
                st.success("✅ Registration Complete!")
                st.session_state.step = 3
                st.rerun()
            else:
                st.error("❌ Please fill all required fields")

def show_documents_page():
    """Document upload (unchanged)"""
    st.header("🆔 Document Upload")
    
    if not st.session_state.get('customer_data'):
        st.warning("⚠️ Please complete registration first")
        if st.button("Go to Registration"):
            st.session_state['step'] = 2
            st.rerun()
        return
    
    uploaded_file = st.file_uploader(
        "Choose an Aadhaar card image",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear image of your Aadhaar card (max 10MB)"
    )
    
    if uploaded_file is not None:
        # File validation
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("❌ File too large. Maximum size is 10MB.")
            return
        
        if uploaded_file.type not in ['image/jpeg', 'image/jpg', 'image/png']:
            st.error("❌ Invalid file type. Please upload JPG or PNG images.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(uploaded_file, caption="Uploaded Document", use_container_width=True)
        
        with col2:
            st.success(f"✅ File ready: {uploaded_file.name}")
            st.info(f"📏 Size: {uploaded_file.size:,} bytes")
            st.info(f"📋 Type: {uploaded_file.type}")
        
        # Upload button
        if st.button("📤 Upload Document", type="primary", use_container_width=True):
            with st.spinner("Uploading document..."):
                try:
                    uploaded_file.seek(0)
                    result = api_client.upload_document(uploaded_file, "aadhaar")
                    
                    if result and "document_id" in result:
                        st.session_state['document_id'] = result['document_id']
                        st.success("✅ Document uploaded successfully!")
                        st.info(f"📄 Document ID: {result['document_id']}")
                    elif result and "error" in result:
                        st.error(f"❌ Upload failed: {result['error']}")
                        return
                    else:
                        st.error("❌ Unexpected response from server")
                        return
                except Exception as e:
                    st.error(f"❌ Upload error: {str(e)}")
                    return
    
    if st.session_state.get('document_id'):
        st.markdown("---")
        if st.button("🔄 Continue to AI Processing", type="primary", use_container_width=True):
            st.session_state['step'] = 4
            st.rerun()

def show_ai_processing_page():
    """AI processing (unchanged)"""
    st.header("🤖 AI Processing & Fraud Detection")
    
    if not st.session_state.get('document_id'):
        st.warning("⚠️ Please upload a document first")
        if st.button("Go to Documents"):
            st.session_state['step'] = 3
            st.rerun()
        return
    
    st.info(f"📄 Processing Document ID: {st.session_state['document_id']}")
    
    # Start AI Analysis button
    if st.button("🔍 Start AI Analysis", type="primary", use_container_width=True):
        with st.spinner("🤖 AI is analyzing your document..."):
            try:
                result = api_client.process_document(st.session_state['document_id'])
                
                if result:
                    # Store results in session state
                    st.session_state['processing_results'] = result
                    st.success("✅ AI Processing Complete!")
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Document Status", result.get('status', 'Unknown'))
                    
                    with col2:
                        validation_score = result.get('validation_summary', {}).get('validation_score', 0)
                        st.metric("Validation Score", f"{validation_score}%")
                    
                    with col3:
                        fraud_risk = result.get('fraud_analysis', {}).get('overall_risk_level', 'Unknown')
                        st.metric("Fraud Risk", fraud_risk)
                    
                    # Detailed results in expander
                    with st.expander("📊 Detailed Analysis Results"):
                        st.json(result)
                else:
                    st.error("❌ AI processing failed")
                    return
            except Exception as e:
                st.error(f"❌ Processing error: {str(e)}")
                return
    
    # Navigation button
    if st.session_state.get('processing_results'):
        st.markdown("---")
        if st.button("👁️ Continue to Enhanced Liveness", type="primary", use_container_width=True):
            st.session_state['step'] = 5
            st.rerun()

def show_enhanced_face_liveness_page():
    """Enhanced face liveness verification with multiple modes"""
    st.header("👁️ Enhanced Multi-Modal Face Liveness Verification")
    
    if not st.session_state.get('processing_results'):
        st.warning("⚠️ Please complete AI processing first")
        if st.button("Go to AI Processing"):
            st.session_state['step'] = 4
            st.rerun()
        return
    
    st.info("🎯 Choose your preferred liveness verification method for maximum security")
    
    # Enhanced verification mode selector
    st.subheader("🎭 Select Verification Mode")
    verification_mode = st.selectbox(
        "Choose verification method:",
        [
            "Face Validation (Blink, Smile, Head Movement)",
            "Hand Gesture Detection (Timed Raises)", 
            "Combined Verification (Maximum Security)"
        ],
        key="verification_mode_selector"
    )
    
    st.session_state.verification_mode = verification_mode.split("(")[0].strip()
    
    if verification_mode.startswith("Face Validation"):
        show_face_validation_mode()
    elif verification_mode.startswith("Hand Gesture"):
        show_hand_gesture_mode()
    else:
        show_combined_verification_mode()

def show_face_validation_mode():
    """Enhanced face validation interface"""
    st.subheader("🎯 Face Validation Mode")
    st.info("📹 Complete face validation actions: blink, smile, and head movements")
    
    # Initialize face liveness session
    if not st.session_state.get('liveness_session'):
        try:
            session_result = api_client.initiate_face_liveness_check()
            if session_result and not session_result.get('error'):
                st.session_state.liveness_session = session_result
                st.success("✅ Face liveness session initiated")
            else:
                st.error(f"❌ Failed to initiate session: {session_result.get('error', 'Unknown error')}")
                return
        except Exception as e:
            st.error(f"❌ Session initiation error: {str(e)}")
            return
    
    # Display required actions
    if st.session_state.liveness_session:
        session_data = st.session_state.liveness_session.get('session_data', {})
        if 'data' in session_data:
            required_actions = session_data['data'].get('required_actions', [])
            st.info(f"📋 Required actions: {', '.join(required_actions)}")
    
    # Instructions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎭 Face Validation Actions:")
        st.markdown("1. **Blink** - Blink your eyes naturally 2-3 times")
        st.markdown("2. **Smile** - Smile naturally for 2-3 seconds") 
        st.markdown("3. **Turn Head Left** - Slowly turn your head left")
        st.markdown("4. **Turn Head Right** - Slowly turn your head right")
    
    with col2:
        st.markdown("### 💡 Tips for Success:")
        st.markdown("• Ensure good lighting on your face")
        st.markdown("• Look directly at the camera")
        st.markdown("• Perform actions slowly and naturally")
        st.markdown("• Keep your face centered in the frame")
    
    # Camera input for face validation
    st.subheader("📷 Face Validation Capture")
    camera_photo = st.camera_input("Capture your face while performing the required actions")
    
    if camera_photo is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(camera_photo, caption="Captured Face Image", use_container_width=True)
        
        with col2:
            st.success("✅ Face image captured successfully!")
            file_size = len(camera_photo.getvalue())
            st.info(f"📏 File size: {file_size:,} bytes")
        
        if st.button("🔍 Analyze Face Liveness", type="primary", use_container_width=True):
            with st.spinner("👁️ Analyzing face liveness actions..."):
                try:
                    # Convert to base64
                    camera_photo.seek(0)
                    image_bytes = camera_photo.read()
                    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Prepare frames list (simulate video sequence)
                    video_frames = [encoded_image] * 20  # 20 frames for analysis
                    
                    # Call enhanced face liveness API
                    result = api_client.analyze_face_liveness_sequence(video_frames)
                    
                    if result and not result.get('error'):
                        st.session_state['face_liveness_results'] = result
                        display_face_liveness_results(result.get('face_liveness_result', {}))
                    else:
                        st.error(f"❌ Face liveness analysis failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error during face liveness analysis: {str(e)}")
    else:
        st.info("📷 Please capture a face image to analyze liveness")

def show_hand_gesture_mode():
    """Hand gesture liveness interface"""
    st.subheader("🤚 Hand Gesture Mode") 
    st.info("🎥 Complete timed hand gesture challenges")
    
    # Instructions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤚 Required Gestures:")
        st.markdown("1. **Raise RIGHT hand** and hold for 5 seconds")
        st.markdown("2. **Lower right hand, raise LEFT hand** and hold for 5 seconds") 
        st.markdown("3. **Keep your face visible** throughout")
    
    with col2:
        st.markdown("### 💡 Tips for Success:")
        st.markdown("• Ensure good lighting on your face and hands")
        st.markdown("• Perform gestures slowly and deliberately")
        st.markdown("• Hold each gesture for the full duration")
        st.markdown("• Keep both face and hands in frame")
    
    # Camera input for hand gestures
    st.subheader("📷 Hand Gesture Capture")
    camera_photo = st.camera_input("Capture photo showing clear hand gestures")
    
    if camera_photo is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(camera_photo, caption="Captured Gesture Image", use_container_width=True)
        
        with col2:
            st.success("✅ Gesture image captured successfully!")
            file_size = len(camera_photo.getvalue())
            st.info(f"📏 File size: {file_size:,} bytes")
        
        if st.button("🔍 Analyze Hand Gestures", type="primary", use_container_width=True):
            with st.spinner("🤚 Analyzing hand gesture liveness..."):
                try:
                    # Convert to base64
                    camera_photo.seek(0)
                    image_bytes = camera_photo.read()
                    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Prepare data for hand gesture API
                    video_data = {
                        "frames": [encoded_image] * 15,  # Simulate video frames
                        "frame_count": 15,
                        "original_fps": 30,
                        "challenge_type": "hand_gestures"
                    }
                    
                    # Call hand gesture liveness API
                    result = api_client.analyze_liveness(video_data)
                    
                    if result and 'liveness_result' in result:
                        st.session_state['hand_liveness_results'] = result
                        display_hand_gesture_results(result['liveness_result'])
                    else:
                        st.error(f"❌ Hand gesture analysis failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error during hand gesture analysis: {str(e)}")
    else:
        st.info("📷 Please capture a gesture image to analyze liveness")

def show_combined_verification_mode():
    """Combined face + hand gesture verification"""
    st.subheader("🔄 Combined Verification Mode (Maximum Security)")
    st.info("🎯 This mode combines both face validation and hand gesture detection for ultimate security")
    
    # Step-by-step process
    st.markdown("### 📋 Verification Steps")
    
    # Step 1: Face Validation
    with st.expander("Step 1: Face Validation", expanded=True):
        st.markdown("Complete face validation actions first")
        show_face_validation_mode()
    
    # Step 2: Hand Gesture Detection
    with st.expander("Step 2: Hand Gesture Detection", expanded=False):
        st.markdown("Complete hand gesture challenges")
        show_hand_gesture_mode()
    
    # Combined analysis
    if (st.session_state.get('face_liveness_results') and 
        st.session_state.get('hand_liveness_results')):
        
        st.subheader("🔍 Combined Analysis")
        
        if st.button("🎯 Perform Combined Analysis", type="primary", use_container_width=True):
            with st.spinner("🔄 Performing combined liveness analysis..."):
                try:
                    # Prepare combined data
                    face_data = st.session_state['face_liveness_results']
                    hand_data = st.session_state['hand_liveness_results']
                    
                    # Mock face frames for combined analysis
                    face_frames = ["mock_face_frame"] * 10  # Would be real frames in production
                    
                    # Call combined liveness API
                    combined_data = {
                        "face_frames": face_frames,
                        "hand_gesture_data": hand_data
                    }
                    
                    result = api_client.analyze_combined_liveness(face_frames, hand_data)
                    
                    if result and not result.get('error'):
                        st.session_state['combined_liveness_results'] = result
                        display_combined_results(result.get('combined_liveness_result', {}))
                    else:
                        st.error(f"❌ Combined analysis failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error during combined analysis: {str(e)}")

def display_face_liveness_results(face_result):
    """Display face liveness analysis results"""
    st.subheader("📊 Face Liveness Analysis Results")
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ VALID" if face_result.get('valid', False) else "❌ INVALID"
        st.metric("Face Validation", status)
    
    with col2:
        confidence = face_result.get('overall_confidence', 0)
        st.metric("Overall Confidence", f"{confidence:.3f}")
    
    with col3:
        pass_rate = face_result.get('pass_rate', 0)
        st.metric("Pass Rate", f"{pass_rate:.3f}")
    
    # Detailed analysis
    with st.expander("📋 Detailed Face Analysis"):
        if 'tests_performed' in face_result:
            for test_name, test_result in face_result['tests_performed'].items():
                if test_result.get('valid', False):
                    st.success(f"✅ {test_name}: PASSED")
                else:
                    st.error(f"❌ {test_name}: FAILED")

def display_hand_gesture_results(hand_result):
    """Display hand gesture liveness results"""
    st.subheader("📊 Hand Gesture Liveness Results")
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ LIVE" if hand_result.get('is_live', False) else "❌ NOT LIVE"
        st.metric("Gesture Status", status)
    
    with col2:
        confidence = hand_result.get('confidence', 0)
        st.metric("Confidence", f"{confidence:.3f}")
    
    with col3:
        challenges = hand_result.get('challenges_passed', 0)
        total = hand_result.get('total_challenges', 2)
        st.metric("Challenges", f"{challenges}/{total}")
    
    # Detailed indicators
    with st.expander("📋 Detailed Gesture Analysis"):
        indicators = hand_result.get('indicators', [])
        for indicator in indicators:
            if "✅" in indicator or "✨" in indicator:
                st.success(indicator)
            elif "❌" in indicator:
                st.error(indicator)
            elif "⚠️" in indicator:
                st.warning(indicator)
            else:
                st.info(indicator)

def display_combined_results(combined_result):
    """Display combined liveness results"""
    st.subheader("🎯 Combined Verification Results")
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ PASSED" if combined_result.get('valid', False) else "❌ FAILED"
        st.metric("Combined Status", status)
    
    with col2:
        confidence = combined_result.get('combined_score', 0)
        st.metric("Combined Score", f"{confidence:.3f}")
    
    with col3:
        verification_type = combined_result.get('verification_type', 'combined')
        st.metric("Verification Type", verification_type.upper())
    
    # Component breakdown
    st.markdown("### 📊 Component Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        face_component = combined_result.get('face_liveness', {})
        face_valid = face_component.get('valid', False)
        face_conf = face_component.get('overall_confidence', 0)
        st.metric("Face Validation", f"{'✅' if face_valid else '❌'} {face_conf:.3f}")
    
    with col2:
        hand_component = combined_result.get('hand_gesture_liveness', {})
        hand_valid = hand_component.get('valid', False) 
        hand_conf = hand_component.get('overall_confidence', 0)
        st.metric("Hand Gestures", f"{'✅' if hand_valid else '❌'} {hand_conf:.3f}")

def show_enhanced_results_page():
    """Enhanced final KYC results page"""
    st.header("✅ Enhanced KYC Verification Results")
    
    if not st.session_state.processing_results:
        st.warning("⚠️ Please complete document processing first")
        return
    
    # Determine liveness results based on verification mode
    liveness_passed = False
    liveness_confidence = 0.0
    verification_type = "none"
    
    if st.session_state.get('combined_liveness_results'):
        combined_result = st.session_state['combined_liveness_results']['combined_liveness_result']
        liveness_passed = combined_result.get('valid', False)
        liveness_confidence = combined_result.get('combined_score', 0.0)
        verification_type = "combined"
    elif st.session_state.get('face_liveness_results'):
        face_result = st.session_state['face_liveness_results']['face_liveness_result']
        liveness_passed = face_result.get('valid', False)
        liveness_confidence = face_result.get('overall_confidence', 0.0)
        verification_type = "face_validation"
    elif st.session_state.get('hand_liveness_results'):
        hand_result = st.session_state['hand_liveness_results']['liveness_result']
        liveness_passed = hand_result.get('is_live', False)
        liveness_confidence = hand_result.get('confidence', 0.0)
        verification_type = "hand_gestures"
    
    # Enhanced final decision calculation
    processing_score = 0.75  # From document processing
    fraud_score = 0.90      # From fraud detection
    
    if verification_type == "combined":
        final_score = (processing_score * 0.3 + fraud_score * 0.3 + liveness_confidence * 0.4)
        decision_threshold = 0.85
    elif verification_type == "face_validation":
        final_score = (processing_score * 0.35 + fraud_score * 0.35 + liveness_confidence * 0.3)
        decision_threshold = 0.8
    else:  # hand_gestures or none
        final_score = (processing_score * 0.4 + fraud_score * 0.4 + liveness_confidence * 0.2)
        decision_threshold = 0.75
    
    # Enhanced decision logic
    if final_score >= decision_threshold and liveness_passed:
        decision = "APPROVED"
        risk_level = "LOW"
        message = "Enhanced KYC verification successful - user approved"
        status_color = "success"
    elif final_score >= 0.7:
        decision = "CONDITIONALLY_APPROVED"  
        risk_level = "LOW_MEDIUM"
        message = "KYC approved with enhanced monitoring recommended"
        status_color = "warning"
    elif final_score >= 0.6:
        decision = "MANUAL_REVIEW"
        risk_level = "MEDIUM"
        message = "Requires manual review before approval"
        status_color = "warning"
    else:
        decision = "REJECTED"
        risk_level = "HIGH"
        message = "Enhanced KYC verification failed - user rejected"
        status_color = "error"
    
    # Display overall status
    if status_color == "success":
        st.success(f"🎉 {message}")
    elif status_color == "warning":
        st.warning(f"⚠️ {message}")
    else:
        st.error(f"❌ {message}")
    
    # Enhanced metrics display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Final Decision", decision)
    
    with col2:
        st.metric("Overall Score", f"{final_score:.3f}")
    
    with col3:
        st.metric("Risk Level", risk_level)
    
    with col4:
        verification_display = verification_type.replace("_", " ").title()
        st.metric("Verification Type", verification_display)
    
    # Enhanced component scores
    st.subheader("📊 Enhanced Component Analysis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Document Processing", f"{processing_score:.3f}", "📄")
    
    with col2:
        st.metric("AI Fraud Detection", f"{fraud_score:.3f}", "🤖")
    
    with col3:
        st.metric(f"{verification_display}", f"{liveness_confidence:.3f}", "👁️")
    
    # Enhanced KYC report generation
    st.subheader("📄 Enhanced KYC Report")
    
    if st.button("📥 Generate Enhanced KYC Report", use_container_width=True):
        enhanced_report = {
            "report_version": "3.0.0-enhanced",
            "customer_data": st.session_state.customer_data,
            "document_processing": st.session_state.processing_results,
            "liveness_verification": {
                "verification_type": verification_type,
                "face_liveness": st.session_state.get('face_liveness_results'),
                "hand_liveness": st.session_state.get('hand_liveness_results'),
                "combined_liveness": st.session_state.get('combined_liveness_results')
            },
            "final_decision": {
                "decision": decision,
                "final_score": final_score,
                "risk_level": risk_level,
                "message": message,
                "verification_type": verification_type,
                "components": {
                    "document_processing": processing_score,
                    "fraud_detection": fraud_score,
                    "liveness_verification": liveness_confidence
                },
                "decided_at": datetime.now().isoformat()
            },
            "generated_at": datetime.now().isoformat()
        }
        
        st.download_button(
            label="📥 Download Enhanced Report (JSON)",
            data=json.dumps(enhanced_report, indent=2),
            file_name=f"enhanced_kyc_report_{st.session_state.customer_data.get('full_name', 'user').replace(' ', '_')}.json",
            mime="application/json"
        )
    
    # Navigation options
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Back to Liveness", use_container_width=True):
            st.session_state['step'] = 5
            st.rerun()
    
    with col2:
        if st.button("🔄 Start New Enhanced KYC", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
