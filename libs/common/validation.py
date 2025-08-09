"""
Input validation and sanitization utilities
Comprehensive validation for API requests and data sanitization
"""

import re
import html
import json
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, ValidationError
from infrastructure.logging import ServiceLogger

logger = ServiceLogger("input-validator")

class ValidationRule:
    """Base class for validation rules"""
    
    def __init__(self, message: str):
        self.message = message
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """Returns (is_valid, error_message)"""
        raise NotImplementedError

class RequiredRule(ValidationRule):
    """Validates that value is not None or empty"""
    
    def __init__(self, message: str = "Field is required"):
        super().__init__(message)
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return False, self.message
        return True, ""

class MinLengthRule(ValidationRule):
    """Validates minimum string length"""
    
    def __init__(self, min_length: int, message: str = None):
        self.min_length = min_length
        super().__init__(message or f"Must be at least {min_length} characters")
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Must be a string"
        
        if len(value) < self.min_length:
            return False, self.message
        return True, ""

class MaxLengthRule(ValidationRule):
    """Validates maximum string length"""
    
    def __init__(self, max_length: int, message: str = None):
        self.max_length = max_length
        super().__init__(message or f"Must be no more than {max_length} characters")
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Must be a string"
        
        if len(value) > self.max_length:
            return False, self.message
        return True, ""

class EmailRule(ValidationRule):
    """Validates email format"""
    
    def __init__(self, message: str = "Invalid email format"):
        super().__init__(message)
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Email must be a string"
        
        try:
            validate_email(value)
            return True, ""
        except EmailNotValidError:
            return False, self.message

class RegexRule(ValidationRule):
    """Validates against regular expression"""
    
    def __init__(self, pattern: str, message: str):
        self.pattern = re.compile(pattern)
        super().__init__(message)
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Must be a string"
        
        if not self.pattern.match(value):
            return False, self.message
        return True, ""

class NumericRangeRule(ValidationRule):
    """Validates numeric range"""
    
    def __init__(self, min_val: Optional[float] = None, max_val: Optional[float] = None,
                 message: str = None):
        self.min_val = min_val
        self.max_val = max_val
        
        if message is None:
            if min_val is not None and max_val is not None:
                message = f"Must be between {min_val} and {max_val}"
            elif min_val is not None:
                message = f"Must be at least {min_val}"
            elif max_val is not None:
                message = f"Must be no more than {max_val}"
            else:
                message = "Invalid numeric value"
        
        super().__init__(message)
    
    def validate(self, value: Any) -> tuple[bool, str]:
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False, "Must be a number"
        
        if self.min_val is not None and num_value < self.min_val:
            return False, self.message
        
        if self.max_val is not None and num_value > self.max_val:
            return False, self.message
        
        return True, ""

class UUIDRule(ValidationRule):
    """Validates UUID format"""
    
    def __init__(self, message: str = "Invalid UUID format"):
        super().__init__(message)
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "UUID must be a string"
        
        try:
            uuid.UUID(value)
            return True, ""
        except ValueError:
            return False, self.message

class DateTimeRule(ValidationRule):
    """Validates datetime format"""
    
    def __init__(self, format: str = "%Y-%m-%d %H:%M:%S", message: str = None):
        self.format = format
        super().__init__(message or f"Invalid datetime format, expected {format}")
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Datetime must be a string"
        
        try:
            datetime.strptime(value, self.format)
            return True, ""
        except ValueError:
            return False, self.message

