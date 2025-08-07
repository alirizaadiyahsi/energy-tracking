#!/usr/bin/env python3
"""
Critical path tests for release validation
"""
import asyncio
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    details: Optional[Dict] = None


class CriticalPathTester:
    """Critical path functionality tester"""
    
    def __init__(self, api_url: str, frontend_url: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.frontend_url = frontend_url.rstrip('/') if frontend_url else None
        self.results: List[TestResult] = []
        
        # Test credentials
        self.test_user = {
            "email": "critical.test@example.com",
            "password": "CriticalTest123!",
            "first_name": "Critical",
            "last_name": "Test"
        }
        
        self.access_token = None
    
    async def run_all_critical_tests(self, timeout: int = 300, retry_attempts: int = 3) -> bool:
        """Run all critical path tests"""
        
        critical_tests = [
            ("test_system_health", "System Health Check"),
            ("test_user_authentication", "User Authentication"),
            ("test_device_operations", "Device Operations"),
            ("test_data_ingestion", "Data Ingestion"),
            ("test_analytics_endpoints", "Analytics Endpoints"),
            ("test_api_performance", "API Performance")
        ]
        
        if self.frontend_url:
            critical_tests.append(("test_frontend_accessibility", "Frontend Accessibility"))
        
        print(f"🧪 Running {len(critical_tests)} critical path tests...")
        
        passed_tests = 0
        
        for test_method, test_name in critical_tests:
            print(f"  Running: {test_name}")
            
            for attempt in range(retry_attempts):
                try:
                    start_time = time.time()
                    method = getattr(self, test_method)
                    success = await method()
                    duration = time.time() - start_time
                    
                    if success:
                        print(f"    ✅ {test_name} passed ({duration:.2f}s)")
                        passed_tests += 1
                        break
                    else:
                        if attempt < retry_attempts - 1:
                            print(f"    ⚠️  {test_name} failed, retrying... (attempt {attempt + 1}/{retry_attempts})")
                            await asyncio.sleep(2)
                        else:
                            print(f"    ❌ {test_name} failed after {retry_attempts} attempts")
                            
                except Exception as e:
                    duration = time.time() - start_time
                    error_msg = str(e)
                    
                    self.results.append(TestResult(
                        name=test_name,
                        passed=False,
                        duration=duration,
                        error=error_msg
                    ))
                    
                    if attempt < retry_attempts - 1:
                        print(f"    ⚠️  {test_name} error, retrying... ({error_msg})")
                        await asyncio.sleep(2)
                    else:
                        print(f"    ❌ {test_name} error: {error_msg}")
                    break
        
        success_rate = (passed_tests / len(critical_tests)) * 100
        print(f"\n📊 Critical Path Results: {passed_tests}/{len(critical_tests)} passed ({success_rate:.1f}%)")
        
        return passed_tests == len(critical_tests)
    
    async def test_system_health(self) -> bool:
        """Test system health endpoints"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = time.time()
                response = await client.get(f"{self.api_url}/health")
                response_time = (time.time() - start_time) * 1000
                
                success = response.status_code == 200
                
                self.results.append(TestResult(
                    name="System Health Check",
                    passed=success,
                    duration=time.time() - start_time,
                    response_time=response_time,
                    status_code=response.status_code,
                    details=response.json() if success else None
                ))
                
                return success
                
        except Exception as e:
            self.results.append(TestResult(
                name="System Health Check",
                passed=False,
                duration=0,
                error=str(e)
            ))
            return False
    
    async def test_user_authentication(self) -> bool:
        """Test user authentication flow"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to register user (might already exist)
                try:
                    await client.post(f"{self.api_url}/auth/register", json=self.test_user)
                except:
                    pass  # User might already exist
                
                # Login
                start_time = time.time()
                login_data = {
                    "username": self.test_user["email"],
                    "password": self.test_user["password"]
                }
                
                response = await client.post(
                    f"{self.api_url}/auth/login",
                    data=login_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code != 200:
                    self.results.append(TestResult(
                        name="User Authentication",
                        passed=False,
                        duration=time.time() - start_time,
                        response_time=response_time,
                        status_code=response.status_code,
                        error="Login failed"
                    ))
                    return False
                
                # Extract token
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                
                if not self.access_token:
                    self.results.append(TestResult(
                        name="User Authentication",
                        passed=False,
                        duration=time.time() - start_time,
                        error="No access token received"
                    ))
                    return False
                
                # Verify token
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = await client.get(f"{self.api_url}/auth/me", headers=headers)
                
                success = response.status_code == 200
                
                self.results.append(TestResult(
                    name="User Authentication",
                    passed=success,
                    duration=time.time() - start_time,
                    response_time=response_time,
                    status_code=response.status_code
                ))
                
                return success
                
        except Exception as e:
            self.results.append(TestResult(
                name="User Authentication",
                passed=False,
                duration=0,
                error=str(e)
            ))
            return False
    
    async def test_device_operations(self) -> bool:
        """Test device management operations"""
        if not self.access_token:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                # List devices
                start_time = time.time()
                response = await client.get(f"{self.api_url}/devices/", headers=headers)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code not in [200, 404]:
                    self.results.append(TestResult(
                        name="Device Operations",
                        passed=False,
                        duration=time.time() - start_time,
                        response_time=response_time,
                        status_code=response.status_code,
                        error="Device listing failed"
                    ))
                    return False
                
                # Create test device
                device_data = {
                    "name": "Critical Test Device",
                    "type": "smart_meter",
                    "location": "Test Location"
                }
                
                response = await client.post(
                    f"{self.api_url}/devices/",
                    json=device_data,
                    headers=headers
                )
                
                success = response.status_code in [201, 409]  # 409 if already exists
                
                self.results.append(TestResult(
                    name="Device Operations",
                    passed=success,
                    duration=time.time() - start_time,
                    response_time=response_time,
                    status_code=response.status_code
                ))
                
                return success
                
        except Exception as e:
            self.results.append(TestResult(
                name="Device Operations",
                passed=False,
                duration=0,
                error=str(e)
            ))
            return False
    
    async def test_data_ingestion(self) -> bool:
        """Test data ingestion endpoints"""
        if not self.access_token:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                # Test data ingestion
                start_time = time.time()
                reading_data = {
                    "device_id": "test-device-001",
                    "timestamp": "2024-01-15T12:00:00Z",
                    "energy_consumed": 125.5,
                    "power": 2.5
                }
                
                response = await client.post(
                    f"{self.api_url}/data-ingestion/readings",
                    json=reading_data,
                    headers=headers
                )
                response_time = (time.time() - start_time) * 1000
                
                success = response.status_code in [201, 202, 404]  # 404 acceptable if endpoint not available
                
                self.results.append(TestResult(
                    name="Data Ingestion",
                    passed=success,
                    duration=time.time() - start_time,
                    response_time=response_time,
                    status_code=response.status_code
                ))
                
                return success
                
        except Exception as e:
            self.results.append(TestResult(
                name="Data Ingestion",
                passed=False,
                duration=0,
                error=str(e)
            ))
            return False
    
    async def test_analytics_endpoints(self) -> bool:
        """Test analytics endpoints"""
        if not self.access_token:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                # Test analytics endpoints
                start_time = time.time()
                response = await client.get(
                    f"{self.api_url}/analytics/consumption/trends",
                    params={"start_date": "2024-01-01", "end_date": "2024-01-02"},
                    headers=headers
                )
                response_time = (time.time() - start_time) * 1000
                
                success = response.status_code in [200, 404]  # 404 acceptable if no data
                
                self.results.append(TestResult(
                    name="Analytics Endpoints",
                    passed=success,
                    duration=time.time() - start_time,
                    response_time=response_time,
                    status_code=response.status_code
                ))
                
                return success
                
        except Exception as e:
            self.results.append(TestResult(
                name="Analytics Endpoints",
                passed=False,
                duration=0,
                error=str(e)
            ))
            return False
    
    async def test_api_performance(self) -> bool:
        """Test API performance under light load"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test multiple concurrent requests
                start_time = time.time()
                
                tasks = []
                for _ in range(10):
                    task = client.get(f"{self.api_url}/health")
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                duration = time.time() - start_time
                
                successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
                avg_response_time = (duration / len(responses)) * 1000
                
                success = len(successful_responses) >= 8  # At least 80% success rate
                
                self.results.append(TestResult(
                    name="API Performance",
                    passed=success,
                    duration=duration,
                    response_time=avg_response_time,
                    details={
                        "total_requests": len(responses),
                        "successful_requests": len(successful_responses),
                        "success_rate": len(successful_responses) / len(responses) * 100
                    }
                ))
                
                return success
                
        except Exception as e:
            self.results.append(TestResult(
                name="API Performance",
                passed=False,
                duration=0,
                error=str(e)
            ))
            return False
    
    async def test_frontend_accessibility(self) -> bool:
        """Test frontend accessibility"""
        if not self.frontend_url:
            return True  # Skip if no frontend URL
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = time.time()
                response = await client.get(self.frontend_url)
                response_time = (time.time() - start_time) * 1000
                
                success = response.status_code == 200
                
                self.results.append(TestResult(
                    name="Frontend Accessibility",
                    passed=success,
                    duration=time.time() - start_time,
                    response_time=response_time,
                    status_code=response.status_code
                ))
                
                return success
                
        except Exception as e:
            self.results.append(TestResult(
                name="Frontend Accessibility",
                passed=False,
                duration=0,
                error=str(e)
            ))
            return False


async def main():
    parser = argparse.ArgumentParser(description='Critical Path Tests')
    parser.add_argument('--api-url', required=True, help='API base URL')
    parser.add_argument('--frontend-url', help='Frontend base URL')
    parser.add_argument('--timeout', type=int, default=300, help='Test timeout in seconds')
    parser.add_argument('--retry-attempts', type=int, default=3, help='Number of retry attempts')
    parser.add_argument('--output', help='Output file for results')
    parser.add_argument('--post-release-validation', action='store_true', 
                       help='Run post-release validation tests')
    
    args = parser.parse_args()
    
    tester = CriticalPathTester(args.api_url, args.frontend_url)
    
    print(f"🚀 Starting critical path tests against {args.api_url}")
    if args.frontend_url:
        print(f"   Frontend: {args.frontend_url}")
    
    start_time = time.time()
    success = await tester.run_all_critical_tests(args.timeout, args.retry_attempts)
    total_duration = time.time() - start_time
    
    # Generate results
    results = {
        "timestamp": time.time(),
        "api_url": args.api_url,
        "frontend_url": args.frontend_url,
        "total_duration": total_duration,
        "success": success,
        "tests": [asdict(result) for result in tester.results]
    }
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Results saved to {args.output}")
    
    print(f"\n🏁 Critical path tests completed in {total_duration:.2f}s")
    print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
