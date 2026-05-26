"""
Main Validation Orchestrator with Face Liveness as Final Step
"""

from typing import Dict, List, Optional
from datetime import datetime
import sys
import os
import uuid

# Import validators
from validators.personal_validators import PersonalValidators
from validators.identity_validators import IdentityValidators
from validators.contact_validators import ContactValidators
from validators.face_validators import LiveFaceValidators
from utils.common_utils import ValidationUtils, MockRedisClient

class KYCValidationOrchestrator:
    """Main orchestrator for complete KYC validation process with Face Liveness"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client or MockRedisClient()
        self.validation_results = {}
        self.current_step = 0
        self.total_steps = 6  # Updated: 6 steps including face liveness
        self.session_id = None

    def initialize_kyc_session(self, customer_data: Dict) -> Dict:
        """Initialize KYC validation session"""
        self.session_id = str(uuid.uuid4())
        session_info = {
            'session_id': self.session_id,
            'customer_data': customer_data,
            'started_at': datetime.now().isoformat(),
            'current_step': 0,
            'total_steps': self.total_steps,
            'status': 'INITIALIZED'
        }
        
        # Store session in Redis
        try:
            session_key = f"kyc_session:{self.session_id}"
            import json
            self.redis_client.set(session_key, json.dumps(session_info), ex=3600)
        except:
            pass
        
        return ValidationUtils.create_validation_response(
            valid=True,
            field="kyc_session",
            message="KYC session initialized successfully",
            data=session_info
        )

    def validate_personal_information(self, full_name: str, date_of_birth: str) -> Dict:
        """Step 1: Validate personal information"""
        print("👤 Step 1: Validating Personal Information...")
        self.current_step = 1
        
        results = {
            "step": 1,
            "step_name": "personal_information",
            "validations": {}
        }
        
        # Validate full name
        name_result = PersonalValidators.validate_full_name(full_name)
        results["validations"]["full_name"] = name_result
        
        # Validate date of birth
        dob_result = PersonalValidators.validate_date_of_birth(date_of_birth)
        results["validations"]["date_of_birth"] = dob_result
        
        # Overall step result
        results["step_valid"] = name_result["valid"] and dob_result["valid"]
        results["step_message"] = "Personal information validation completed"
        
        if not results["step_valid"]:
            errors = []
            if not name_result["valid"]:
                errors.append(f"Name: {name_result['error']}")
            if not dob_result["valid"]:
                errors.append(f"DOB: {dob_result['error']}")
            results["step_message"] = f"Personal validation failed: {'; '.join(errors)}"
        
        self.validation_results["personal"] = results
        return results

    def validate_identity_documents(self, aadhaar_number: str, pan_number: str) -> Dict:
        """Step 2: Validate identity documents"""
        print("🆔 Step 2: Validating Identity Documents...")
        self.current_step = 2
        
        results = {
            "step": 2,
            "step_name": "identity_documents",
            "validations": {}
        }
        
        # Validate Aadhaar
        aadhaar_result = IdentityValidators.validate_aadhaar(aadhaar_number, self.redis_client)
        results["validations"]["aadhaar"] = aadhaar_result
        
        # Validate PAN
        pan_result = IdentityValidators.validate_pan(pan_number, self.redis_client)
        results["validations"]["pan"] = pan_result
        
        # Overall step result
        results["step_valid"] = aadhaar_result["valid"] and pan_result["valid"]
        results["step_message"] = "Identity documents validation completed"
        
        self.validation_results["identity"] = results
        return results

    def validate_contact_information(self, phone_number: str) -> Dict:
        """Step 3: Validate contact information and generate OTP"""
        print("📞 Step 3: Validating Contact Information...")
        self.current_step = 3
        
        results = {
            "step": 3,
            "step_name": "contact_information",
            "validations": {}
        }
        
        # Validate phone number
        phone_result = ContactValidators.validate_phone_number(phone_number)
        results["validations"]["phone"] = phone_result
        
        # Generate OTP if phone is valid
        if phone_result["valid"]:
            otp_result = ContactValidators.generate_otp(phone_number, self.redis_client)
            results["validations"]["otp_generation"] = otp_result
            results["step_valid"] = otp_result["valid"]
            results["otp_generated"] = True
        else:
            results["step_valid"] = False
            results["otp_generated"] = False
            
        results["step_message"] = "Contact information validation completed"
        self.validation_results["contact"] = results
        return results

    def verify_otp(self, phone_number: str, otp_input: str) -> Dict:
        """Step 4: Verify OTP for contact validation"""
        print("📱 Step 4: Verifying OTP...")
        self.current_step = 4
        
        otp_result = ContactValidators.verify_otp(phone_number, otp_input, self.redis_client)
        
        # Update contact validation results
        if "contact" in self.validation_results:
            self.validation_results["contact"]["validations"]["otp_verification"] = otp_result
            self.validation_results["contact"]["otp_verified"] = otp_result["valid"]
            
        return otp_result

    def document_verification(self, aadhaar_image_data: bytes = None, pan_image_data: bytes = None) -> Dict:
        """Step 5: AI-powered document verification"""
        print("📄 Step 5: AI Document Verification...")
        self.current_step = 5
        
        results = {
            "step": 5,
            "step_name": "document_verification",
            "validations": {}
        }
        
        # Mock AI document processing (replace with actual AI integration)
        if aadhaar_image_data:
            aadhaar_ai_result = {
                "valid": True,
                "confidence": 0.95,
                "fraud_score": 0.1,
                "extracted_fields": {
                    "name": "Extracted Name",
                    "aadhaar_number": "123456789012"
                }
            }
            results["validations"]["aadhaar_ai"] = aadhaar_ai_result
        
        if pan_image_data:
            pan_ai_result = {
                "valid": True,
                "confidence": 0.92,
                "fraud_score": 0.15,
                "extracted_fields": {
                    "name": "Extracted Name",
                    "pan_number": "ABCDE1234F"
                }
            }
            results["validations"]["pan_ai"] = pan_ai_result
        
        results["step_valid"] = True
        results["step_message"] = "Document verification completed successfully"
        
        self.validation_results["document_verification"] = results
        return results

    def validate_face_liveness(self, mock_mode: bool = True) -> Dict:
        """Step 6: FINAL STEP - Live Face Liveness Verification"""
        print("👁️ Step 6: FINAL - Live Face Liveness Verification...")
        self.current_step = 6
        
        results = {
            "step": 6,
            "step_name": "face_liveness_verification", 
            "validations": {},
            "is_final_step": True
        }
        
        if mock_mode:
            # Mock liveness check for testing
            liveness_result = FaceValidators.mock_liveness_check()
            results["validations"]["liveness_check"] = liveness_result
            results["step_valid"] = liveness_result["valid"]
            results["step_message"] = "Face liveness verification completed (mock mode)"
        else:
            # Real liveness check initiation
            liveness_initiation = FaceValidators.initiate_liveness_check()
            results["validations"]["liveness_initiation"] = liveness_initiation
            results["step_valid"] = False
            results["step_message"] = "Real liveness check requires camera integration"
        
        # Store results
        self.validation_results["face_liveness"] = results
        
        # If this step passes, KYC is COMPLETE
        if results["step_valid"]:
            self._finalize_kyc_verification()
            
        return results

    def _finalize_kyc_verification(self):
        """Finalize KYC verification when all steps including face liveness pass"""
        print("✅ FINALIZING KYC VERIFICATION...")
        
        if self.session_id:
            final_status = {
                'session_id': self.session_id,
                'status': 'COMPLETED',
                'kyc_status': 'VERIFIED',
                'completed_at': datetime.now().isoformat(),
                'all_steps_passed': True,
                'final_verification': 'APPROVED',
                'face_liveness_verified': True
            }
            
            try:
                session_key = f"kyc_session:{self.session_id}"
                import json
                self.redis_client.set(session_key, json.dumps(final_status), ex=86400 * 30)
            except:
                pass

    def get_overall_validation_status(self) -> Dict:
        """Get comprehensive KYC validation status"""
        required_steps = ["personal", "identity", "contact", "document_verification", "face_liveness"]
        completed_steps = []
        failed_steps = []
        
        for step in required_steps:
            if step in self.validation_results:
                step_result = self.validation_results[step]
                if step_result.get("step_valid", False):
                    # Additional check for contact - OTP must be verified
                    if step == "contact":
                        if step_result.get("otp_verified", False):
                            completed_steps.append(step)
                        else:
                            failed_steps.append(f"{step} (OTP not verified)")
                    else:
                        completed_steps.append(step)
                else:
                    failed_steps.append(step)
            else:
                failed_steps.append(f"{step} (not started)")
        
        # Face liveness is the final gate
        face_liveness_passed = "face_liveness" in completed_steps
        all_valid = len(completed_steps) == len(required_steps) and len(failed_steps) == 0
        
        # Determine final KYC status
        if all_valid and face_liveness_passed:
            kyc_status = "VERIFIED"  # Final verification complete
        elif len(completed_steps) >= 4:
            kyc_status = "MANUAL_REVIEW"
        else:
            kyc_status = "REJECTED"
        
        return {
            "overall_valid": all_valid,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "progress": f"{len(completed_steps)}/{len(required_steps)}",
            "completion_percentage": int((len(completed_steps) / len(required_steps)) * 100),
            "kyc_status": kyc_status,
            "face_liveness_completed": face_liveness_passed,
            "ready_for_finalization": face_liveness_passed,
            "validation_results": self.validation_results,
            "session_id": self.session_id
        }
