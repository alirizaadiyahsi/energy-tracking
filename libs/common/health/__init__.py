"""
Common health check utilities for all microservices
"""

import time
import psutil
import asyncio
from typing import Dict, Any, Callable, List
from datetime import datetime, timezone


class HealthStatus:
    """Health status constants"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy" 
    DEGRADED = "degraded"


class BaseHealthCheck:
    """Base class for health checks"""
    
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
    
    async def check(self) -> Dict[str, Any]:
        """Perform the health check"""
        try:
            start_time = time.time()
            result = await asyncio.wait_for(self._check(), timeout=self.timeout)
            duration = time.time() - start_time
            
            return {
                "name": self.name,
                "status": HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": round(duration * 1000, 2),
                "details": await self._get_details() if result else {}
            }
        except asyncio.TimeoutError:
            return {
                "name": self.name,
                "status": HealthStatus.UNHEALTHY,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Health check timed out after {self.timeout}s"
            }
        except Exception as e:
            return {
                "name": self.name,
                "status": HealthStatus.UNHEALTHY,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    async def _check(self) -> bool:
        """Override this method to implement the actual check"""
        raise NotImplementedError
    
    async def _get_details(self) -> Dict[str, Any]:
        """Override this method to provide additional details"""
        return {}


class DatabaseHealthCheck(BaseHealthCheck):
    """Health check for database connectivity"""
    
    def __init__(self, db_connection, name: str = "database"):
        super().__init__(name)
        self.db_connection = db_connection
    
    async def _check(self) -> bool:
        """Check database connectivity"""
        try:
            # Try to execute a simple query
            if hasattr(self.db_connection, 'execute'):
                # SQLAlchemy connection
                await self.db_connection.execute("SELECT 1")
            else:
                # Custom connection - assume it has a ping method
                await self.db_connection.ping()
            return True
        except Exception:
            return False
    
    async def _get_details(self) -> Dict[str, Any]:
        """Get database details"""
        return {
            "connection_pool_size": getattr(self.db_connection, 'pool_size', 'unknown'),
            "connection_checked_out": getattr(self.db_connection, 'checked_out', 'unknown')
        }


class RedisHealthCheck(BaseHealthCheck):
    """Health check for Redis connectivity"""
    
    def __init__(self, redis_client, name: str = "redis"):
        super().__init__(name)
        self.redis_client = redis_client
    
    async def _check(self) -> bool:
        """Check Redis connectivity"""
        try:
            result = await self.redis_client.ping()
            return result is True
        except Exception:
            return False
    
    async def _get_details(self) -> Dict[str, Any]:
        """Get Redis details"""
        try:
            info = await self.redis_client.info()
            return {
                "used_memory": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients'),
                "uptime_in_seconds": info.get('uptime_in_seconds')
            }
        except Exception:
            return {}


class ExternalServiceHealthCheck(BaseHealthCheck):
    """Health check for external HTTP services"""
    
    def __init__(self, service_url: str, name: str, expected_status: int = 200):
        super().__init__(name)
        self.service_url = service_url
        self.expected_status = expected_status
    
    async def _check(self) -> bool:
        """Check external service health"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.service_url}/health",
                    timeout=self.timeout
                )
                return response.status_code == self.expected_status
        except Exception:
            return False


class SystemHealthCheck(BaseHealthCheck):
    """Health check for system resources"""
    
    def __init__(self, name: str = "system", 
                 cpu_threshold: float = 90.0, 
                 memory_threshold: float = 90.0,
                 disk_threshold: float = 90.0):
        super().__init__(name)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    async def _check(self) -> bool:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            return (cpu_percent < self.cpu_threshold and 
                   memory_percent < self.memory_threshold and
                   disk_percent < self.disk_threshold)
        except Exception:
            return False
    
    async def _get_details(self) -> Dict[str, Any]:
        """Get system resource details"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception:
            return {}


class HealthChecker:
    """Main health checker that aggregates multiple checks"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: List[BaseHealthCheck] = []
        self.start_time = time.time()
    
    def add_check(self, health_check: BaseHealthCheck):
        """Add a health check"""
        self.checks.append(health_check)
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return aggregated results"""
        if not self.checks:
            return {
                "service": self.service_name,
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": round(time.time() - self.start_time, 2),
                "checks": {},
                "message": "No health checks configured"
            }
        
        # Run all checks concurrently
        check_results = await asyncio.gather(
            *[check.check() for check in self.checks],
            return_exceptions=True
        )
        
        # Process results
        checks_detail = {}
        overall_healthy = True
        
        for i, result in enumerate(check_results):
            if isinstance(result, Exception):
                check_name = self.checks[i].name
                checks_detail[check_name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "error": str(result),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                overall_healthy = False
            else:
                checks_detail[result["name"]] = result
                if result["status"] != HealthStatus.HEALTHY:
                    overall_healthy = False
        
        return {
            "service": self.service_name,
            "status": HealthStatus.HEALTHY if overall_healthy else HealthStatus.UNHEALTHY,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "checks": checks_detail,
            "version": self._get_version()
        }
    
    def _get_version(self) -> str:
        """Get service version - override in subclasses"""
        import os
        return os.getenv("SERVICE_VERSION", "unknown")
