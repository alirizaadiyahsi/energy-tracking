"""
Common utility functions
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from decimal import Decimal


class DateTimeUtils:
    """Date and time utility functions"""
    
    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC datetime"""
        return datetime.utcnow()
    
    @staticmethod
    def to_iso_string(dt: datetime) -> str:
        """Convert datetime to ISO string"""
        return dt.isoformat() + "Z"
    
    @staticmethod
    def from_iso_string(iso_string: str) -> datetime:
        """Parse datetime from ISO string"""
        if iso_string.endswith("Z"):
            iso_string = iso_string[:-1]
        return datetime.fromisoformat(iso_string)


class JsonUtils:
    """JSON utility functions with support for special types"""
    
    @staticmethod
    def serialize(obj: Any) -> str:
        """Serialize object to JSON with datetime and Decimal support"""
        def default_serializer(o):
            if isinstance(o, datetime):
                return DateTimeUtils.to_iso_string(o)
            elif isinstance(o, Decimal):
                return float(o)
            raise TypeError(f"Object of type {type(o)} is not JSON serializable")
        
        return json.dumps(obj, default=default_serializer)
    
    @staticmethod
    def deserialize(json_str: str) -> Any:
        """Deserialize JSON string"""
        return json.loads(json_str)


class HashUtils:
    """Hashing utility functions"""
    
    @staticmethod
    def sha256_hash(data: str) -> str:
        """Generate SHA256 hash"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def md5_hash(data: str) -> str:
        """Generate MD5 hash"""
        return hashlib.md5(data.encode()).hexdigest()


class ValidationUtils:
    """Common validation utilities"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_strong_password(password: str) -> bool:
        """Check if password meets strength requirements"""
        import re
        # At least 8 characters, one uppercase, one lowercase, one digit, one special char
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        return re.match(pattern, password) is not None


class ConfigUtils:
    """Configuration utility functions"""
    
    @staticmethod
    def get_env_var(var_name: str, default: Optional[str] = None) -> str:
        """Get environment variable with optional default"""
        import os
        return os.getenv(var_name, default)
    
    @staticmethod
    def get_bool_env_var(var_name: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        import os
        value = os.getenv(var_name, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int_env_var(var_name: str, default: int = 0) -> int:
        """Get integer environment variable"""
        import os
        try:
            return int(os.getenv(var_name, str(default)))
        except ValueError:
            return default
