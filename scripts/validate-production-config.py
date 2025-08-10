# Production Configuration Validation Script

import os
import sys
import yaml
import json
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ConfigValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]

class ProductionConfigValidator:
    """Validates production configuration for device management system"""
    
    def __init__(self):
        self.required_env_vars = {
            'DATABASE_URL': 'Database connection string',
            'AUTH_SERVICE_URL': 'Authentication service endpoint',
            'SECRET_KEY': 'Secret key for JWT validation',
            'ORGANIZATION_ISOLATION_ENABLED': 'Organization isolation flag',
            'RATE_LIMITING_ENABLED': 'Rate limiting enablement',
            'AUDIT_LOGGING_ENABLED': 'Audit logging enablement'
        }
        
        self.security_requirements = {
            'authentication': ['JWT_ALGORITHM', 'JWT_SECRET_KEY', 'TOKEN_EXPIRY'],
            'rate_limiting': ['RATE_LIMIT_PER_MINUTE', 'ADMIN_RATE_LIMIT_PER_MINUTE'],
            'audit': ['AUDIT_LOG_LEVEL', 'AUDIT_RETENTION_DAYS'],
            'database': ['DB_SSL_MODE', 'DB_CONNECTION_POOL_SIZE']
        }
        
        self.recommended_values = {
            'JWT_ALGORITHM': 'HS256',
            'TOKEN_EXPIRY': '3600',  # 1 hour
            'RATE_LIMIT_PER_MINUTE': '100',
            'ADMIN_RATE_LIMIT_PER_MINUTE': '500',
            'AUDIT_LOG_LEVEL': 'INFO',
            'AUDIT_RETENTION_DAYS': '90',
            'DB_SSL_MODE': 'require',
            'DB_CONNECTION_POOL_SIZE': '20'
        }
    
    def validate_environment_variables(self) -> ConfigValidationResult:
        """Validate required environment variables"""
        errors = []
        warnings = []
        recommendations = []
        
        # Check required environment variables
        for var, description in self.required_env_vars.items():
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing required environment variable: {var} ({description})")
            elif var == 'SECRET_KEY' and len(value) < 32:
                warnings.append(f"SECRET_KEY should be at least 32 characters long for security")
        
        # Check security-related configurations
        for category, vars in self.security_requirements.items():
            for var in vars:
                value = os.getenv(var)
                if not value:
                    warnings.append(f"Missing {category} configuration: {var}")
                elif var in self.recommended_values and value != self.recommended_values[var]:
                    recommendations.append(
                        f"Consider setting {var}={self.recommended_values[var]} "
                        f"(current: {value})"
                    )
        
        # Check for debug/development settings
        debug_vars = ['DEBUG', 'DEVELOPMENT_MODE', 'TESTING_MODE']
        for var in debug_vars:
            if os.getenv(var, '').lower() in ['true', '1', 'yes']:
                errors.append(f"Development setting {var} should be disabled in production")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def validate_database_config(self) -> ConfigValidationResult:
        """Validate database configuration"""
        errors = []
        warnings = []
        recommendations = []
        
        db_url = os.getenv('DATABASE_URL', '')
        
        if not db_url:
            errors.append("DATABASE_URL is required")
        else:
            # Check for SSL/security in connection string
            if 'postgresql' in db_url.lower():
                if 'sslmode=require' not in db_url.lower():
                    warnings.append("PostgreSQL connection should use SSL (sslmode=require)")
                if 'localhost' in db_url or '127.0.0.1' in db_url:
                    warnings.append("Database appears to be localhost - ensure this is intended for production")
            
            # Check for credentials in URL (security risk)
            if '@' in db_url and ('password' in db_url.lower() or len(db_url.split('@')[0].split(':')) > 3):
                recommendations.append("Consider using environment variables for database credentials instead of embedding in URL")
        
        # Check connection pool settings
        pool_size = os.getenv('DB_CONNECTION_POOL_SIZE')
        if pool_size:
            try:
                size = int(pool_size)
                if size < 5:
                    warnings.append("Database connection pool size might be too small for production")
                elif size > 100:
                    warnings.append("Database connection pool size might be too large")
            except ValueError:
                errors.append("DB_CONNECTION_POOL_SIZE must be a valid integer")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def validate_security_config(self) -> ConfigValidationResult:
        """Validate security configuration"""
        errors = []
        warnings = []
        recommendations = []
        
        # JWT Configuration
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if jwt_secret:
            if len(jwt_secret) < 32:
                errors.append("JWT_SECRET_KEY must be at least 32 characters long")
            elif jwt_secret in ['secret', 'password', 'default']:
                errors.append("JWT_SECRET_KEY appears to be a default/weak value")
        
        # Rate limiting
        rate_limit = os.getenv('RATE_LIMIT_PER_MINUTE')
        if rate_limit:
            try:
                limit = int(rate_limit)
                if limit < 10:
                    warnings.append("Rate limit might be too restrictive for production use")
                elif limit > 1000:
                    warnings.append("Rate limit might be too permissive")
            except ValueError:
                errors.append("RATE_LIMIT_PER_MINUTE must be a valid integer")
        
        # CORS settings
        cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '*')
        if cors_origins == '*':
            warnings.append("CORS is set to allow all origins - restrict for production")
        
        # HTTPS enforcement
        force_https = os.getenv('FORCE_HTTPS', 'false').lower()
        if force_https not in ['true', '1', 'yes']:
            warnings.append("HTTPS should be enforced in production (FORCE_HTTPS=true)")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def validate_monitoring_config(self) -> ConfigValidationResult:
        """Validate monitoring and logging configuration"""
        errors = []
        warnings = []
        recommendations = []
        
        # Logging configuration
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        if log_level == 'DEBUG':
            warnings.append("LOG_LEVEL=DEBUG may be too verbose for production")
        elif log_level not in ['INFO', 'WARNING', 'ERROR']:
            recommendations.append("Consider setting LOG_LEVEL to INFO for production")
        
        # Audit logging
        audit_enabled = os.getenv('AUDIT_LOGGING_ENABLED', 'false').lower()
        if audit_enabled not in ['true', '1', 'yes']:
            errors.append("Audit logging must be enabled in production for compliance")
        
        # Metrics and monitoring
        metrics_endpoint = os.getenv('METRICS_ENDPOINT')
        if not metrics_endpoint:
            recommendations.append("Consider enabling metrics endpoint for monitoring")
        
        # Health check endpoint
        health_check_enabled = os.getenv('HEALTH_CHECK_ENABLED', 'false').lower()
        if health_check_enabled not in ['true', '1', 'yes']:
            recommendations.append("Enable health check endpoint for load balancer monitoring")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def validate_performance_config(self) -> ConfigValidationResult:
        """Validate performance-related configuration"""
        errors = []
        warnings = []
        recommendations = []
        
        # Worker configuration
        workers = os.getenv('WORKERS')
        if workers:
            try:
                worker_count = int(workers)
                if worker_count < 2:
                    warnings.append("Consider using multiple workers for production")
                elif worker_count > 32:
                    warnings.append("Too many workers may cause resource contention")
            except ValueError:
                errors.append("WORKERS must be a valid integer")
        
        # Cache configuration
        cache_enabled = os.getenv('CACHE_ENABLED', 'false').lower()
        if cache_enabled not in ['true', '1', 'yes']:
            recommendations.append("Enable caching for better performance")
        
        # Request timeout
        timeout = os.getenv('REQUEST_TIMEOUT')
        if timeout:
            try:
                timeout_val = int(timeout)
                if timeout_val < 10:
                    warnings.append("Request timeout might be too short")
                elif timeout_val > 300:
                    warnings.append("Request timeout might be too long")
            except ValueError:
                errors.append("REQUEST_TIMEOUT must be a valid integer")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def run_full_validation(self) -> Dict[str, ConfigValidationResult]:
        """Run all validation checks"""
        return {
            'environment': self.validate_environment_variables(),
            'database': self.validate_database_config(),
            'security': self.validate_security_config(),
            'monitoring': self.validate_monitoring_config(),
            'performance': self.validate_performance_config()
        }
    
    def generate_report(self, results: Dict[str, ConfigValidationResult]) -> str:
        """Generate a human-readable validation report"""
        report = []
        report.append("=" * 60)
        report.append("PRODUCTION CONFIGURATION VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        overall_valid = True
        total_errors = 0
        total_warnings = 0
        total_recommendations = 0
        
        for category, result in results.items():
            if not result.is_valid:
                overall_valid = False
            
            total_errors += len(result.errors)
            total_warnings += len(result.warnings)
            total_recommendations += len(result.recommendations)
            
            status = "✅ VALID" if result.is_valid else "❌ INVALID"
            report.append(f"{category.upper()} CONFIGURATION: {status}")
            report.append("-" * 40)
            
            if result.errors:
                report.append("🔴 ERRORS:")
                for error in result.errors:
                    report.append(f"  • {error}")
                report.append("")
            
            if result.warnings:
                report.append("🟡 WARNINGS:")
                for warning in result.warnings:
                    report.append(f"  • {warning}")
                report.append("")
            
            if result.recommendations:
                report.append("💡 RECOMMENDATIONS:")
                for rec in result.recommendations:
                    report.append(f"  • {rec}")
                report.append("")
            
            report.append("")
        
        # Summary
        report.append("=" * 60)
        report.append("SUMMARY")
        report.append("=" * 60)
        report.append(f"Overall Status: {'✅ READY FOR PRODUCTION' if overall_valid else '❌ NOT READY FOR PRODUCTION'}")
        report.append(f"Total Errors: {total_errors}")
        report.append(f"Total Warnings: {total_warnings}")
        report.append(f"Total Recommendations: {total_recommendations}")
        report.append("")
        
        if overall_valid:
            report.append("🎉 Configuration validation passed! The system is ready for production deployment.")
        else:
            report.append("❌ Configuration validation failed. Please address all errors before deploying to production.")
        
        return "\n".join(report)

def main():
    """Main validation script"""
    print("🔍 Running production configuration validation...")
    print("")
    
    validator = ProductionConfigValidator()
    results = validator.run_full_validation()
    report = validator.generate_report(results)
    
    print(report)
    
    # Save report to file
    with open('production_config_validation_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n📄 Report saved to: production_config_validation_report.txt")
    
    # Exit with error code if validation failed
    overall_valid = all(result.is_valid for result in results.values())
    if not overall_valid:
        print("\n❌ Validation failed. Exiting with error code 1.")
        sys.exit(1)
    else:
        print("\n✅ Validation passed. System ready for production!")
        sys.exit(0)

if __name__ == "__main__":
    main()
