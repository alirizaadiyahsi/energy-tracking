"""
Security configuration management for the Energy Tracking platform
Centralized security settings and environment-specific configurations
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from infrastructure.logging import ServiceLogger

logger = ServiceLogger("security-config")

class SecurityLevel(Enum):
    """Security levels for different environments"""
    LOW = "low"          # Development
    MEDIUM = "medium"    # Testing/Staging
    HIGH = "high"        # Production
    MAXIMUM = "maximum"  # High-security production

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_size: int
    block_duration_minutes: int

@dataclass
class PasswordPolicyConfig:
    """Password policy configuration"""
    min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_numbers: bool
    require_special_chars: bool
    max_age_days: int
    history_count: int
    lockout_attempts: int
    lockout_duration_minutes: int

@dataclass
class SessionConfig:
    """Session management configuration"""
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    session_timeout_minutes: int
    max_concurrent_sessions: int
    secure_cookies: bool
    same_site_policy: str

@dataclass
class AuditConfig:
    """Audit logging configuration"""
    enabled: bool
    log_all_requests: bool
    log_request_bodies: bool
    log_response_bodies: bool
    sensitive_endpoints: List[str]
    retention_days: int

@dataclass
class ThreatDetectionConfig:
    """Threat detection configuration"""
    enabled: bool
    failed_login_threshold: int
    rapid_request_threshold: int
    suspicious_endpoint_threshold: int
    auto_block_enabled: bool
    threat_score_threshold: int

class SecurityConfigManager:
    """Manages security configurations across different environments"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment.lower()
        self.logger = ServiceLogger("security-config-manager")
        self._configs = self._load_configurations()
    
    def _load_configurations(self) -> Dict[str, Dict]:
        """Load security configurations for all environments"""
        return {
            "development": self._get_development_config(),
            "testing": self._get_testing_config(),
            "staging": self._get_staging_config(),
            "production": self._get_production_config(),
            "high_security": self._get_high_security_config()
        }
    
    def _get_development_config(self) -> Dict:
        """Development environment configuration - relaxed security"""
        return {
            "security_level": SecurityLevel.LOW,
            "rate_limit": RateLimitConfig(
                requests_per_minute=200,
                requests_per_hour=2000,
                requests_per_day=50000,
                burst_size=50,
                block_duration_minutes=5
            ),
            "password_policy": PasswordPolicyConfig(
                min_length=8,
                require_uppercase=False,
                require_lowercase=True,
                require_numbers=False,
                require_special_chars=False,
                max_age_days=365,
                history_count=3,
                lockout_attempts=10,
                lockout_duration_minutes=5
            ),
            "session": SessionConfig(
                access_token_expire_minutes=60,
                refresh_token_expire_days=7,
                session_timeout_minutes=120,
                max_concurrent_sessions=10,
                secure_cookies=False,
                same_site_policy="lax"
            ),
            "audit": AuditConfig(
                enabled=True,
                log_all_requests=False,
                log_request_bodies=False,
                log_response_bodies=False,
                sensitive_endpoints=["/auth/login", "/auth/register"],
                retention_days=30
            ),
            "threat_detection": ThreatDetectionConfig(
                enabled=True,
                failed_login_threshold=10,
                rapid_request_threshold=150,
                suspicious_endpoint_threshold=20,
                auto_block_enabled=False,
                threat_score_threshold=80
            )
        }
    
    def _get_testing_config(self) -> Dict:
        """Testing environment configuration"""
        config = self._get_development_config()
        config["security_level"] = SecurityLevel.MEDIUM
        
        # Stricter rate limiting for testing
        config["rate_limit"].requests_per_minute = 100
        config["rate_limit"].requests_per_hour = 1000
        
        # Enable more auditing
        config["audit"].log_all_requests = True
        
        return config
    
    def _get_staging_config(self) -> Dict:
        """Staging environment configuration - production-like security"""
        return {
            "security_level": SecurityLevel.HIGH,
            "rate_limit": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=500,
                requests_per_day=10000,
                burst_size=10,
                block_duration_minutes=30
            ),
            "password_policy": PasswordPolicyConfig(
                min_length=12,
                require_uppercase=True,
                require_lowercase=True,
                require_numbers=True,
                require_special_chars=True,
                max_age_days=90,
                history_count=12,
                lockout_attempts=5,
                lockout_duration_minutes=30
            ),
            "session": SessionConfig(
                access_token_expire_minutes=15,
                refresh_token_expire_days=1,
                session_timeout_minutes=30,
                max_concurrent_sessions=3,
                secure_cookies=True,
                same_site_policy="strict"
            ),
            "audit": AuditConfig(
                enabled=True,
                log_all_requests=True,
                log_request_bodies=True,
                log_response_bodies=False,
                sensitive_endpoints=[
                    "/auth/login", "/auth/register", "/users", "/admin",
                    "/auth/logout", "/auth/refresh", "/auth/password"
                ],
                retention_days=90
            ),
            "threat_detection": ThreatDetectionConfig(
                enabled=True,
                failed_login_threshold=5,
                rapid_request_threshold=80,
                suspicious_endpoint_threshold=10,
                auto_block_enabled=True,
                threat_score_threshold=60
            )
        }
    
    def _get_production_config(self) -> Dict:
        """Production environment configuration"""
        return {
            "security_level": SecurityLevel.HIGH,
            "rate_limit": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=500,
                requests_per_day=5000,
                burst_size=5,
                block_duration_minutes=60
            ),
            "password_policy": PasswordPolicyConfig(
                min_length=12,
                require_uppercase=True,
                require_lowercase=True,
                require_numbers=True,
                require_special_chars=True,
                max_age_days=90,
                history_count=12,
                lockout_attempts=3,
                lockout_duration_minutes=60
            ),
            "session": SessionConfig(
                access_token_expire_minutes=15,
                refresh_token_expire_days=1,
                session_timeout_minutes=30,
                max_concurrent_sessions=2,
                secure_cookies=True,
                same_site_policy="strict"
            ),
            "audit": AuditConfig(
                enabled=True,
                log_all_requests=True,
                log_request_bodies=True,
                log_response_bodies=False,
                sensitive_endpoints=[
                    "/auth/login", "/auth/register", "/users", "/admin",
                    "/auth/logout", "/auth/refresh", "/auth/password",
                    "/auth/delete", "/roles", "/permissions"
                ],
                retention_days=365
            ),
            "threat_detection": ThreatDetectionConfig(
                enabled=True,
                failed_login_threshold=3,
                rapid_request_threshold=50,
                suspicious_endpoint_threshold=5,
                auto_block_enabled=True,
                threat_score_threshold=50
            )
        }
    
    def _get_high_security_config(self) -> Dict:
        """Maximum security configuration for sensitive deployments"""
        return {
            "security_level": SecurityLevel.MAXIMUM,
            "rate_limit": RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=200,
                requests_per_day=2000,
                burst_size=3,
                block_duration_minutes=120
            ),
            "password_policy": PasswordPolicyConfig(
                min_length=16,
                require_uppercase=True,
                require_lowercase=True,
                require_numbers=True,
                require_special_chars=True,
                max_age_days=30,
                history_count=24,
                lockout_attempts=2,
                lockout_duration_minutes=120
            ),
            "session": SessionConfig(
                access_token_expire_minutes=5,
                refresh_token_expire_days=1,
                session_timeout_minutes=15,
                max_concurrent_sessions=1,
                secure_cookies=True,
                same_site_policy="strict"
            ),
            "audit": AuditConfig(
                enabled=True,
                log_all_requests=True,
                log_request_bodies=True,
                log_response_bodies=True,
                sensitive_endpoints=[
                    "/auth/login", "/auth/register", "/users", "/admin",
                    "/auth/logout", "/auth/refresh", "/auth/password",
                    "/auth/delete", "/roles", "/permissions", "/config",
                    "/system", "/monitoring"
                ],
                retention_days=2555  # 7 years
            ),
            "threat_detection": ThreatDetectionConfig(
                enabled=True,
                failed_login_threshold=2,
                rapid_request_threshold=25,
                suspicious_endpoint_threshold=3,
                auto_block_enabled=True,
                threat_score_threshold=30
            )
        }
    
    def get_config(self, config_type: str) -> any:
        """Get specific configuration for current environment"""
        env_config = self._configs.get(self.environment, self._configs["development"])
        return env_config.get(config_type)
    
    def get_rate_limit_config(self) -> RateLimitConfig:
        """Get rate limiting configuration"""
        return self.get_config("rate_limit")
    
    def get_password_policy_config(self) -> PasswordPolicyConfig:
        """Get password policy configuration"""
        return self.get_config("password_policy")
    
    def get_session_config(self) -> SessionConfig:
        """Get session configuration"""
        return self.get_config("session")
    
    def get_audit_config(self) -> AuditConfig:
        """Get audit configuration"""
        return self.get_config("audit")
    
    def get_threat_detection_config(self) -> ThreatDetectionConfig:
        """Get threat detection configuration"""
        return self.get_config("threat_detection")
    
    def get_security_level(self) -> SecurityLevel:
        """Get current security level"""
        return self.get_config("security_level")
    
    def export_config(self, include_sensitive: bool = False) -> Dict:
        """Export configuration for documentation or backup"""
        config = self._configs[self.environment]
        
        # Convert dataclasses to dictionaries
        exported = {}
        for key, value in config.items():
            if hasattr(value, '__dict__'):
                exported[key] = asdict(value)
            else:
                exported[key] = value.value if hasattr(value, 'value') else value
        
        if not include_sensitive:
            # Remove sensitive configuration details
            if 'password_policy' in exported:
                del exported['password_policy']['history_count']
        
        return exported
    
    def validate_environment_config(self) -> List[str]:
        """Validate current environment configuration"""
        warnings = []
        config = self._configs[self.environment]
        
        # Check for development settings in production
        if self.environment in ["production", "staging"]:
            rate_limit = config["rate_limit"]
            if rate_limit.requests_per_minute > 100:
                warnings.append("Rate limit too high for production environment")
            
            password_policy = config["password_policy"]
            if password_policy.min_length < 12:
                warnings.append("Password minimum length too low for production")
            
            session = config["session"]
            if session.access_token_expire_minutes > 30:
                warnings.append("Access token expiry too long for production")
        
        return warnings
    
    def update_from_environment_variables(self) -> None:
        """Update configuration from environment variables"""
        env_config = self._configs[self.environment]
        
        # Rate limiting overrides
        if os.getenv("RATE_LIMIT_PER_MINUTE"):
            env_config["rate_limit"].requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE"))
        
        if os.getenv("RATE_LIMIT_PER_HOUR"):
            env_config["rate_limit"].requests_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR"))
        
        # Password policy overrides
        if os.getenv("PASSWORD_MIN_LENGTH"):
            env_config["password_policy"].min_length = int(os.getenv("PASSWORD_MIN_LENGTH"))
        
        if os.getenv("PASSWORD_MAX_AGE_DAYS"):
            env_config["password_policy"].max_age_days = int(os.getenv("PASSWORD_MAX_AGE_DAYS"))
        
        # Session overrides
        if os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"):
            env_config["session"].access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
        
        # Threat detection overrides
        if os.getenv("THREAT_DETECTION_ENABLED"):
            env_config["threat_detection"].enabled = os.getenv("THREAT_DETECTION_ENABLED").lower() == "true"
        
        self.logger.info(f"Security configuration updated from environment variables for {self.environment}")

# Global security configuration manager
def get_security_config_manager(environment: str = None) -> SecurityConfigManager:
    """Get security configuration manager for environment"""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    return SecurityConfigManager(environment)

# Helper functions for common configurations
def get_rate_limit_for_endpoint(endpoint: str, environment: str = None) -> RateLimitConfig:
    """Get rate limit configuration for specific endpoint"""
    manager = get_security_config_manager(environment)
    base_config = manager.get_rate_limit_config()
    
    # Endpoint-specific overrides
    if endpoint in ["/auth/login", "/auth/register"]:
        # Stricter limits for auth endpoints
        base_config.requests_per_minute = max(1, base_config.requests_per_minute // 2)
        base_config.requests_per_hour = max(10, base_config.requests_per_hour // 2)
    elif endpoint.startswith("/admin"):
        # Very strict limits for admin endpoints
        base_config.requests_per_minute = max(1, base_config.requests_per_minute // 4)
        base_config.requests_per_hour = max(5, base_config.requests_per_hour // 4)
    
    return base_config
