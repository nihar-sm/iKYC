"""
Live Interactive Face Liveness Test Suite

This module provides interactive testing where the camera opens for 10 seconds
for each required action (blink, smile, head movements) and validates them in real-time.

Usage:
    python test_face.py
"""

import unittest
import numpy as np
import cv2
import time
import threading
from datetime import datetime
from face_validators import LiveFaceValidators


class LiveInteractiveFaceTest:
    """Interactive live face liveness testing with camera"""
    
    def __init__(self):
        self.validator = LiveFaceValidators()
        self.cap = None
        self.frames_collected = []
        self.current_action = None
        self.action_completed = False
        self.action_start_time = None
        
    def initialize_camera(self):
        """Initialize camera capture"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Could not open camera")
            
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print("✓ Camera initialized successfully")
            return True
            
        except Exception as e:
            print(f"✗ Camera initialization failed: {e}")
            return False
    
    def release_camera(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
            print("✓ Camera released")
    
    def collect_frames_for_action(self, action_name, duration=10):
        """Collect frames for a specific action over the given duration"""
        print(f"\n=== Starting {action_name.upper()} Test ===")
        print(f"You have {duration} seconds to perform: {action_name}")
        print("Press 'q' to quit early or 'c' to mark action as completed")
        
        self.frames_collected = []
        self.current_action = action_name
        self.action_completed = False
        self.action_start_time = time.time()
        
        frame_count = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("✗ Failed to capture frame")
                break
            
            # Store frame for analysis
            self.frames_collected.append(frame.copy())
            frame_count += 1
            
            # Create display frame with instructions
            display_frame = frame.copy()
            elapsed_time = time.time() - self.action_start_time
            remaining_time = max(0, duration - elapsed_time)
            
            # Add text overlay
            cv2.putText(display_frame, f"Action: {action_name.upper()}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Time remaining: {remaining_time:.1f}s", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(display_frame, "Press 'c' when completed, 'q' to quit", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, f"Frames collected: {frame_count}", (10, 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show action-specific instructions
            instructions = self.get_action_instructions(action_name)
            y_offset = 180
            for instruction in instructions:
                cv2.putText(display_frame, instruction, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                y_offset += 20
            
            # Display frame
            cv2.imshow(f'Live Liveness Test - {action_name}', display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("✗ Test quit by user")
                break
            elif key == ord('c'):
                print("✓ Action marked as completed by user")
                self.action_completed = True
                break
            
            # Check time limit
            if elapsed_time >= duration:
                print(f"⏰ Time limit reached ({duration}s)")
                break
        
        cv2.destroyAllWindows()
        
        print(f"📊 Collected {len(self.frames_collected)} frames in {elapsed_time:.2f}s")
        return self.frames_collected
    
    def get_action_instructions(self, action_name):
        """Get specific instructions for each action"""
        instructions = {
            "blink": [
                "🔸 Look directly at the camera",
                "🔸 Blink your eyes naturally 2-3 times",
                "🔸 Keep your face centered in the frame"
            ],
            "turn_head_left": [
                "🔸 Start facing the camera",
                "🔸 Slowly turn your head to the LEFT",
                "🔸 Keep your face visible in the frame"
            ],
            "turn_head_right": [
                "🔸 Start facing the camera", 
                "🔸 Slowly turn your head to the RIGHT",
                "🔸 Keep your face visible in the frame"
            ],
            "smile": [
                "🔸 Look directly at the camera",
                "🔸 Smile naturally and hold for 2-3 seconds",
                "🔸 Keep your face centered in the frame"
            ]
        }
        return instructions.get(action_name, ["🔸 Follow the on-screen instructions"])
    
    def analyze_collected_frames(self, action_name, frames):
        """Analyze the collected frames for the specific action"""
        if len(frames) < 5:
            return {
                "valid": False,
                "error": f"Insufficient frames collected for {action_name} (got {len(frames)}, need at least 5)"
            }
        
        print(f"\n📋 Analyzing {action_name} with {len(frames)} frames...")
        
        # Perform action-specific analysis
        if action_name == "blink":
            result = self.validator.detect_blink_sequence(frames)
        elif action_name == "turn_head_left":
            result = self.validator.detect_head_movement(frames, "left")
        elif action_name == "turn_head_right":
            result = self.validator.detect_head_movement(frames, "right") 
        elif action_name == "smile":
            result = self.validator.detect_smile(frames)
        else:
            result = {"valid": False, "error": f"Unknown action: {action_name}"}
        
        # Add action completion info
        result["action_name"] = action_name
        result["frames_analyzed"] = len(frames)
        result["user_completed"] = self.action_completed
        
        return result
    
    def run_complete_liveness_test(self):
        """Run the complete interactive liveness test"""
        print("="*70)
        print("🎯 INTERACTIVE LIVE FACE LIVENESS TEST")
        print("="*70)
        print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.initialize_camera():
            return False
        
        # Get required actions from the validator
        liveness_init = LiveFaceValidators.initiate_live_liveness_check()
        required_actions = liveness_init["data"]["required_actions"]
        
        print(f"\n📋 Required actions: {', '.join(required_actions)}")
        print("📝 Each action has a 10-second time limit")
        print("🔄 You can press 'c' to complete an action early or 'q' to quit")
        
        input("\nPress Enter to start the test...")
        
        # Results storage
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "session_id": liveness_init["data"]["session_id"],
            "individual_tests": {},
            "all_frames": []
        }
        
        # Perform each action test
        for action in required_actions:
            print(f"\n{'='*50}")
            print(f"🎬 Preparing for {action} test...")
            print("📸 Camera will open in 3 seconds...")
            
            # Countdown
            for i in range(3, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            # Collect frames for this action
            frames = self.collect_frames_for_action(action, duration=10)
            
            if not frames:
                print(f"✗ No frames collected for {action}")
                test_results["individual_tests"][action] = {
                    "valid": False,
                    "error": "No frames collected"
                }
                continue
            
            # Analyze the frames
            analysis_result = self.analyze_collected_frames(action, frames)
            test_results["individual_tests"][action] = analysis_result
            test_results["all_frames"].extend(frames)
            
            # Display results
            if analysis_result["valid"]:
                confidence = analysis_result.get("confidence", 0.0)
                print(f"✅ {action.upper()} TEST PASSED (confidence: {confidence:.3f})")
            else:
                error_msg = analysis_result.get("error", analysis_result.get("message", "Unknown error"))
                print(f"❌ {action.upper()} TEST FAILED: {error_msg}")
            
            # Brief pause between actions
            if action != required_actions[-1]:  # Not the last action
                print("\n⏳ Preparing for next action...")
                time.sleep(2)
        
        # Perform overall analysis
        print(f"\n{'='*50}")
        print("🔍 PERFORMING OVERALL LIVENESS ANALYSIS...")
        
        if len(test_results["all_frames"]) >= 20:
            overall_result = self.validator.process_live_liveness_sequence(test_results["all_frames"])
            test_results["overall_analysis"] = overall_result
        else:
            test_results["overall_analysis"] = {
                "valid": False,
                "error": f"Insufficient total frames for analysis (got {len(test_results['all_frames'])}, need 20+)"
            }
        
        # Display final results
        self.display_final_results(test_results)
        
        self.release_camera()
        return test_results
    
    def display_final_results(self, test_results):
        """Display comprehensive test results"""
        print(f"\n{'='*70}")
        print("📊 COMPREHENSIVE TEST RESULTS")
        print(f"{'='*70}")
        
        # Individual action results
        print("\n🎯 Individual Action Results:")
        passed_actions = 0
        total_actions = len(test_results["individual_tests"])
        
        for action, result in test_results["individual_tests"].items():
            status = "✅ PASS" if result["valid"] else "❌ FAIL"
            confidence = result.get("confidence", 0.0)
            frames = result.get("frames_analyzed", 0)
            user_completed = result.get("user_completed", False)
            
            print(f"   {action.upper():<20} {status} (confidence: {confidence:.3f}) [{frames} frames]")
            if user_completed:
                print(f"   {'':>20} 👤 User marked as completed")
            
            if result["valid"]:
                passed_actions += 1
        
        # Overall analysis results
        print(f"\n🔬 Overall Liveness Analysis:")
        overall = test_results.get("overall_analysis", {})
        
        if overall.get("valid", False):
            print("   ✅ OVERALL LIVENESS: PASSED")
            print(f"   📈 Overall Confidence: {overall['overall_confidence']:.3f}")
            print(f"   📊 Pass Rate: {overall['pass_rate']:.3f}")
            print(f"   🎯 Liveness Score: {overall['liveness_score']:.3f}")
        else:
            error_msg = overall.get("error", "Analysis failed")
            print(f"   ❌ OVERALL LIVENESS: FAILED")
            print(f"   ⚠️  Reason: {error_msg}")
        
        # Summary statistics
        print(f"\n📈 Summary Statistics:")
        print(f"   Actions Passed: {passed_actions}/{total_actions}")
        print(f"   Success Rate: {(passed_actions/total_actions)*100:.1f}%")
        print(f"   Total Frames Collected: {len(test_results.get('all_frames', []))}")
        print(f"   Session ID: {test_results.get('session_id', 'N/A')}")
        
        # Final verdict
        print(f"\n🏆 FINAL VERDICT:")
        if overall.get("valid", False) and passed_actions >= total_actions * 0.6:
            print("   🎉 LIVE FACE LIVENESS VERIFICATION: SUCCESSFUL")
        else:
            print("   ⚠️  LIVE FACE LIVENESS VERIFICATION: FAILED")
            print("   💡 Tip: Ensure good lighting and follow instructions carefully")


class TestBasicFunctionality(unittest.TestCase):
    """Basic unit tests without camera interaction"""
    
    def setUp(self):
        self.validator = LiveFaceValidators()
    
    def test_validator_initialization(self):
        """Test that validator initializes properly"""
        self.assertIsNotNone(self.validator)
        self.assertIsNotNone(self.validator.face_detection)
    
    def test_mock_liveness_check(self):
        """Test mock liveness functionality"""
        result = LiveFaceValidators.mock_liveness_check()
        self.assertIn("valid", result)
        self.assertIn("data", result)
        self.assertTrue(result["data"]["mock_mode"])


def run_interactive_test():
    """Run the interactive camera-based test"""
    tester = LiveInteractiveFaceTest()
    
    print("🎯 Welcome to the Interactive Live Face Liveness Test!")
    print("📹 This test will use your camera to verify live face liveness.")
    print("⚠️  Ensure good lighting and position your face clearly in the camera view.")
    
    choice = input("\nDo you want to run the interactive test? (y/n): ").lower()
    
    if choice in ['y', 'yes']:
        return tester.run_complete_liveness_test()
    else:
        print("Interactive test skipped.")
        return None


def main():
    """Main test runner with options"""
    print("="*70)
    print("🎯 LIVE FACE LIVENESS DETECTION TEST SUITE")
    print("="*70)
    
    print("\nAvailable test modes:")
    print("1. Interactive Camera Test (10 seconds per action)")
    print("2. Basic Unit Tests (no camera)")
    print("3. Both")
    
    choice = input("\nSelect test mode (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        print("\n" + "="*50)
        print("🎬 INTERACTIVE CAMERA TESTS")
        print("="*50)
        interactive_result = run_interactive_test()
    
    if choice in ['2', '3']:
        print("\n" + "="*50)
        print("🧪 BASIC UNIT TESTS")
        print("="*50)
        unittest.main(argv=[''], exit=False, verbosity=2)
    
    print(f"\n{'='*70}")
    print("✅ TEST SUITE COMPLETED")
    print(f"{'='*70}")
    print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
