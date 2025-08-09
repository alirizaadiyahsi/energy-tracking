"""
Monitoring and observability utilities
"""

import time
import logging
import traceback
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager


class RequestIDFilter(logging.Filter):
    """Adds request ID to log records"""
    
    def filter(self, record):
        # Add a default request_id if not present
        if not hasattr(record, 'request_id'):
            record.request_id = '-'
        return True


class MetricsCollector:
    """Simple metrics collection utility"""
    
    def __init__(self):
        self.metrics = {}
        self.counters = {}
        self.timers = {}
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = f"{name}:{tags}" if tags else name
        if key not in self.counters:
            self.counters[key] = 0
        self.counters[key] += value
    
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timing metric"""
        key = f"{name}:{tags}" if tags else name
        if key not in self.timers:
            self.timers[key] = []
        self.timers[key].append(duration)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        key = f"{name}:{tags}" if tags else name
        self.metrics[key] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return {
            "counters": self.counters,
            "timers": self.timers,
            "gauges": self.metrics
        }


class StructuredLogger:
    """Structured logging utility"""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create structured formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self._log("INFO", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self._log("ERROR", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self._log("WARNING", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        self._log("DEBUG", message, **kwargs)
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method"""
        extra_data = {
            "service": self.service_name,
            "timestamp": time.time(),
            **kwargs
        }
        
        log_message = f"{message} | {extra_data}"
        getattr(self.logger, level.lower())(log_message)


def timing_decorator(metrics_collector: Optional[MetricsCollector] = None):
    """Decorator to measure function execution time"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metrics_collector:
                    metrics_collector.record_timing(func.__name__, duration)
        return wrapper
    return decorator


@contextmanager
def timing_context(name: str, metrics_collector: Optional[MetricsCollector] = None):
    """Context manager for timing operations"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if metrics_collector:
            metrics_collector.record_timing(name, duration)


class HealthChecker:
    """Health check utility"""
    
    def __init__(self):
        self.checks = {}
    
    def add_check(self, name: str, check_func: Callable[[], bool]):
        """Add a health check function"""
        self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "healthy": result
                }
                if not result:
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "healthy": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": time.time()
        }
