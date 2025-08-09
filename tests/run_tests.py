#!/usr/bin/env python3
"""
Test runner for the Energy Tracking System
Provides a unified interface for running different types of tests
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


class Colors:
    """ANSI color codes for colored output"""

    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class TestRunner:
    """Main test runner class"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.results: Dict[str, bool] = {}

    def print_colored(self, message: str, color: str = Colors.WHITE) -> None:
        """Print colored message"""
        print(f"{color}{message}{Colors.END}")

    def print_header(self, title: str) -> None:
        """Print section header"""
        self.print_colored(f"\n{'='*60}", Colors.BLUE)
        self.print_colored(f"{title}", Colors.BOLD + Colors.BLUE)
        self.print_colored(f"{'='*60}", Colors.BLUE)

    def run_command(self, command: List[str], cwd: Path = None) -> bool:
        """Run a command and return success status"""
        try:
            self.print_colored(f"Running: {' '.join(command)}", Colors.CYAN)
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            if result.returncode == 0:
                self.print_colored("✅ Command succeeded", Colors.GREEN)
                if result.stdout.strip():
                    print(result.stdout)
                return True
            else:
                self.print_colored("❌ Command failed", Colors.RED)
                if result.stderr.strip():
                    print(result.stderr)
                if result.stdout.strip():
                    print(result.stdout)
                return False

        except subprocess.TimeoutExpired:
            self.print_colored("❌ Command timed out", Colors.RED)
            return False
        except Exception as e:
            self.print_colored(f"❌ Command error: {e}", Colors.RED)
            return False

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        self.print_header("Checking Dependencies")

        # Check Python packages
        required_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "httpx",
            "factory-boy",
            "faker",
            "testcontainers",
        ]

        missing_packages = []
        for package in required_packages:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", f'import {package.replace("-", "_")}'],
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    missing_packages.append(package)
            except Exception:
                missing_packages.append(package)

        if missing_packages:
            self.print_colored(
                f"❌ Missing packages: {', '.join(missing_packages)}", Colors.RED
            )
            self.print_colored(
                "Run: pip install -r tests/test-requirements.txt", Colors.YELLOW
            )
            return False

        self.print_colored("✅ All dependencies are installed", Colors.GREEN)
        return True

    def install_dependencies(self) -> bool:
        """Install test dependencies"""
        self.print_header("Installing Test Dependencies")

        requirements_file = self.tests_dir / "test-requirements.txt"
        if not requirements_file.exists():
            self.print_colored("❌ test-requirements.txt not found", Colors.RED)
            return False

        success = self.run_command(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        )

        if success:
            self.print_colored("✅ Dependencies installed successfully", Colors.GREEN)
        else:
            self.print_colored("❌ Failed to install dependencies", Colors.RED)

        return success

    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        self.print_header("Running Unit Tests")

        success = self.run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                str(self.tests_dir / "unit"),
                "-v",
                "-m",
                "unit",
                "--tb=short",
            ]
        )

        self.results["unit"] = success

        if success:
            self.print_colored("✅ Unit tests passed", Colors.GREEN)
        else:
            self.print_colored("❌ Unit tests failed", Colors.RED)

        return success

    def run_integration_tests(self) -> bool:
        """Run integration tests"""
        self.print_header("Running Integration Tests")

        # Check if Docker is available for integration tests
        docker_available = self.run_command(["docker", "--version"])
        if not docker_available:
            self.print_colored(
                "⚠️  Docker not available, skipping integration tests", Colors.YELLOW
            )
            return True

        success = self.run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                str(self.tests_dir / "integration"),
                "-v",
                "-m",
                "integration",
                "--tb=short",
            ]
        )

        self.results["integration"] = success

        if success:
            self.print_colored("✅ Integration tests passed", Colors.GREEN)
        else:
            self.print_colored("❌ Integration tests failed", Colors.RED)

        return success

    def run_performance_tests(self) -> bool:
        """Run performance tests"""
        self.print_header("Running Performance Tests")

        success = self.run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                str(self.tests_dir / "performance"),
                "-v",
                "-m",
                "performance",
                "--tb=short",
            ]
        )

        self.results["performance"] = success

        if success:
            self.print_colored("✅ Performance tests passed", Colors.GREEN)
        else:
            self.print_colored("❌ Performance tests failed", Colors.RED)

        return success

    def run_e2e_tests(self) -> bool:
        """Run end-to-end tests"""
        self.print_header("Running End-to-End Tests")

        success = self.run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                str(self.tests_dir / "e2e"),
                "-v",
                "-m",
                "e2e",
                "--tb=short",
            ]
        )

        self.results["e2e"] = success

        if success:
            self.print_colored("✅ E2E tests passed", Colors.GREEN)
        else:
            self.print_colored("❌ E2E tests failed", Colors.RED)

        return success

    def run_coverage_tests(self) -> bool:
        """Run tests with coverage"""
        self.print_header("Running Coverage Tests")

        success = self.run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                str(self.tests_dir),
                "--cov=services",
                "--cov-report=html",
                "--cov-report=term",
                "--cov-fail-under=80",
                "-v",
            ]
        )

        self.results["coverage"] = success

        if success:
            self.print_colored("✅ Coverage tests passed", Colors.GREEN)
            self.print_colored("📊 Coverage report generated in htmlcov/", Colors.BLUE)
        else:
            self.print_colored("❌ Coverage tests failed", Colors.RED)

        return success

    def run_security_tests(self) -> bool:
        """Run security tests"""
        self.print_header("Running Security Tests")

        # Run bandit for security issues
        bandit_success = self.run_command(
            [sys.executable, "-m", "bandit", "-r", "services/", "-f", "json"]
        )

        # Run safety for known vulnerabilities
        safety_success = self.run_command([sys.executable, "-m", "safety", "check"])

        # Run security-specific tests
        pytest_success = self.run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                str(self.tests_dir),
                "-v",
                "-m",
                "security",
                "--tb=short",
            ]
        )

        success = bandit_success and safety_success and pytest_success
        self.results["security"] = success

        if success:
            self.print_colored("✅ Security tests passed", Colors.GREEN)
        else:
            self.print_colored("❌ Security tests failed", Colors.RED)

        return success

    def run_specific_service(self, service: str, test_type: str = "all") -> bool:
        """Run tests for a specific service"""
        self.print_header(f"Running {test_type.title()} Tests for {service}")

        if test_type == "all":
            test_path = str(self.tests_dir / "**" / service)
        else:
            test_path = str(self.tests_dir / test_type / service)

        success = self.run_command(
            [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"]
        )

        self.results[f"{service}_{test_type}"] = success

        if success:
            self.print_colored(f"✅ {service} {test_type} tests passed", Colors.GREEN)
        else:
            self.print_colored(f"❌ {service} {test_type} tests failed", Colors.RED)

        return success

    def print_summary(self) -> None:
        """Print test results summary"""
        self.print_header("Test Results Summary")

        if not self.results:
            self.print_colored("No tests were run", Colors.YELLOW)
            return

        passed = sum(1 for result in self.results.values() if result)
        total = len(self.results)

        self.print_colored(
            f"Tests passed: {passed}/{total}",
            Colors.GREEN if passed == total else Colors.YELLOW,
        )

        for test_name, result in self.results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            color = Colors.GREEN if result else Colors.RED
            self.print_colored(f"{test_name}: {status}", color)

        if passed == total:
            self.print_colored("\n🎉 All tests passed!", Colors.GREEN + Colors.BOLD)
        else:
            self.print_colored(
                f"\n⚠️  {total - passed} test(s) failed", Colors.RED + Colors.BOLD
            )

    def cleanup(self) -> None:
        """Cleanup after test runs"""
        self.print_colored("🧹 Cleaning up...", Colors.BLUE)

        # Clean up Docker containers if needed
        try:
            subprocess.run(
                ["docker-compose", "-f", "docker-compose.test.yml", "down"],
                cwd=self.project_root,
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass  # Ignore cleanup errors


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Energy Tracking System Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py --all                 # Run all tests
  python tests/run_tests.py --unit                # Run unit tests only
  python tests/run_tests.py --integration         # Run integration tests only
  python tests/run_tests.py --coverage            # Run with coverage
  python tests/run_tests.py --service auth-service --type unit
  python tests/run_tests.py --install-deps        # Install dependencies
        """,
    )

    # Test type options
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--performance", action="store_true", help="Run performance tests only"
    )
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage"
    )
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")

    # Service-specific options
    parser.add_argument("--service", help="Run tests for specific service")
    parser.add_argument(
        "--type",
        default="all",
        choices=["unit", "integration", "performance", "e2e", "all"],
        help="Type of tests to run for specific service",
    )

    # Utility options
    parser.add_argument(
        "--install-deps", action="store_true", help="Install test dependencies"
    )
    parser.add_argument(
        "--check-deps", action="store_true", help="Check if dependencies are installed"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Find project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Initialize test runner
    runner = TestRunner(project_root)

    runner.print_colored(
        "🚀 Energy Tracking System Test Runner", Colors.BLUE + Colors.BOLD
    )
    runner.print_colored(f"Project root: {project_root}", Colors.CYAN)

    start_time = time.time()

    try:
        # Install dependencies if requested
        if args.install_deps:
            if not runner.install_dependencies():
                sys.exit(1)

        # Check dependencies if requested
        if args.check_deps:
            if not runner.check_dependencies():
                sys.exit(1)
            return

        # Check dependencies before running tests
        if not args.install_deps and not runner.check_dependencies():
            runner.print_colored(
                "Run with --install-deps to install missing dependencies", Colors.YELLOW
            )
            sys.exit(1)

        # Run specific service tests
        if args.service:
            success = runner.run_specific_service(args.service, args.type)
            runner.print_summary()
            sys.exit(0 if success else 1)

        # Run tests based on arguments
        success_count = 0
        total_count = 0

        if args.all or (
            not any(
                [
                    args.unit,
                    args.integration,
                    args.performance,
                    args.e2e,
                    args.coverage,
                    args.security,
                ]
            )
        ):
            # Run all test types
            test_functions = [
                runner.run_unit_tests,
                runner.run_integration_tests,
                runner.run_performance_tests,
                runner.run_e2e_tests,
                runner.run_coverage_tests,
                runner.run_security_tests,
            ]
        else:
            # Run specific test types
            test_functions = []
            if args.unit:
                test_functions.append(runner.run_unit_tests)
            if args.integration:
                test_functions.append(runner.run_integration_tests)
            if args.performance:
                test_functions.append(runner.run_performance_tests)
            if args.e2e:
                test_functions.append(runner.run_e2e_tests)
            if args.coverage:
                test_functions.append(runner.run_coverage_tests)
            if args.security:
                test_functions.append(runner.run_security_tests)

        # Execute test functions
        for test_func in test_functions:
            total_count += 1
            if test_func():
                success_count += 1

        # Print final summary
        end_time = time.time()
        duration = end_time - start_time

        runner.print_summary()
        runner.print_colored(
            f"\n⏱️  Total execution time: {duration:.2f} seconds", Colors.BLUE
        )

        # Exit with appropriate code
        sys.exit(0 if success_count == total_count else 1)

    except KeyboardInterrupt:
        runner.print_colored("\n❌ Tests interrupted by user", Colors.RED)
        sys.exit(1)

    finally:
        runner.cleanup()


if __name__ == "__main__":
    main()
