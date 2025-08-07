#!/usr/bin/env python3
"""
Master Test Runner for Energy Tracking System
Coordinates and executes all test types: Unit, Integration, Performance, E2E
"""
import asyncio
import subprocess
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import configparser


@dataclass
class TestSuite:
    """Test suite configuration"""
    name: str
    description: str
    command: List[str]
    working_dir: str
    timeout: int = 300
    required: bool = True
    parallel: bool = False
    dependencies: List[str] = None


@dataclass
class TestResult:
    """Test execution result"""
    suite_name: str
    passed: bool
    duration: float
    output: str = ""
    error: str = ""
    exit_code: int = 0
    skipped: bool = False
    skip_reason: str = ""


class MasterTestRunner:
    """Master test runner that coordinates all test types"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.config_file = self.tests_dir / "test_config.ini"
        self.results: List[TestResult] = []
        
        # Load configuration
        self.config = self._load_config()
        
        # Define test suites
        self.test_suites = self._define_test_suites()
    
    def _load_config(self) -> configparser.ConfigParser:
        """Load test configuration"""
        config = configparser.ConfigParser()
        if self.config_file.exists():
            config.read(self.config_file)
        return config
    
    def _define_test_suites(self) -> Dict[str, TestSuite]:
        """Define all test suites"""
        python_exe = sys.executable
        
        return {
            "unit": TestSuite(
                name="unit",
                description="Unit Tests - Individual component testing",
                command=[python_exe, "-m", "pytest", "unit/", "-v", "--tb=short", "--cov=services", "--cov-report=term-missing"],
                working_dir=str(self.tests_dir),
                timeout=300,
                required=True
            ),
            
            "integration": TestSuite(
                name="integration",
                description="Integration Tests - Service interaction testing",
                command=[python_exe, "-m", "pytest", "integration/", "-v", "--tb=short"],
                working_dir=str(self.tests_dir),
                timeout=600,
                required=True,
                dependencies=["unit"]
            ),
            
            "performance": TestSuite(
                name="performance",
                description="Performance Tests - Load and stress testing",
                command=[python_exe, "performance/run_performance_tests.py", "--scenario", "light", "--headless"],
                working_dir=str(self.tests_dir),
                timeout=900,
                required=False
            ),
            
            "e2e-api": TestSuite(
                name="e2e-api",
                description="E2E API Tests - Complete workflow testing",
                command=[python_exe, "e2e/test_complete_flows.py"],
                working_dir=str(self.tests_dir),
                timeout=600,
                required=True,
                dependencies=["integration"]
            ),
            
            "e2e-browser": TestSuite(
                name="e2e-browser",
                description="E2E Browser Tests - Frontend workflow testing",
                command=[python_exe, "e2e/test_browser_flows.py", "--headless"],
                working_dir=str(self.tests_dir),
                timeout=900,
                required=False
            ),
            
            "security": TestSuite(
                name="security",
                description="Security Tests - Authentication and authorization",
                command=[python_exe, "-m", "pytest", "unit/", "-v", "-m", "security"],
                working_dir=str(self.tests_dir),
                timeout=300,
                required=True
            ),
            
            "lint": TestSuite(
                name="lint",
                description="Code Quality - Linting and formatting checks",
                command=[python_exe, "-m", "flake8", "--max-line-length=120", "--extend-ignore=E203,W503"],
                working_dir=str(self.project_root),
                timeout=120,
                required=False
            )
        }
    
    def print_colored(self, message: str, color_code: str = "0") -> None:
        """Print colored message"""
        print(f"\033[{color_code}m{message}\033[0m")
    
    def check_prerequisites(self) -> Tuple[bool, List[str]]:
        """Check if all prerequisites are met"""
        self.print_colored("🔍 Checking prerequisites...", "94")
        
        missing_packages = []
        required_packages = [
            "pytest", "pytest-asyncio", "pytest-cov", "pytest-mock",
            "httpx", "bcrypt", "PyJWT", "factory-boy", "faker"
        ]
        
        for package in required_packages:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", f"import {package.replace('-', '_')}"],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    missing_packages.append(package)
            except Exception:
                missing_packages.append(package)
        
        if missing_packages:
            self.print_colored(f"❌ Missing packages: {', '.join(missing_packages)}", "91")
            self.print_colored("Install with: pip install " + " ".join(missing_packages), "93")
            return False, missing_packages
        
        # Check if test files exist
        required_files = [
            self.tests_dir / "conftest.py",
            self.tests_dir / "pytest.ini"
        ]
        
        missing_files = [f for f in required_files if not f.exists()]
        if missing_files:
            self.print_colored(f"❌ Missing test files: {missing_files}", "91")
            return False, [str(f) for f in missing_files]
        
        self.print_colored("✅ Prerequisites check passed", "92")
        return True, []
    
    async def run_test_suite(self, suite: TestSuite) -> TestResult:
        """Run a single test suite"""
        self.print_colored(f"🧪 Running {suite.name}: {suite.description}", "94")
        
        start_time = time.time()
        
        try:
            # Run the test command
            process = await asyncio.create_subprocess_exec(
                *suite.command,
                cwd=suite.working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=None
            )
            
            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(),
                    timeout=suite.timeout
                )
                exit_code = process.returncode
                output = stdout.decode('utf-8', errors='replace') if stdout else ""
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                duration = time.time() - start_time
                return TestResult(
                    suite_name=suite.name,
                    passed=False,
                    duration=duration,
                    error=f"Test suite timed out after {suite.timeout}s",
                    exit_code=-1
                )
            
            duration = time.time() - start_time
            passed = exit_code == 0
            
            return TestResult(
                suite_name=suite.name,
                passed=passed,
                duration=duration,
                output=output,
                exit_code=exit_code
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                suite_name=suite.name,
                passed=False,
                duration=duration,
                error=str(e),
                exit_code=-2
            )
    
    def check_dependencies(self, suite_name: str, completed_suites: set) -> Tuple[bool, List[str]]:
        """Check if suite dependencies are satisfied"""
        suite = self.test_suites[suite_name]
        
        if not suite.dependencies:
            return True, []
        
        missing_deps = []
        for dep in suite.dependencies:
            if dep not in completed_suites:
                missing_deps.append(dep)
        
        return len(missing_deps) == 0, missing_deps
    
    async def run_all_tests(
        self,
        include_suites: Optional[List[str]] = None,
        exclude_suites: Optional[List[str]] = None,
        fail_fast: bool = False,
        parallel: bool = False
    ) -> bool:
        """Run all test suites"""
        
        # Check prerequisites
        prereq_ok, missing = self.check_prerequisites()
        if not prereq_ok:
            self.print_colored("❌ Prerequisites not met. Aborting.", "91")
            return False
        
        # Determine which suites to run
        suites_to_run = []
        for name, suite in self.test_suites.items():
            if include_suites and name not in include_suites:
                continue
            if exclude_suites and name in exclude_suites:
                continue
            suites_to_run.append(name)
        
        if not suites_to_run:
            self.print_colored("❌ No test suites to run", "91")
            return False
        
        self.print_colored(f"🚀 Running test suites: {', '.join(suites_to_run)}", "95")
        self.print_colored(f"Parallel execution: {'enabled' if parallel else 'disabled'}", "96")
        
        completed_suites = set()
        failed_suites = set()
        total_start_time = time.time()
        
        # Group suites by dependency level for parallel execution
        if parallel:
            suite_groups = self._group_suites_by_dependencies(suites_to_run)
        else:
            suite_groups = [[suite] for suite in suites_to_run]
        
        # Execute suite groups
        for group_index, suite_group in enumerate(suite_groups):
            self.print_colored(f"\n📋 Executing group {group_index + 1}: {', '.join(suite_group)}", "95")
            
            # Check dependencies for each suite in group
            ready_suites = []
            for suite_name in suite_group:
                deps_ok, missing_deps = self.check_dependencies(suite_name, completed_suites)
                
                if deps_ok:
                    ready_suites.append(suite_name)
                else:
                    self.print_colored(f"⏸️  Skipping {suite_name}: missing dependencies {missing_deps}", "93")
                    result = TestResult(
                        suite_name=suite_name,
                        passed=False,
                        duration=0,
                        skipped=True,
                        skip_reason=f"Missing dependencies: {missing_deps}"
                    )
                    self.results.append(result)
            
            if not ready_suites:
                continue
            
            # Run suites in group (parallel if more than one)
            if len(ready_suites) > 1 and parallel:
                # Run in parallel
                tasks = []
                for suite_name in ready_suites:
                    suite = self.test_suites[suite_name]
                    task = asyncio.create_task(self.run_test_suite(suite))
                    tasks.append((suite_name, task))
                
                # Wait for all tasks in group
                for suite_name, task in tasks:
                    result = await task
                    self.results.append(result)
                    
                    if result.passed:
                        self.print_colored(f"✅ {suite_name} - PASSED ({result.duration:.2f}s)", "92")
                        completed_suites.add(suite_name)
                    else:
                        self.print_colored(f"❌ {suite_name} - FAILED ({result.duration:.2f}s)", "91")
                        failed_suites.add(suite_name)
                        
                        if result.error:
                            self.print_colored(f"   Error: {result.error}", "91")
                        
                        if fail_fast:
                            self.print_colored("💥 Fail-fast enabled. Stopping execution.", "91")
                            return False
            else:
                # Run sequentially
                for suite_name in ready_suites:
                    suite = self.test_suites[suite_name]
                    result = await self.run_test_suite(suite)
                    self.results.append(result)
                    
                    if result.passed:
                        self.print_colored(f"✅ {suite_name} - PASSED ({result.duration:.2f}s)", "92")
                        completed_suites.add(suite_name)
                    else:
                        self.print_colored(f"❌ {suite_name} - FAILED ({result.duration:.2f}s)", "91")
                        failed_suites.add(suite_name)
                        
                        if result.error:
                            self.print_colored(f"   Error: {result.error}", "91")
                        
                        if fail_fast:
                            self.print_colored("💥 Fail-fast enabled. Stopping execution.", "91")
                            return False
        
        # Print final summary
        total_duration = time.time() - total_start_time
        self.print_summary(total_duration)
        
        # Generate reports
        self.generate_reports()
        
        return len(failed_suites) == 0
    
    def _group_suites_by_dependencies(self, suite_names: List[str]) -> List[List[str]]:
        """Group test suites by dependency levels for parallel execution"""
        groups = []
        remaining = set(suite_names)
        processed = set()
        
        while remaining:
            current_group = []
            
            for suite_name in list(remaining):
                suite = self.test_suites[suite_name]
                
                # Check if all dependencies are already processed
                if not suite.dependencies or all(dep in processed for dep in suite.dependencies):
                    current_group.append(suite_name)
            
            if not current_group:
                # Circular dependency or missing dependency
                self.print_colored(f"⚠️  Circular or missing dependencies for: {remaining}", "93")
                current_group = list(remaining)  # Add remaining to avoid infinite loop
            
            groups.append(current_group)
            
            for suite_name in current_group:
                remaining.remove(suite_name)
                processed.add(suite_name)
        
        return groups
    
    def print_summary(self, total_duration: float):
        """Print comprehensive test summary"""
        self.print_colored(f"\n{'='*80}", "95")
        self.print_colored("COMPREHENSIVE TEST SUMMARY", "95")
        self.print_colored(f"{'='*80}", "95")
        
        # Overall statistics
        total_suites = len(self.results)
        passed_suites = sum(1 for r in self.results if r.passed)
        failed_suites = sum(1 for r in self.results if not r.passed and not r.skipped)
        skipped_suites = sum(1 for r in self.results if r.skipped)
        
        self.print_colored(f"Total Duration: {total_duration:.2f}s", "96")
        self.print_colored(f"Test Suites: {total_suites} total, {passed_suites} passed, {failed_suites} failed, {skipped_suites} skipped", "96")
        
        success_rate = (passed_suites / total_suites * 100) if total_suites > 0 else 0
        self.print_colored(f"Success Rate: {success_rate:.1f}%", "92" if success_rate > 80 else "93")
        
        # Detailed results
        self.print_colored(f"\n📊 Detailed Results:", "95")
        for result in self.results:
            status_color = "92" if result.passed else "93" if result.skipped else "91"
            status_text = "PASSED" if result.passed else "SKIPPED" if result.skipped else "FAILED"
            
            self.print_colored(
                f"  {result.suite_name:15} | {status_text:7} | {result.duration:6.2f}s | {self.test_suites[result.suite_name].description}",
                status_color
            )
            
            if result.error:
                self.print_colored(f"    └─ Error: {result.error}", "91")
            
            if result.skip_reason:
                self.print_colored(f"    └─ Skipped: {result.skip_reason}", "93")
        
        # Recommendations
        if failed_suites > 0:
            self.print_colored(f"\n🔧 Recommendations:", "93")
            self.print_colored("  - Review failed test output above", "93")
            self.print_colored("  - Check test logs in the results/ directory", "93")
            self.print_colored("  - Run individual test suites for detailed debugging", "93")
    
    def generate_reports(self):
        """Generate test reports in various formats"""
        results_dir = self.tests_dir / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = int(time.time())
        
        # JSON report
        json_report = {
            "timestamp": timestamp,
            "total_duration": sum(r.duration for r in self.results),
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed and not r.skipped),
                "skipped": sum(1 for r in self.results if r.skipped)
            },
            "results": [asdict(r) for r in self.results]
        }
        
        json_file = results_dir / f"test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        
        self.print_colored(f"📄 JSON report: {json_file}", "96")
        
        # HTML report (simple)
        html_content = self._generate_html_report(json_report)
        html_file = results_dir / f"test_results_{timestamp}.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        self.print_colored(f"🌐 HTML report: {html_file}", "96")
    
    def _generate_html_report(self, data: Dict) -> str:
        """Generate simple HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Energy Tracking Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .results {{ margin-top: 30px; }}
        .suite {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .passed {{ background: #d4edda; border-left: 4px solid #28a745; }}
        .failed {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .skipped {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
        .error {{ color: #dc3545; font-size: 0.9em; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Energy Tracking System - Test Results</h1>
        <p><strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['timestamp']))}</p>
        <p><strong>Total Duration:</strong> {data['total_duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Suites:</strong> {data['summary']['total']}</p>
        <p><strong>Passed:</strong> {data['summary']['passed']}</p>
        <p><strong>Failed:</strong> {data['summary']['failed']}</p>
        <p><strong>Skipped:</strong> {data['summary']['skipped']}</p>
        <p><strong>Success Rate:</strong> {(data['summary']['passed'] / data['summary']['total'] * 100):.1f}%</p>
    </div>
    
    <div class="results">
        <h2>Detailed Results</h2>
"""
        
        for result in data['results']:
            status_class = "passed" if result['passed'] else "skipped" if result['skipped'] else "failed"
            status_text = "PASSED" if result['passed'] else "SKIPPED" if result['skipped'] else "FAILED"
            
            html += f"""
        <div class="suite {status_class}">
            <h3>{result['suite_name']} - {status_text} ({result['duration']:.2f}s)</h3>
            <p>{self.test_suites[result['suite_name']].description}</p>
"""
            
            if result['error']:
                html += f'<div class="error">Error: {result["error"]}</div>'
            
            if result['skip_reason']:
                html += f'<div class="error">Skipped: {result["skip_reason"]}</div>'
            
            html += "</div>"
        
        html += """
    </div>
</body>
</html>"""
        
        return html


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Energy Tracking Master Test Runner")
    
    parser.add_argument("--include", nargs="+", help="Include specific test suites")
    parser.add_argument("--exclude", nargs="+", help="Exclude specific test suites")
    parser.add_argument("--list", action="store_true", help="List available test suites")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--parallel", action="store_true", help="Run compatible tests in parallel")
    parser.add_argument("--quick", action="store_true", help="Run only quick tests (unit + integration)")
    parser.add_argument("--full", action="store_true", help="Run all tests including performance and E2E")
    
    args = parser.parse_args()
    
    # Find project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Initialize runner
    runner = MasterTestRunner(project_root)
    
    # List test suites if requested
    if args.list:
        runner.print_colored("📋 Available Test Suites:", "95")
        for name, suite in runner.test_suites.items():
            required_text = "required" if suite.required else "optional"
            runner.print_colored(f"  {name:15} | {required_text:8} | {suite.description}", "96")
        return
    
    # Determine test suite selection
    include_suites = args.include
    exclude_suites = args.exclude or []
    
    if args.quick:
        include_suites = ["unit", "integration", "security"]
    elif args.full:
        include_suites = None  # Run all
        exclude_suites = []
    
    try:
        success = await runner.run_all_tests(
            include_suites=include_suites,
            exclude_suites=exclude_suites,
            fail_fast=args.fail_fast,
            parallel=args.parallel
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        runner.print_colored("\n❌ Test execution interrupted by user", "91")
        sys.exit(1)
    except Exception as e:
        runner.print_colored(f"❌ Error running tests: {e}", "91")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
