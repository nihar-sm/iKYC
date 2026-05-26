"""
Configuration settings for IntelliKYC Validation Engine
"""

class ValidationConfig:
    """Central configuration for all validators"""
    
    # Personal Validation Settings
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 100
    MIN_AGE = 18
    MAX_AGE = 120
    
    # Identity Validation Settings
    AADHAAR_LENGTH = 12
    PAN_LENGTH = 10
    
    # Contact Validation Settings
    PHONE_LENGTH = 10
    OTP_LENGTH = 6
    OTP_VALIDITY_MINUTES = 5
    
    # Face Validation Settings
    FACE_CONFIDENCE_THRESHOLD = 0.8
    LIVENESS_ACTIONS = ['blink', 'nod', 'turn_head']
    
    # Redis Configuration (for teammate's database)
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    
    # Validation Error Codes
    ERROR_CODES = {
        'EMPTY_FIELD': 'Field cannot be empty',
        'INVALID_LENGTH': 'Invalid field length',
        'INVALID_FORMAT': 'Invalid field format',
        'NOT_FOUND': 'Record not found in database',
        'DATABASE_ERROR': 'Database connection error'
    }
