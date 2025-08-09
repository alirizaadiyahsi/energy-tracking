#!/usr/bin/env python3
"""
End-to-End Test Runner for Energy Tracking System
"""
import asyncio
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class TestResult:
    """Test result data structure"""

    name: str
    passed: bool
    duration: float
    error: Optional[str] = None
    details: Optional[Dict] = None


class E2ETestRunner:
    """End-to-End test runner for the Energy Tracking System"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_gateway_url = f"{base_url}/api/v1"
        self.auth_url = f"{self.api_gateway_url}/auth"
        self.devices_url = f"{self.api_gateway_url}/devices"
        self.analytics_url = f"{self.api_gateway_url}/analytics"

        # Test user credentials
        self.test_user = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

        # Store authentication tokens
        self.access_token = None
        self.refresh_token = None

        # Test results
        self.results: List[TestResult] = []

    def print_colored(self, message: str, color_code: str = "0") -> None:
        """Print colored message"""
        print(f"\033[{color_code}m{message}\033[0m")

    async def run_all_tests(self) -> bool:
        """Run all E2E tests"""
        self.print_colored("🎭 Starting End-to-End Tests", "95")
        self.print_colored(f"Target: {self.base_url}", "96")

        # Define test sequence
        test_methods = [
            ("health_check", "System Health Check"),
            ("user_registration_flow", "User Registration Flow"),
            ("user_authentication_flow", "User Authentication Flow"),
            ("device_management_flow", "Device Management Flow"),
            ("data_ingestion_flow", "Data Ingestion Flow"),
            ("analytics_flow", "Analytics Flow"),
            ("user_logout_flow", "User Logout Flow"),
        ]

        total_tests = len(test_methods)
        passed_tests = 0

        for i, (method_name, test_name) in enumerate(test_methods, 1):
            self.print_colored(f"\n[{i}/{total_tests}] {test_name}", "94")

            try:
                start_time = time.time()
                method = getattr(self, method_name)
                success = await method()
                duration = time.time() - start_time

                if success:
                    self.print_colored(
                        f"✅ {test_name} - PASSED ({duration:.2f}s)", "92"
                    )
                    self.results.append(TestResult(test_name, True, duration))
                    passed_tests += 1
                else:
                    self.print_colored(
                        f"❌ {test_name} - FAILED ({duration:.2f}s)", "91"
                    )
                    self.results.append(TestResult(test_name, False, duration))

            except Exception as e:
                duration = time.time() - start_time
                self.print_colored(
                    f"❌ {test_name} - ERROR: {str(e)} ({duration:.2f}s)", "91"
                )
                self.results.append(TestResult(test_name, False, duration, str(e)))

        # Print summary
        self.print_summary(passed_tests, total_tests)
        return passed_tests == total_tests

    def print_summary(self, passed: int, total: int) -> None:
        """Print test summary"""
        self.print_colored(f"\n{'='*60}", "95")
        self.print_colored("E2E TEST SUMMARY", "95")
        self.print_colored(f"{'='*60}", "95")

        success_rate = (passed / total * 100) if total > 0 else 0

        self.print_colored(
            f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)",
            "92" if passed == total else "93",
        )

        total_duration = sum(r.duration for r in self.results)
        self.print_colored(f"Total Duration: {total_duration:.2f}s", "96")

        # Show failed tests
        failed_tests = [r for r in self.results if not r.passed]
        if failed_tests:
            self.print_colored(f"\n❌ Failed Tests:", "91")
            for result in failed_tests:
                self.print_colored(f"  - {result.name}", "91")
                if result.error:
                    self.print_colored(f"    Error: {result.error}", "91")

    async def health_check(self) -> bool:
        """Test system health endpoints"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check API Gateway health
                response = await client.get(f"{self.base_url}/health")
                if response.status_code != 200:
                    self.print_colored(
                        f"API Gateway health check failed: {response.status_code}", "91"
                    )
                    return False

                # Check individual services if available
                services = ["auth", "data-ingestion", "analytics"]
                for service in services:
                    try:
                        response = await client.get(
                            f"{self.api_gateway_url}/{service}/health"
                        )
                        if response.status_code == 200:
                            self.print_colored(f"  ✅ {service} service healthy", "92")
                    except Exception:
                        self.print_colored(f"  ⚠️  {service} service unavailable", "93")

                return True

        except Exception as e:
            self.print_colored(f"Health check failed: {e}", "91")
            return False

    async def user_registration_flow(self) -> bool:
        """Test complete user registration flow"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Register new user
                response = await client.post(
                    f"{self.auth_url}/register", json=self.test_user
                )

                if response.status_code not in [201, 409]:  # 409 if user already exists
                    self.print_colored(
                        f"Registration failed: {response.status_code} - {response.text}",
                        "91",
                    )
                    return False

                if response.status_code == 201:
                    self.print_colored("  ✅ New user registered successfully", "92")
                else:
                    self.print_colored("  ✅ User already exists (continuing)", "92")

                return True

        except Exception as e:
            self.print_colored(f"Registration flow failed: {e}", "91")
            return False

    async def user_authentication_flow(self) -> bool:
        """Test user authentication flow"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Login
                login_data = {
                    "username": self.test_user["email"],
                    "password": self.test_user["password"],
                }

                response = await client.post(
                    f"{self.auth_url}/login",
                    data=login_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    self.print_colored(
                        f"Login failed: {response.status_code} - {response.text}", "91"
                    )
                    return False

                # Extract tokens
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")

                if not self.access_token:
                    self.print_colored("No access token received", "91")
                    return False

                self.print_colored("  ✅ Authentication successful", "92")

                # Verify token by accessing protected endpoint
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = await client.get(f"{self.auth_url}/me", headers=headers)

                if response.status_code != 200:
                    self.print_colored(
                        f"Token verification failed: {response.status_code}", "91"
                    )
                    return False

                user_data = response.json()
                if user_data.get("email") != self.test_user["email"]:
                    self.print_colored("User data mismatch", "91")
                    return False

                self.print_colored("  ✅ Token verification successful", "92")
                return True

        except Exception as e:
            self.print_colored(f"Authentication flow failed: {e}", "91")
            return False

    async def device_management_flow(self) -> bool:
        """Test device management operations"""
        if not self.access_token:
            self.print_colored("No authentication token available", "91")
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}

                # Create a test device
                device_data = {
                    "name": "Test Smart Meter",
                    "type": "smart_meter",
                    "location": "Test Location",
                    "metadata": {"model": "TestMeter-2024", "manufacturer": "TestCorp"},
                }

                response = await client.post(
                    f"{self.devices_url}/", json=device_data, headers=headers
                )

                if response.status_code not in [201, 409]:
                    self.print_colored(
                        f"Device creation failed: {response.status_code} - {response.text}",
                        "91",
                    )
                    return False

                device = response.json()
                device_id = device.get("id")

                if not device_id:
                    self.print_colored("No device ID returned", "91")
                    return False

                self.print_colored(f"  ✅ Device created: {device_id}", "92")

                # List devices
                response = await client.get(f"{self.devices_url}/", headers=headers)

                if response.status_code != 200:
                    self.print_colored(
                        f"Device listing failed: {response.status_code}", "91"
                    )
                    return False

                devices = response.json()
                if not any(d.get("id") == device_id for d in devices):
                    self.print_colored("Created device not found in list", "91")
                    return False

                self.print_colored("  ✅ Device listing successful", "92")

                # Get specific device
                response = await client.get(
                    f"{self.devices_url}/{device_id}", headers=headers
                )

                if response.status_code != 200:
                    self.print_colored(
                        f"Device retrieval failed: {response.status_code}", "91"
                    )
                    return False

                retrieved_device = response.json()
                if retrieved_device.get("name") != device_data["name"]:
                    self.print_colored("Device data mismatch", "91")
                    return False

                self.print_colored("  ✅ Device retrieval successful", "92")

                # Store device_id for later tests
                self.test_device_id = device_id

                return True

        except Exception as e:
            self.print_colored(f"Device management flow failed: {e}", "91")
            return False

    async def data_ingestion_flow(self) -> bool:
        """Test data ingestion pipeline"""
        if not self.access_token or not hasattr(self, "test_device_id"):
            self.print_colored("Prerequisites not met for data ingestion test", "91")
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}

                # Send energy reading data
                reading_data = {
                    "device_id": self.test_device_id,
                    "timestamp": "2024-01-15T12:00:00Z",
                    "energy_consumed": 125.5,
                    "power": 2.5,
                    "voltage": 230.0,
                    "current": 10.9,
                    "metadata": {"quality": "good", "source": "e2e_test"},
                }

                response = await client.post(
                    f"{self.api_gateway_url}/data-ingestion/readings",
                    json=reading_data,
                    headers=headers,
                )

                if response.status_code not in [201, 202]:
                    self.print_colored(
                        f"Data ingestion failed: {response.status_code} - {response.text}",
                        "91",
                    )
                    return False

                self.print_colored("  ✅ Energy reading ingested", "92")

                # Send multiple readings
                batch_data = {
                    "readings": [
                        {
                            "device_id": self.test_device_id,
                            "timestamp": "2024-01-15T12:15:00Z",
                            "energy_consumed": 128.0,
                            "power": 2.6,
                        },
                        {
                            "device_id": self.test_device_id,
                            "timestamp": "2024-01-15T12:30:00Z",
                            "energy_consumed": 130.5,
                            "power": 2.7,
                        },
                    ]
                }

                response = await client.post(
                    f"{self.api_gateway_url}/data-ingestion/readings/batch",
                    json=batch_data,
                    headers=headers,
                )

                if response.status_code not in [201, 202]:
                    self.print_colored(
                        f"Batch ingestion failed: {response.status_code} - {response.text}",
                        "91",
                    )
                    return False

                self.print_colored("  ✅ Batch readings ingested", "92")

                # Wait a moment for data processing
                await asyncio.sleep(2)

                return True

        except Exception as e:
            self.print_colored(f"Data ingestion flow failed: {e}", "91")
            return False

    async def analytics_flow(self) -> bool:
        """Test analytics and reporting functionality"""
        if not self.access_token or not hasattr(self, "test_device_id"):
            self.print_colored("Prerequisites not met for analytics test", "91")
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}

                # Get device analytics
                response = await client.get(
                    f"{self.analytics_url}/devices/{self.test_device_id}/summary",
                    headers=headers,
                )

                if response.status_code not in [
                    200,
                    404,
                ]:  # 404 acceptable if no data yet
                    self.print_colored(
                        f"Device analytics failed: {response.status_code} - {response.text}",
                        "91",
                    )
                    return False

                if response.status_code == 200:
                    analytics = response.json()
                    self.print_colored(
                        f"  ✅ Device analytics retrieved: {analytics}", "92"
                    )
                else:
                    self.print_colored(
                        "  ✅ Device analytics endpoint accessible (no data yet)", "92"
                    )

                # Get consumption trends
                response = await client.get(
                    f"{self.analytics_url}/consumption/trends",
                    params={
                        "start_date": "2024-01-15",
                        "end_date": "2024-01-15",
                        "device_id": self.test_device_id,
                    },
                    headers=headers,
                )

                if response.status_code not in [200, 404]:
                    self.print_colored(
                        f"Consumption trends failed: {response.status_code} - {response.text}",
                        "91",
                    )
                    return False

                self.print_colored("  ✅ Consumption trends endpoint accessible", "92")

                # Get energy efficiency metrics
                response = await client.get(
                    f"{self.analytics_url}/efficiency/metrics",
                    params={"device_id": self.test_device_id},
                    headers=headers,
                )

                if response.status_code not in [200, 404]:
                    self.print_colored(
                        f"Efficiency metrics failed: {response.status_code} - {response.text}",
                        "91",
                    )
                    return False

                self.print_colored("  ✅ Efficiency metrics endpoint accessible", "92")

                return True

        except Exception as e:
            self.print_colored(f"Analytics flow failed: {e}", "91")
            return False

    async def user_logout_flow(self) -> bool:
        """Test user logout flow"""
        if not self.access_token:
            self.print_colored("No authentication token available", "91")
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}

                # Logout
                response = await client.post(f"{self.auth_url}/logout", headers=headers)

                if response.status_code not in [200, 204]:
                    self.print_colored(
                        f"Logout failed: {response.status_code} - {response.text}", "91"
                    )
                    return False

                self.print_colored("  ✅ Logout successful", "92")

                # Verify token is invalidated
                response = await client.get(f"{self.auth_url}/me", headers=headers)

                if response.status_code != 401:
                    self.print_colored(
                        f"Token should be invalidated: {response.status_code}", "91"
                    )
                    return False

                self.print_colored("  ✅ Token invalidated", "92")

                # Clear tokens
                self.access_token = None
                self.refresh_token = None

                return True

        except Exception as e:
            self.print_colored(f"Logout flow failed: {e}", "91")
            return False


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Energy Tracking E2E Test Runner")
    parser.add_argument(
        "--host", default="http://localhost:8000", help="Base URL for the application"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Initialize runner
    runner = E2ETestRunner(args.host)

    try:
        # Run all tests
        success = await runner.run_all_tests()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        runner.print_colored("\n❌ E2E tests interrupted by user", "91")
        sys.exit(1)
    except Exception as e:
        runner.print_colored(f"❌ Error running E2E tests: {e}", "91")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