class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove/escape HTML tags and entities"""
        if not isinstance(text, str):
            return text
        
        # Remove script tags completely
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove dangerous attributes
        dangerous_attrs = ['onload', 'onerror', 'onclick', 'onmouseover', 'onfocus', 'onblur']
        for attr in dangerous_attrs:
            text = re.sub(f'{attr}\\s*=\\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        
        # Escape HTML entities
        text = html.escape(text)
        
        return text
    
    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Basic SQL injection prevention"""
        if not isinstance(text, str):
            return text
        
        # Remove SQL keywords and dangerous characters
        dangerous_patterns = [
            r'\bUNION\b', r'\bSELECT\b', r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b',
            r'\bDROP\b', r'\bCREATE\b', r'\bALTER\b', r'\bEXEC\b', r'\bEXECUTE\b',
            r'--', r'/\*', r'\*/', r';', r"'", r'"'
        ]
        
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        if not isinstance(filename, str):
            return "unknown"
        
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Keep only alphanumeric, dots, dashes, and underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename or "unknown"
    
    @staticmethod
    def sanitize_json(data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {key: InputSanitizer.sanitize_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [InputSanitizer.sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return InputSanitizer.sanitize_html(data)
        else:
            return data

class FieldValidator:
    """Field-level validator with multiple rules"""
    
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.rules: List[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule) -> 'FieldValidator':
        """Add validation rule"""
        self.rules.append(rule)
        return self
    
    def required(self, message: str = None) -> 'FieldValidator':
        """Add required validation"""
        return self.add_rule(RequiredRule(message or f"{self.field_name} is required"))
    
    def min_length(self, length: int, message: str = None) -> 'FieldValidator':
        """Add minimum length validation"""
        return self.add_rule(MinLengthRule(length, message))
    
    def max_length(self, length: int, message: str = None) -> 'FieldValidator':
        """Add maximum length validation"""
        return self.add_rule(MaxLengthRule(length, message))
    
    def email(self, message: str = None) -> 'FieldValidator':
        """Add email validation"""
        return self.add_rule(EmailRule(message))
    
    def regex(self, pattern: str, message: str) -> 'FieldValidator':
        """Add regex validation"""
        return self.add_rule(RegexRule(pattern, message))
    
    def numeric_range(self, min_val: Optional[float] = None, 
                     max_val: Optional[float] = None, message: str = None) -> 'FieldValidator':
        """Add numeric range validation"""
        return self.add_rule(NumericRangeRule(min_val, max_val, message))
    
    def uuid(self, message: str = None) -> 'FieldValidator':
        """Add UUID validation"""
        return self.add_rule(UUIDRule(message))
    
    def datetime(self, format: str = "%Y-%m-%d %H:%M:%S", message: str = None) -> 'FieldValidator':
        """Add datetime validation"""
        return self.add_rule(DateTimeRule(format, message))
    
    def validate(self, value: Any) -> tuple[bool, List[str]]:
        """Validate value against all rules"""
        errors = []
        
        for rule in self.rules:
            is_valid, error_message = rule.validate(value)
            if not is_valid:
                errors.append(error_message)
        
        return len(errors) == 0, errors

class SchemaValidator:
    """Schema-level validator for complex data structures"""
    
    def __init__(self):
        self.fields: Dict[str, FieldValidator] = {}
    
    def field(self, name: str) -> FieldValidator:
        """Add field validator"""
        validator = FieldValidator(name)
        self.fields[name] = validator
        return validator
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, Dict[str, List[str]]]:
        """Validate data against schema"""
        errors = {}
        is_valid = True
        
        for field_name, validator in self.fields.items():
            value = data.get(field_name)
            field_valid, field_errors = validator.validate(value)
            
            if not field_valid:
                errors[field_name] = field_errors
                is_valid = False
        
        return is_valid, errors

# Predefined common validators
class CommonValidators:
    """Common validation schemas"""
    
    @staticmethod
    def user_registration() -> SchemaValidator:
        """User registration validation"""
        schema = SchemaValidator()
        
        schema.field("email").required().email().max_length(255)
        schema.field("password").required().min_length(8).max_length(128)
        schema.field("first_name").required().min_length(1).max_length(50)
        schema.field("last_name").required().min_length(1).max_length(50)
        
        return schema
    
    @staticmethod
    def user_login() -> SchemaValidator:
        """User login validation"""
        schema = SchemaValidator()
        
        schema.field("email").required().email().max_length(255)
        schema.field("password").required().min_length(1).max_length(128)
        
        return schema
    
    @staticmethod
    def password_change() -> SchemaValidator:
        """Password change validation"""
        schema = SchemaValidator()
        
        schema.field("current_password").required().min_length(1).max_length(128)
        schema.field("new_password").required().min_length(8).max_length(128).regex(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
            "Password must contain uppercase, lowercase, number and special character"
        )
        
        return schema
    
    @staticmethod
    def device_data() -> SchemaValidator:
        """IoT device data validation"""
        schema = SchemaValidator()
        
        schema.field("device_id").required().uuid()
        schema.field("timestamp").required().datetime("%Y-%m-%dT%H:%M:%SZ")
        schema.field("temperature").numeric_range(-50, 100)
        schema.field("humidity").numeric_range(0, 100)
        schema.field("energy_consumption").numeric_range(0, 10000)
        
        return schema

# Helper functions
def validate_and_sanitize(data: Dict[str, Any], schema: SchemaValidator) -> tuple[bool, Dict[str, Any], Dict[str, List[str]]]:
    """Validate and sanitize data in one operation"""
    # First sanitize
    sanitized_data = InputSanitizer.sanitize_json(data)
    
    # Then validate
    is_valid, errors = schema.validate(sanitized_data)
    
    return is_valid, sanitized_data, errors

def create_validation_middleware(schema: SchemaValidator) -> Callable:
    """Create FastAPI middleware for request validation"""
    async def validation_middleware(request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    is_valid, sanitized_data, errors = validate_and_sanitize(data, schema)
                    
                    if not is_valid:
                        from fastapi.responses import JSONResponse
                        return JSONResponse(
                            status_code=422,
                            content={
                                "error": "VALIDATION_ERROR",
                                "message": "Request validation failed",
                                "details": errors
                            }
                        )
                    
                    # Replace request body with sanitized data
                    request._body = json.dumps(sanitized_data).encode()
            
            except json.JSONDecodeError:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "INVALID_JSON",
                        "message": "Request body is not valid JSON"
                    }
                )
        
        return await call_next(request)
    
    return validation_middleware
