"""
HTTP client utilities for inter-service communication
"""

import asyncio
import time
from typing import Dict, Any, Optional, Union
import httpx
from .exceptions import ExternalServiceError


class ServiceClient:
    """HTTP client for inter-service communication"""
    
    def __init__(
        self, 
        base_url: str, 
        timeout: float = 30.0,
        retries: int = 3,
        auth_token: Optional[str] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retries = retries
        self.auth_token = auth_token
        self._client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
    
    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ServiceClient/1.0"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retries"""
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers(headers)
        
        for attempt in range(self.retries + 1):
            try:
                if not self._client:
                    self._client = httpx.AsyncClient(timeout=self.timeout)
                
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data if method.upper() != 'GET' else None,
                    params=params,
                    headers=request_headers
                )
                
                if response.status_code >= 400:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('detail', error_detail)
                    except:
                        pass
                    
                    raise ExternalServiceError(
                        self.base_url,
                        f"HTTP {response.status_code}: {error_detail}"
                    )
                
                return response.json() if response.content else {}
                
            except httpx.TimeoutException:
                if attempt == self.retries:
                    raise ExternalServiceError(self.base_url, "Request timeout")
                await asyncio.sleep(2 ** attempt)
                
            except httpx.RequestError as e:
                if attempt == self.retries:
                    raise ExternalServiceError(self.base_url, str(e))
                await asyncio.sleep(2 ** attempt)
    
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request("GET", endpoint, params=params, headers=headers)
    
    async def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request("POST", endpoint, data=data, headers=headers)
    
    async def put(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make PUT request"""
        return await self._make_request("PUT", endpoint, data=data, headers=headers)
    
    async def delete(
        self, 
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self._make_request("DELETE", endpoint, headers=headers)
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        try:
            response = await self.get("/health")
            return response.get("status") == "healthy"
        except:
            return False


class ServiceRegistry:
    """Registry for managing service endpoints"""
    
    def __init__(self):
        self.services: Dict[str, str] = {}
        self.clients: Dict[str, ServiceClient] = {}
    
    def register_service(self, name: str, base_url: str, auth_token: Optional[str] = None):
        """Register a service"""
        self.services[name] = base_url
        self.clients[name] = ServiceClient(base_url, auth_token=auth_token)
    
    def get_client(self, service_name: str) -> Optional[ServiceClient]:
        """Get client for a service"""
        return self.clients.get(service_name)
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get base URL for a service"""
        return self.services.get(service_name)
    
    async def check_all_services(self) -> Dict[str, bool]:
        """Check health of all registered services"""
        results = {}
        
        for name, client in self.clients.items():
            async with client:
                results[name] = await client.health_check()
        
        return results


# Global service registry instance
service_registry = ServiceRegistry()


def register_service(name: str, base_url: str, auth_token: Optional[str] = None):
    """Register a service in the global registry"""
    service_registry.register_service(name, base_url, auth_token)


def get_service_client(service_name: str) -> Optional[ServiceClient]:
    """Get service client from global registry"""
    return service_registry.get_client(service_name)
