#!/usr/bin/env python3
"""
Test Runner for Energy Tracking System
Provides unified test execution across all components
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Optional

class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

class TestRunner:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: Dict[str, bool] = {}
    
    def print_colored(self, message: str, color: str = Colors.NC):
        print(f"{color}{message}{Colors.NC}")
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> bool:
        """Run a command and return success status"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            self.print_colored("❌ Command timed out after 5 minutes", Colors.RED)
            return False
        except Exception as e:
            self.print_colored(f"❌ Command failed: {e}", Colors.RED)
            return False
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        self.print_colored("🔍 Checking dependencies...", Colors.BLUE)
        
        # Check Python dependencies
        required_packages = ['pytest', 'pytest-asyncio', 'pytest-cov', 'httpx']
        missing_packages = []
        
        for package in required_packages:
            try:
                subprocess.run([sys.executable, '-c', f'import {package}'], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError:
                missing_packages.append(package)
        
        if missing_packages:
            self.print_colored(f"❌ Missing packages: {', '.join(missing_packages)}", Colors.RED)
            self.print_colored("Run: pip install -r test-requirements.txt", Colors.YELLOW)
            return False
        
        # Check if frontend dependencies are installed
        frontend_path = self.project_root / "frontend"
        if frontend_path.exists():
            node_modules = frontend_path / "node_modules"
            if not node_modules.exists():
                self.print_colored("❌ Frontend dependencies not installed", Colors.RED)
                self.print_colored("Run: cd frontend && npm install", Colors.YELLOW)
                return False
        
        self.print_colored("✅ All dependencies are installed", Colors.GREEN)
        return True
    
    def install_dependencies(self) -> bool:
        """Install test dependencies"""
        self.print_colored("📦 Installing test dependencies...", Colors.BLUE)
        
        # Install Python dependencies
        success = self.run_command([
            sys.executable, '-m', 'pip', 'install', '-r', 'test-requirements.txt'
        ])
        
        if not success:
            return False
        
        # Install frontend dependencies if frontend exists
        frontend_path = self.project_root / "frontend"
        if frontend_path.exists():
            success = self.run_command(['npm', 'install'], cwd=frontend_path)
            if not success:
                return False
        
        self.print_colored("✅ Dependencies installed successfully", Colors.GREEN)
        return True
    
    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        self.print_colored("🧪 Running unit tests...", Colors.BLUE)
        
        success = self.run_command([
            sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '-m', 'unit'
        ])
        
        self.results['unit'] = success
        
        if success:
            self.print_colored("✅ Unit tests passed", Colors.GREEN)
        else:
            self.print_colored("❌ Unit tests failed", Colors.RED)
        
        return success
    
    def run_integration_tests(self) -> bool:
        """Run integration tests"""
        self.print_colored("🔗 Running integration tests...", Colors.BLUE)
        
        # Check if services are running
        if not self.check_services():
            self.print_colored("⚠️  Services not running, starting them...", Colors.YELLOW)
            if not self.start_services():
                return False
        
        success = self.run_command([
            sys.executable, '-m', 'pytest', 'tests/integration/', '-v', '-m', 'integration'
        ])
        
        self.results['integration'] = success
        
        if success:
            self.print_colored("✅ Integration tests passed", Colors.GREEN)
        else:
            self.print_colored("❌ Integration tests failed", Colors.RED)
        
        return success
    
    def run_frontend_tests(self) -> bool:
        """Run frontend tests"""
        self.print_colored("⚛️  Running frontend tests...", Colors.BLUE)
        
        frontend_path = self.project_root / "frontend"
        if not frontend_path.exists():
            self.print_colored("⚠️  Frontend directory not found, skipping", Colors.YELLOW)
            return True
        
        success = self.run_command(['npm', 'test', '--', '--run'], cwd=frontend_path)
        
        self.results['frontend'] = success
        
        if success:
            self.print_colored("✅ Frontend tests passed", Colors.GREEN)
        else:
            self.print_colored("❌ Frontend tests failed", Colors.RED)
        
        return success
    
    def run_coverage_tests(self) -> bool:
        """Run tests with coverage"""
        self.print_colored("📊 Running tests with coverage...", Colors.BLUE)
        
        success = self.run_command([
            sys.executable, '-m', 'pytest', 'tests/', 
            '--cov=services', '--cov-report=html', '--cov-report=term',
            '--cov-fail-under=80'
        ])
        
        self.results['coverage'] = success
        
        if success:
            self.print_colored("✅ Coverage tests passed", Colors.GREEN)
            self.print_colored("📋 Coverage report generated in htmlcov/", Colors.BLUE)
        else:
            self.print_colored("❌ Coverage tests failed", Colors.RED)
        
        return success
    
    def check_services(self) -> bool:
        """Check if services are running"""
        services = [
            ('http://localhost:8000/health', 'API Gateway'),
            ('http://localhost:8005/health', 'Auth Service'),
        ]
        
        import urllib.request
        
        for url, name in services:
            try:
                urllib.request.urlopen(url, timeout=5)
            except:
                return False
        
        return True
    
    def start_services(self) -> bool:
        """Start services using Docker Compose"""
        self.print_colored("🐳 Starting services with Docker Compose...", Colors.BLUE)
        
        success = self.run_command(['docker-compose', 'up', '-d'])
        
        if not success:
            return False
        
        # Wait for services to be ready
        self.print_colored("⏳ Waiting for services to be ready...", Colors.YELLOW)
        time.sleep(30)
        
        if self.check_services():
            self.print_colored("✅ Services are ready", Colors.GREEN)
            return True
        else:
            self.print_colored("❌ Services failed to start properly", Colors.RED)
            return False
    
    def print_summary(self):
        """Print test summary"""
        self.print_colored("\n" + "="*60, Colors.BLUE)
        self.print_colored("📋 TEST SUMMARY", Colors.BLUE)
        self.print_colored("="*60, Colors.BLUE)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for success in self.results.values() if success)
        
        for test_type, success in self.results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            color = Colors.GREEN if success else Colors.RED
            self.print_colored(f"{test_type.upper():.<20} {status}", color)
        
        self.print_colored("="*60, Colors.BLUE)
        
        if passed_tests == total_tests:
            self.print_colored(f"🎉 ALL TESTS PASSED ({passed_tests}/{total_tests})", Colors.GREEN)
        else:
            self.print_colored(f"⚠️  SOME TESTS FAILED ({passed_tests}/{total_tests})", Colors.RED)
        
        self.print_colored("="*60, Colors.BLUE)

