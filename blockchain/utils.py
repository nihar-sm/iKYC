"""
Utility functions for the KYC blockchain system
"""

import hashlib
import json
from typing import Any, Dict


def hash_data(data: Any) -> str:
    """
    Create SHA-256 hash of any data structure
    
    Args:
        data: Data to hash (will be JSON serialized)
        
    Returns:
        Hexadecimal hash string
    """
    if isinstance(data, dict):
        json_string = json.dumps(data, sort_keys=True)
    else:
        json_string = str(data)
    
    return hashlib.sha256(json_string.encode('utf-8')).hexdigest()


def validate_kyc_level(level: str) -> bool:
    """
    Validate KYC verification level
    
    Args:
        level: KYC level string
        
    Returns:
        True if valid level, False otherwise
    """
    valid_levels = ['CIP', 'CDD', 'EDD']
    return level in valid_levels


def format_timestamp(timestamp: float) -> str:
    """
    Format timestamp for display
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted datetime string
    """
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
