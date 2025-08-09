"""
Centralized logging configuration for all microservices
"""

import os
import yaml
import logging
import logging.config
from typing import Optional
from contextlib import contextmanager


class RequestIDFilter(logging.Filter):
    """Filter to add request ID to log records"""
    
    def filter(self, record):
        # Try to get request ID from contextvars or set default
        record.request_id = getattr(record, 'request_id', 'no-request-id')
        return True


def setup_logging(
    service_name: str,
    config_path: Optional[str] = None,
    log_level: Optional[str] = None,
    log_to_file: bool = True
):
    """
    Setup centralized logging for a microservice
    
    Args:
        service_name: Name of the microservice
        config_path: Path to logging configuration file
        log_level: Override log level
        log_to_file: Whether to log to files
    """
    
    # Create logs directory if it doesn't exist
    if log_to_file:
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
    
    # Default config path
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "logging.yaml"
        )
    
    # Load logging configuration
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override log level if specified
        if log_level:
            config['root']['level'] = log_level.upper()
            # Also update handler levels
            for handler in config['handlers'].values():
                if handler.get('level') == 'INFO':
                    handler['level'] = log_level.upper()
        
        # Remove file handlers if not logging to file
        if not log_to_file:
            config['handlers'] = {
                k: v for k, v in config['handlers'].items() 
                if not v.get('filename')
            }
            config['root']['handlers'] = [
                h for h in config['root']['handlers'] 
                if h in config['handlers']
            ]
        
        # Apply configuration
        logging.config.dictConfig(config)
    else:
        # Fallback to basic configuration
        logging.basicConfig(
            level=log_level or "INFO",
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Set service name as root logger name
    logger = logging.getLogger(service_name)
    logger.info(f"Logging initialized for service: {service_name}")
    
    return logger


@contextmanager
def log_context(request_id: str = None, **kwargs):
    """
    Context manager to add contextual information to logs
    
    Args:
        request_id: Request ID to track across logs
        **kwargs: Additional context to include in logs
    """
    
    # Create a custom logger adapter
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            # Add context to extra
            context = {'request_id': request_id or 'no-request-id'}
            context.update(self.extra)
            kwargs.setdefault('extra', {}).update(context)
            return msg, kwargs
    
    # Get the root logger and create adapter
    logger = logging.getLogger()
    adapter = ContextAdapter(logger, kwargs)
    
    try:
        yield adapter
    finally:
        pass


class ServiceLogger:
    """Enhanced logger with service-specific features"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
    
    def info(self, message: str, **kwargs):
        """Log info with context"""
        self._log('info', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error with context"""
        self._log('error', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning with context"""
        self._log('warning', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug with context"""
        self._log('debug', message, **kwargs)
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method with context"""
        extra = {
            'service': self.service_name,
            **kwargs
        }
        getattr(self.logger, level)(message, extra=extra)
    
    def log_api_call(self, method: str, endpoint: str, status_code: int, 
                     duration: float, **kwargs):
        """Log API call with structured data"""
        self.info(
            f"API {method} {endpoint} - {status_code} - {duration:.3f}s",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration,
            **kwargs
        )
    
    def log_database_operation(self, operation: str, table: str, 
                              duration: float, **kwargs):
        """Log database operation"""
        self.info(
            f"DB {operation} on {table} - {duration:.3f}s",
            operation=operation,
            table=table,
            duration=duration,
            **kwargs
        )
    
    def log_external_service_call(self, service: str, endpoint: str, 
                                 status_code: int, duration: float, **kwargs):
        """Log external service call"""
        self.info(
            f"External {service} {endpoint} - {status_code} - {duration:.3f}s",
            external_service=service,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration,
            **kwargs
        )