def main():
    parser = argparse.ArgumentParser(description='Energy Tracking System Test Runner')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--frontend', action='store_true', help='Run frontend tests only')
    parser.add_argument('--coverage', action='store_true', help='Run coverage tests')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Find project root
    project_root = Path(__file__).parent
    
    # Initialize test runner
    runner = TestRunner(project_root)
    
    runner.print_colored("🚀 Energy Tracking System Test Runner", Colors.BLUE)
    runner.print_colored("="*50, Colors.BLUE)
    
    # Install dependencies if requested
    if args.install_deps or args.all:
        if not runner.install_dependencies():
            sys.exit(1)
    
    # Check dependencies
    if not runner.check_dependencies():
        runner.print_colored("Run with --install-deps to install missing dependencies", Colors.YELLOW)
        sys.exit(1)
    
    # Determine which tests to run
    if args.unit:
        runner.run_unit_tests()
    elif args.integration:
        runner.run_integration_tests()
    elif args.frontend:
        runner.run_frontend_tests()
    elif args.coverage:
        runner.run_coverage_tests()
    elif args.all:
        runner.run_unit_tests()
        runner.run_integration_tests()
        runner.run_frontend_tests()
        runner.run_coverage_tests()
    else:
        # Default: run unit and integration tests
        runner.run_unit_tests()
        runner.run_integration_tests()
    
    # Print summary
    runner.print_summary()
    
    # Exit with appropriate code
    if all(runner.results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
