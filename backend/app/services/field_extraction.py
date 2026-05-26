import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentFieldExtractor:
    """Enhanced field extraction for Indian identity documents"""
    
    def __init__(self):
        # Aadhaar number patterns
        self.aadhaar_patterns = [
            r'\b(\d{4})\s*(\d{4})\s*(\d{4})\b',  # 1234 5678 9012
            r'\b(\d{12})\b',  # 123456789012
        ]
        
        # PAN patterns
        self.pan_patterns = [
            r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',  # ABCDE1234F
            r'\b[A-Z]{5}\s*[0-9]{4}\s*[A-Z]{1}\b',  # ABCDE 1234 F
        ]
        
        # Name patterns
        self.name_patterns = [
            r'Name[:\s]+([A-Za-z\s]+?)(?:\n|DOB|Date|Address|Phone)',
            r'(?:Name|नाम)[:\s]*([A-Za-z\s]+?)(?:\n|DOB|Date)',
            r'([A-Z][A-Z\s]{10,40})(?:\n|\s{2,})',  # All caps names
        ]
        
        # Date patterns
        self.date_patterns = [
            r'DOB[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Date of Birth[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'जन्म तिथि[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        # Address patterns
        self.address_patterns = [
            r'Address[:\s]+([^:]+?)(?:Pin|Phone|\n\n)',
            r'पता[:\s]+([^:]+?)(?:Pin|Phone|\n\n)',
        ]
        
        # Phone patterns
        self.phone_patterns = [
            r'(?:Phone|Mobile|Ph)[:\s]*(\+91[-\s]?)?([6-9]\d{9})',
            r'\b([6-9]\d{9})\b',
        ]
    
    def extract_fields(self, text: str, document_type: str = "aadhaar") -> Dict[str, Any]:
        """Extract structured fields from OCR text"""
        
        logger.info(f"Extracting fields for {document_type} document")
        
        fields = {}
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Extract based on document type
        if document_type.lower() == "aadhaar":
            fields.update(self._extract_aadhaar_fields(cleaned_text))
        elif document_type.lower() == "pan":
            fields.update(self._extract_pan_fields(cleaned_text))
        else:
            # Generic extraction
            fields.update(self._extract_common_fields(cleaned_text))
        
        # Post-process and validate fields
        fields = self._validate_and_clean_fields(fields)
        
        logger.info(f"Extracted {len(fields)} fields: {list(fields.keys())}")
        
        return fields
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize OCR text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that interfere with extraction
        text = re.sub(r'[^\w\s:/-]', ' ', text)
        return text.strip()
    
    def _extract_aadhaar_fields(self, text: str) -> Dict[str, Any]:
        """Extract fields specific to Aadhaar cards"""
        fields = {}
        
        # Extract Aadhaar number
        for pattern in self.aadhaar_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:  # Grouped format
                    fields['aadhaar_number'] = ''.join(match.groups())
                else:  # Single group
                    fields['aadhaar_number'] = match.group(1) if len(match.groups()) > 0 else match.group(0)
                break
        
        # Extract common fields
        fields.update(self._extract_common_fields(text))
        
        return fields
    
    def _extract_pan_fields(self, text: str) -> Dict[str, Any]:
        """Extract fields specific to PAN cards"""
        fields = {}
        
        # Extract PAN number
        for pattern in self.pan_patterns:
            match = re.search(pattern, text)
            if match:
                fields['pan_number'] = match.group(0).replace(' ', '')
                break
        
        # Extract common fields
        fields.update(self._extract_common_fields(text))
        
        return fields
    
    def _extract_common_fields(self, text: str) -> Dict[str, Any]:
        """Extract common fields from any document"""
        fields = {}
        
        # Extract name
        for pattern in self.name_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name.split()) >= 2 and len(name) <= 50:  # Reasonable name
                    fields['name'] = name
                    break
        
        # Extract date of birth
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dob = match.group(1)
                if self._is_valid_date(dob):
                    fields['date_of_birth'] = self._standardize_date(dob)
                    break
        
        # Extract address
        for pattern in self.address_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                address = match.group(1).strip()
                if len(address) > 10:  # Reasonable address length
                    fields['address'] = address[:200]  # Limit length
                    break
        
        # Extract phone number
        for pattern in self.phone_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) >= 2:
                    phone = match.group(2)
                else:
                    phone = match.group(1) if len(match.groups()) > 0 else match.group(0)
                
                if len(phone) == 10:
                    fields['phone'] = phone
                    break
        
        return fields
    
    def _validate_and_clean_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted fields"""
        cleaned_fields = {}
        
        # Validate Aadhaar number
        if 'aadhaar_number' in fields:
            aadhaar = fields['aadhaar_number']
            if self._is_valid_aadhaar(aadhaar):
                cleaned_fields['aadhaar_number'] = aadhaar
        
        # Validate PAN number
        if 'pan_number' in fields:
            pan = fields['pan_number']
            if self._is_valid_pan(pan):
                cleaned_fields['pan_number'] = pan
        
        # Validate name
        if 'name' in fields:
            name = fields['name'].strip()
            if 2 <= len(name.split()) <= 5 and len(name) <= 50:
                cleaned_fields['name'] = name.title()
        
        # Validate and standardize date
        if 'date_of_birth' in fields:
            dob = fields['date_of_birth']
            if self._is_valid_date(dob):
                cleaned_fields['date_of_birth'] = self._standardize_date(dob)
        
        # Add other fields as-is
        for key, value in fields.items():
            if key not in cleaned_fields and key not in ['aadhaar_number', 'pan_number', 'name', 'date_of_birth']:
                cleaned_fields[key] = value
        
        return cleaned_fields
    
    def _is_valid_aadhaar(self, aadhaar: str) -> bool:
        """Validate Aadhaar number format"""
        aadhaar = re.sub(r'\D', '', aadhaar)  # Remove non-digits
        return len(aadhaar) == 12 and aadhaar.isdigit()
    
    def _is_valid_pan(self, pan: str) -> bool:
        """Validate PAN number format"""
        pan = pan.replace(' ', '').upper()
        return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan))
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Validate date string"""
        try:
            # Try different date formats
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%Y-%m-%d']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    # Check if date is reasonable (not in future, not too old)
                    current_year = datetime.now().year
                    if 1900 <= date_obj.year <= current_year:
                        return True
                except ValueError:
                    continue
            return False
        except:
            return False
    
    def _standardize_date(self, date_str: str) -> str:
        """Standardize date to DD/MM/YYYY format"""
        try:
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%Y-%m-%d']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    continue
            return date_str  # Return original if can't parse
        except:
            return date_str

# Global field extractor instance
field_extractor = DocumentFieldExtractor()
