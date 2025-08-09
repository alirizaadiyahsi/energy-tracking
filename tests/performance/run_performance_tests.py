#!/usr/bin/env python3
"""
Performance test runner for Energy Tracking System
"""
import argparse
import configparser
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


class PerformanceTestRunner:
    """Manages and executes performance tests using Locust"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests" / "performance"
        self.config_file = self.tests_dir / "config.ini"
        self.locustfile = self.tests_dir / "locustfile.py"
        self.results_dir = self.tests_dir / "results"

        # Ensure results directory exists
        self.results_dir.mkdir(exist_ok=True)

        # Load configuration
        self.config = self._load_config()

    def _load_config(self) -> configparser.ConfigParser:
        """Load performance test configuration"""
        config = configparser.ConfigParser()
        if self.config_file.exists():
            config.read(self.config_file)
        return config

    def print_colored(self, message: str, color_code: str = "0") -> None:
        """Print colored message"""
        print(f"\033[{color_code}m{message}\033[0m")

    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met"""
        self.print_colored("🔍 Checking prerequisites...", "94")

        # Check if Locust is installed
        try:
            result = subprocess.run(
                [sys.executable, "-c", "import locust"], capture_output=True, text=True
            )
            if result.returncode != 0:
                self.print_colored(
                    "❌ Locust not installed. Run: pip install locust", "91"
                )
                return False
        except Exception as e:
            self.print_colored(f"❌ Error checking Locust: {e}", "91")
            return False

        # Check if locustfile exists
        if not self.locustfile.exists():
            self.print_colored(f"❌ Locustfile not found: {self.locustfile}", "91")
            return False

        self.print_colored("✅ Prerequisites check passed", "92")
        return True

    def run_performance_test(
        self,
        scenario: str = "medium",
        host: str = "http://localhost:8000",
        headless: bool = True,
        custom_params: Optional[Dict] = None,
    ) -> bool:
        """Run performance test with specified parameters"""

        if not self.check_prerequisites():
            return False

        # Get scenario configuration
        scenario_config = self._get_scenario_config(scenario)
        if custom_params:
            scenario_config.update(custom_params)

        # Prepare command
        timestamp = int(time.time())
        results_prefix = f"{scenario}_{timestamp}"

        command = [
            "locust",
            "-f",
            str(self.locustfile),
            "--host",
            host,
            "--users",
            str(scenario_config.get("users", 10)),
            "--spawn-rate",
            str(scenario_config.get("spawn_rate", 2)),
            "--run-time",
            scenario_config.get("run_time", "60s"),
            "--html",
            str(self.results_dir / f"{results_prefix}.html"),
            "--csv",
            str(self.results_dir / results_prefix),
            "--loglevel",
            "INFO",
        ]

        if headless:
            command.append("--headless")

        self.print_colored(f"🚀 Starting {scenario} performance test...", "94")
        self.print_colored(f"Target: {host}", "96")
        self.print_colored(f"Users: {scenario_config.get('users', 10)}", "96")
        self.print_colored(f"Duration: {scenario_config.get('run_time', '60s')}", "96")

        try:
            # Run the test
            result = subprocess.run(
                command,
                cwd=self.project_root,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            if result.returncode == 0:
                self.print_colored("✅ Performance test completed successfully", "92")
                self._analyze_results(results_prefix)
                return True
            else:
                self.print_colored("❌ Performance test failed", "91")
                return False

        except subprocess.TimeoutExpired:
            self.print_colored("❌ Performance test timed out", "91")
            return False
        except Exception as e:
            self.print_colored(f"❌ Error running performance test: {e}", "91")
            return False

    def _get_scenario_config(self, scenario: str) -> Dict:
        """Get configuration for a specific scenario"""
        scenarios = {
            "light": {"users": 5, "spawn_rate": 1, "run_time": "30s"},
            "medium": {"users": 20, "spawn_rate": 5, "run_time": "120s"},
            "heavy": {"users": 100, "spawn_rate": 10, "run_time": "300s"},
            "stress": {"users": 500, "spawn_rate": 50, "run_time": "600s"},
            "spike": {"users": 200, "spawn_rate": 100, "run_time": "60s"},
        }

        # Override with config file if available
        if self.config.has_section("scenarios"):
            for key in scenarios.get(scenario, {}):
                config_key = f"{scenario}.{key}"
                if self.config.has_option("scenarios", config_key):
                    value = self.config.get("scenarios", config_key)
                    # Convert to appropriate type
                    if key in ["users", "spawn_rate"]:
                        scenarios[scenario][key] = int(value)
                    else:
                        scenarios[scenario][key] = value

        return scenarios.get(scenario, scenarios["medium"])

    def _analyze_results(self, results_prefix: str) -> None:
        """Analyze and display test results"""
        self.print_colored("📊 Analyzing results...", "94")

        # Look for CSV results file
        csv_file = self.results_dir / f"{results_prefix}_stats.csv"

        if csv_file.exists():
            try:
                import pandas as pd

                df = pd.read_csv(csv_file)

                self.print_colored("📈 Performance Summary:", "93")
                print(f"Total Requests: {df['Request Count'].sum()}")
                print(f"Failed Requests: {df['Failure Count'].sum()}")
                print(
                    f"Average Response Time: {df['Average Response Time'].mean():.2f}ms"
                )
                print(f"Max Response Time: {df['Max Response Time'].max():.2f}ms")
                print(f"Requests per Second: {df['Requests/s'].mean():.2f}")

                # Check against thresholds
                self._check_thresholds(df)

            except ImportError:
                self.print_colored(
                    "⚠️  Install pandas for detailed analysis: pip install pandas", "93"
                )
            except Exception as e:
                self.print_colored(f"⚠️  Error analyzing results: {e}", "93")

        # Display HTML report location
        html_file = self.results_dir / f"{results_prefix}.html"
        if html_file.exists():
            self.print_colored(f"📋 Detailed report: {html_file}", "96")

    def _check_thresholds(self, df) -> None:
        """Check results against performance thresholds"""
        thresholds = {
            "max_response_time": 2000,
            "error_rate": 5,
            "min_requests_per_second": 10,
        }

        # Override with config file
        if self.config.has_section("thresholds"):
            for key in thresholds:
                if self.config.has_option("thresholds", key):
                    thresholds[key] = float(self.config.get("thresholds", key))

        self.print_colored("🎯 Threshold Analysis:", "93")

        # Check max response time
        max_response = df["Max Response Time"].max()
        if max_response > thresholds["max_response_time"]:
            self.print_colored(
                f"❌ Max response time exceeded: {max_response:.2f}ms > {thresholds['max_response_time']}ms",
                "91",
            )
        else:
            self.print_colored(
                f"✅ Max response time within threshold: {max_response:.2f}ms", "92"
            )

        # Check error rate
        total_requests = df["Request Count"].sum()
        total_failures = df["Failure Count"].sum()
        error_rate = (
            (total_failures / total_requests * 100) if total_requests > 0 else 0
        )

        if error_rate > thresholds["error_rate"]:
            self.print_colored(
                f"❌ Error rate exceeded: {error_rate:.2f}% > {thresholds['error_rate']}%",
                "91",
            )
        else:
            self.print_colored(
                f"✅ Error rate within threshold: {error_rate:.2f}%", "92"
            )

        # Check requests per second
        avg_rps = df["Requests/s"].mean()
        if avg_rps < thresholds["min_requests_per_second"]:
            self.print_colored(
                f"❌ Requests per second below threshold: {avg_rps:.2f} < {thresholds['min_requests_per_second']}",
                "91",
            )
        else:
            self.print_colored(
                f"✅ Requests per second above threshold: {avg_rps:.2f}", "92"
            )

    def run_load_test_suite(self, host: str = "http://localhost:8000") -> None:
        """Run a complete suite of load tests"""
        scenarios = ["light", "medium", "heavy"]

        self.print_colored("🧪 Running Load Test Suite", "95")

        results = {}
        for scenario in scenarios:
            self.print_colored(f"\n{'='*50}", "94")
            self.print_colored(f"Running {scenario.upper()} load test", "94")
            self.print_colored(f"{'='*50}", "94")

            success = self.run_performance_test(scenario, host, headless=True)
            results[scenario] = success

            if not success:
                self.print_colored(f"❌ {scenario} test failed, stopping suite", "91")
                break

            # Wait between tests
            time.sleep(5)

        # Summary
        self.print_colored("\n📊 Load Test Suite Summary", "95")
        for scenario, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            self.print_colored(
                f"{scenario.upper()}: {status}", "92" if success else "91"
            )

    def run_stress_test(self, host: str = "http://localhost:8000") -> bool:
        """Run stress test"""
        self.print_colored("⚡ Running Stress Test", "95")
        return self.run_performance_test("stress", host, headless=True)

    def run_spike_test(self, host: str = "http://localhost:8000") -> bool:
        """Run spike test"""
        self.print_colored("📈 Running Spike Test", "95")
        return self.run_performance_test("spike", host, headless=True)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Energy Tracking Performance Test Runner"
    )

    parser.add_argument(
        "--scenario",
        choices=["light", "medium", "heavy", "stress", "spike"],
        default="medium",
        help="Test scenario to run",
    )
    parser.add_argument(
        "--host", default="http://localhost:8000", help="Target host for testing"
    )
    parser.add_argument("--users", type=int, help="Number of concurrent users")
    parser.add_argument("--spawn-rate", type=int, help="User spawn rate")
    parser.add_argument("--run-time", help="Test duration (e.g., 60s, 5m)")
    parser.add_argument("--suite", action="store_true", help="Run complete test suite")
    parser.add_argument("--stress", action="store_true", help="Run stress test")
    parser.add_argument("--spike", action="store_true", help="Run spike test")
    parser.add_argument("--gui", action="store_true", help="Run with Locust web UI")

    args = parser.parse_args()

    # Find project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    # Initialize runner
    runner = PerformanceTestRunner(project_root)

    try:
        if args.suite:
            runner.run_load_test_suite(args.host)
        elif args.stress:
            runner.run_stress_test(args.host)
        elif args.spike:
            runner.run_spike_test(args.host)
        else:
            # Custom parameters
            custom_params = {}
            if args.users:
                custom_params["users"] = args.users
            if args.spawn_rate:
                custom_params["spawn_rate"] = args.spawn_rate
            if args.run_time:
                custom_params["run_time"] = args.run_time

            runner.run_performance_test(
                args.scenario,
                args.host,
                headless=not args.gui,
                custom_params=custom_params if custom_params else None,
            )

    except KeyboardInterrupt:
        runner.print_colored("\n❌ Performance test interrupted by user", "91")
        sys.exit(1)
    except Exception as e:
        runner.print_colored(f"❌ Error running performance tests: {e}", "91")
        sys.exit(1)


if __name__ == "__main__":
    main()
