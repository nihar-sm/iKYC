"""
Personal Information Validators for Indian KYC
Validates full name and date of birth
"""

import re
from datetime import datetime, date
from typing import Dict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.validation_config import ValidationConfig
from utils.common_utils import ValidationUtils

class PersonalValidators:
    """Validators for personal information"""
    
    @staticmethod
    def validate_full_name(name: str) -> Dict:
        """
        Validate full name according to Indian KYC standards
        
        Rules:
        - Only alphabets and single spaces
        - Minimum 3 characters, maximum 100 characters
        - At least 2 words (first name + last name)
        - No consecutive spaces or special characters
        """
        
        # Clean input
        name_clean = ValidationUtils.clean_text_input(name) if name else ""
        
        # Empty check
        if not name_clean:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="full_name",
                error="Name cannot be empty",
                error_code="EMPTY_NAME"
            )
        
        # Length validation
        if len(name_clean) < ValidationConfig.MIN_NAME_LENGTH:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="full_name",
                error=f"Name must be at least {ValidationConfig.MIN_NAME_LENGTH} characters long",
                error_code="NAME_TOO_SHORT"
            )
        
        if len(name_clean) > ValidationConfig.MAX_NAME_LENGTH:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="full_name",
                error=f"Name must not exceed {ValidationConfig.MAX_NAME_LENGTH} characters",
                error_code="NAME_TOO_LONG"
            )
        
        # Pattern validation: Only alphabets and single spaces
        name_pattern = r"^[A-Za-z]+(\s[A-Za-z]+)*$"
        if not re.match(name_pattern, name_clean):
            return ValidationUtils.create_validation_response(
                valid=False,
                field="full_name",
                error="Name should only contain alphabets and single spaces",
                error_code="INVALID_NAME_FORMAT"
            )
        
        # Word count validation
        words = name_clean.split()
        if len(words) < 2:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="full_name",
                error="Please provide both first name and last name",
                error_code="INSUFFICIENT_WORDS"
            )
        
        # Success response
        return ValidationUtils.create_validation_response(
            valid=True,
            field="full_name",
            message="Name validation successful",
            data={
                "cleaned_value": name_clean,
                "word_count": len(words),
                "first_name": words[0],
                "last_name": " ".join(words[1:])
            }
        )
    
    @staticmethod
    def validate_date_of_birth(dob: str) -> Dict:
        """
        Validate date of birth in DD-MM-YYYY format
        
        Rules:
        - Must match DD-MM-YYYY format exactly
        - Must be a valid calendar date
        - Age must be >= 18 years
        - Cannot be future date
        """
        
        # Clean input
        dob_clean = ValidationUtils.clean_text_input(dob) if dob else ""
        
        # Empty check
        if not dob_clean:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="date_of_birth",
                error="Date of birth cannot be empty",
                error_code="EMPTY_DOB"
            )
        
        # Format validation
        dob_pattern = r"^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-([0-9]{4})$"
        if not re.match(dob_pattern, dob_clean):
            return ValidationUtils.create_validation_response(
                valid=False,
                field="date_of_birth",
                error="Date must be in DD-MM-YYYY format (e.g., 15-08-1990)",
                error_code="INVALID_DOB_FORMAT"
            )
        
        try:
            # Parse date
            day, month, year = map(int, dob_clean.split('-'))
            birth_date = date(year, month, day)
            today = date.today()
            
            # Future date check
            if birth_date > today:
                return ValidationUtils.create_validation_response(
                    valid=False,
                    field="date_of_birth",
                    error="Date of birth cannot be in the future",
                    error_code="FUTURE_DOB"
                )
            
            # Age calculation
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            # Minimum age check
            if age < ValidationConfig.MIN_AGE:
                return ValidationUtils.create_validation_response(
                    valid=False,
                    field="date_of_birth",
                    error=f"Minimum age requirement is {ValidationConfig.MIN_AGE} years. Current age: {age}",
                    error_code="UNDERAGE"
                )
            
            # Maximum age check
            if age > ValidationConfig.MAX_AGE:
                return ValidationUtils.create_validation_response(
                    valid=False,
                    field="date_of_birth",
                    error="Please enter a valid date of birth",
                    error_code="INVALID_AGE"
                )
            
            # Success response
            return ValidationUtils.create_validation_response(
                valid=True,
                field="date_of_birth",
                message=f"Date of birth validation successful. Age: {age} years",
                data={
                    "parsed_date": birth_date.isoformat(),
                    "formatted_date": dob_clean,
                    "age": age
                }
            )
            
        except ValueError as e:
            return ValidationUtils.create_validation_response(
                valid=False,
                field="date_of_birth",
                error=f"Invalid date: Please check the day/month combination",
                error_code="INVALID_DATE"
            )
