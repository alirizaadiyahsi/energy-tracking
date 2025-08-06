"""
Performance Test Runner for Energy Tracking System
Automated performance testing with different load scenarios
"""

import os
import sys
import subprocess
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class PerformanceTestRunner:
    """Manages and executes performance tests using Locust"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_dir = project_root / "tests" / "performance"
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test configurations
        self.test_scenarios = {
            "smoke": {
                "users": 10,
                "spawn_rate": 2,
                "duration": "2m",
                "description": "Smoke test - basic functionality"
            },
            "normal": {
                "users": 50,
                "spawn_rate": 5,
                "duration": "5m",
                "description": "Normal load test"
            },
            "peak": {
                "users": 200,
                "spawn_rate": 20,
                "duration": "3m",
                "description": "Peak load test"
            },
            "stress": {
                "users": 500,
                "spawn_rate": 50,
                "duration": "2m",
                "description": "Stress test - maximum load"
            },
            "endurance": {
                "users": 100,
                "spawn_rate": 10,
                "duration": "30m",
                "description": "Endurance test - sustained load"
            }
        }
    
    def print_colored(self, message: str, color: str = ""):
        """Print colored output"""
        colors = {
            "blue": "\033[0;34m",
            "green": "\033[0;32m",
            "yellow": "\033[1;33m",
            "red": "\033[0;31m",
            "reset": "\033[0m"
        }
        
        if color in colors:
            print(f"{colors[color]}{message}{colors['reset']}")
        else:
            print(message)
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met"""
        self.print_colored("🔍 Checking prerequisites...", "blue")
        
        # Check if Locust is installed
        try:
            result = subprocess.run(["locust", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.print_colored("❌ Locust is not installed", "red")
                self.print_colored("Install with: pip install locust", "yellow")
                return False
        except FileNotFoundError:
            self.print_colored("❌ Locust is not installed or not in PATH", "red")
            return False
        
        # Check if locustfile exists
        locustfile = self.test_dir / "locustfile.py"
        if not locustfile.exists():
            self.print_colored("❌ Locustfile not found", "red")
            return False
        
        self.print_colored("✅ Prerequisites met", "green")
        return True
    
    def start_services(self) -> bool:
        """Start services for testing"""
        self.print_colored("🐳 Starting services...", "blue")
        
        try:
            # Use test docker-compose file
            compose_file = self.project_root / "docker-compose.test.yml"
            
            if compose_file.exists():
                result = subprocess.run([
                    "docker-compose", "-f", str(compose_file), "up", "-d"
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode != 0:
                    self.print_colored(f"❌ Failed to start services: {result.stderr}", "red")
                    return False
            else:
                # Use regular docker-compose
                result = subprocess.run([
                    "docker-compose", "up", "-d"
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode != 0:
                    self.print_colored(f"❌ Failed to start services: {result.stderr}", "red")
                    return False
            
            # Wait for services to be ready
            self.print_colored("⏳ Waiting for services to be ready...", "yellow")
            time.sleep(45)  # Give services time to start
            
            # Check if services are responding
            import urllib.request
            services = [
                "http://localhost:8000/health",
                "http://localhost:8005/health"
            ]
            
            for service_url in services:
                try:
                    urllib.request.urlopen(service_url, timeout=10)
                except Exception as e:
                    self.print_colored(f"❌ Service not ready: {service_url} - {e}", "red")
                    return False
            
            self.print_colored("✅ Services are ready", "green")
            return True
            
        except Exception as e:
            self.print_colored(f"❌ Error starting services: {e}", "red")
            return False
    
    def run_performance_test(self, scenario: str, host: str = "http://localhost:8000") -> Dict:
        """Run a specific performance test scenario"""
        
        if scenario not in self.test_scenarios:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        config = self.test_scenarios[scenario]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.print_colored(f"🚀 Running {scenario} test: {config['description']}", "blue")
        self.print_colored(f"   Users: {config['users']}, Spawn Rate: {config['spawn_rate']}, Duration: {config['duration']}", "blue")
        
        # Prepare output files
        html_report = self.results_dir / f"performance_report_{scenario}_{timestamp}.html"
        csv_prefix = self.results_dir / f"performance_results_{scenario}_{timestamp}"
        
        # Build Locust command
        cmd = [
            "locust",
            "-f", str(self.test_dir / "locustfile.py"),
            "--host", host,
            "--users", str(config["users"]),
            "--spawn-rate", str(config["spawn_rate"]),
            "--run-time", config["duration"],
            "--headless",
            "--html", str(html_report),
            "--csv", str(csv_prefix)
        ]
        
        # Run the test
        start_time = time.time()
        
        try:
            self.print_colored(f"   Executing: {' '.join(cmd)}", "yellow")
            result = subprocess.run(cmd, cwd=self.test_dir, capture_output=True, text=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                self.print_colored(f"✅ {scenario.title()} test completed successfully", "green")
                
                # Parse results
                test_results = self.parse_test_results(csv_prefix, html_report, scenario, duration)
                
                # Print summary
                self.print_test_summary(test_results)
                
                return test_results
            else:
                self.print_colored(f"❌ {scenario.title()} test failed", "red")
                self.print_colored(f"Error: {result.stderr}", "red")
                return {"status": "failed", "error": result.stderr}
                
        except Exception as e:
            self.print_colored(f"❌ Error running {scenario} test: {e}", "red")
            return {"status": "error", "error": str(e)}
    
    def parse_test_results(self, csv_prefix: Path, html_report: Path, scenario: str, duration: float) -> Dict:
        """Parse Locust test results"""
        results = {
            "scenario": scenario,
            "duration": duration,
            "html_report": str(html_report),
            "timestamp": datetime.now().isoformat()
        }
        
        # Try to parse CSV stats
        stats_file = Path(f"{csv_prefix}_stats.csv")
        if stats_file.exists():
            try:
                import csv
                with open(stats_file, 'r') as f:
                    reader = csv.DictReader(f)
                    stats = list(reader)
                    
                    if stats:
                        # Get aggregated stats (usually the last row)
                        total_stats = stats[-1] if len(stats) > 1 else stats[0]
                        
                        results.update({
                            "total_requests": int(total_stats.get("Request Count", 0)),
                            "failure_count": int(total_stats.get("Failure Count", 0)),
                            "median_response_time": float(total_stats.get("Median Response Time", 0)),
                            "average_response_time": float(total_stats.get("Average Response Time", 0)),
                            "p95_response_time": float(total_stats.get("95%ile", 0)),
                            "p99_response_time": float(total_stats.get("99%ile", 0)),
                            "requests_per_second": float(total_stats.get("Requests/s", 0)),
                            "failure_rate": float(total_stats.get("Failure Count", 0)) / max(float(total_stats.get("Request Count", 1)), 1)
                        })
            except Exception as e:
                self.print_colored(f"⚠️ Could not parse CSV results: {e}", "yellow")
        
        return results
    
    def print_test_summary(self, results: Dict):
        """Print test summary"""
        self.print_colored("\n" + "="*60, "blue")
        self.print_colored(f"📊 {results['scenario'].upper()} TEST SUMMARY", "blue")
        self.print_colored("="*60, "blue")
        
        if "total_requests" in results:
            self.print_colored(f"Total Requests: {results['total_requests']:,}", "")
            self.print_colored(f"Failed Requests: {results['failure_count']:,}", "")
            self.print_colored(f"Failure Rate: {results['failure_rate']:.2%}", "")
            self.print_colored(f"Requests/sec: {results['requests_per_second']:.2f}", "")
            self.print_colored(f"Median Response Time: {results['median_response_time']:.0f}ms", "")
            self.print_colored(f"Average Response Time: {results['average_response_time']:.0f}ms", "")
            self.print_colored(f"95th Percentile: {results['p95_response_time']:.0f}ms", "")
            self.print_colored(f"99th Percentile: {results['p99_response_time']:.0f}ms", "")
        
        self.print_colored(f"Duration: {results['duration']:.1f} seconds", "")
        self.print_colored(f"Report: {results['html_report']}", "")
        self.print_colored("="*60, "blue")
    
    def run_all_scenarios(self, host: str = "http://localhost:8000") -> List[Dict]:
        """Run all performance test scenarios"""
        self.print_colored("🎯 Running all performance test scenarios", "blue")
        
        all_results = []
        
        for scenario in ["smoke", "normal", "peak", "stress"]:
            result = self.run_performance_test(scenario, host)
            all_results.append(result)
            
            # Small break between tests
            if scenario != "stress":  # Don't wait after the last test
                self.print_colored("⏳ Cooling down before next test...", "yellow")
                time.sleep(30)
        
        # Generate combined report
        self.generate_combined_report(all_results)
        
        return all_results
    
    def generate_combined_report(self, all_results: List[Dict]):
        """Generate a combined performance report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"performance_summary_{timestamp}.json"
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_scenarios": len(all_results),
            "scenarios": all_results
        }
        
        # Calculate aggregate metrics
        if any("total_requests" in result for result in all_results):
            valid_results = [r for r in all_results if "total_requests" in r]
            
            if valid_results:
                summary["aggregate_metrics"] = {
                    "total_requests": sum(r["total_requests"] for r in valid_results),
                    "total_failures": sum(r["failure_count"] for r in valid_results),
                    "average_rps": sum(r["requests_per_second"] for r in valid_results) / len(valid_results),
                    "average_response_time": sum(r["average_response_time"] for r in valid_results) / len(valid_results),
                    "max_p99_response_time": max(r["p99_response_time"] for r in valid_results)
                }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.print_colored(f"📋 Combined report saved: {report_file}", "green")
    
    def cleanup_services(self):
        """Stop services after testing"""
        self.print_colored("🧹 Stopping services...", "yellow")
        
        try:
            compose_file = self.project_root / "docker-compose.test.yml"
            
            if compose_file.exists():
                subprocess.run([
                    "docker-compose", "-f", str(compose_file), "down"
                ], capture_output=True, cwd=self.project_root)
            else:
                subprocess.run([
                    "docker-compose", "down"
                ], capture_output=True, cwd=self.project_root)
            
            self.print_colored("✅ Services stopped", "green")
            
        except Exception as e:
            self.print_colored(f"⚠️ Error stopping services: {e}", "yellow")


def main():
    parser = argparse.ArgumentParser(description="Energy Tracking System Performance Test Runner")
    parser.add_argument("--scenario", choices=["smoke", "normal", "peak", "stress", "endurance", "all"],
                       default="smoke", help="Test scenario to run")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host")
    parser.add_argument("--start-services", action="store_true", help="Start services before testing")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup services after testing")
    
    args = parser.parse_args()
    
    # Initialize runner
    project_root = Path(__file__).parent.parent.parent
    runner = PerformanceTestRunner(project_root)
    
    runner.print_colored("⚡ Energy Tracking System Performance Test Runner", "blue")
    runner.print_colored("="*60, "blue")
    
    # Check prerequisites
    if not runner.check_prerequisites():
        sys.exit(1)
    
    # Start services if requested
    if args.start_services:
        if not runner.start_services():
            sys.exit(1)
    
    try:
        # Run tests
        if args.scenario == "all":
            results = runner.run_all_scenarios(args.host)
            success = all(r.get("status") != "failed" for r in results)
        else:
            result = runner.run_performance_test(args.scenario, args.host)
            success = result.get("status") != "failed"
        
        # Print final status
        if success:
            runner.print_colored("🎉 Performance testing completed successfully!", "green")
        else:
            runner.print_colored("❌ Some performance tests failed", "red")
        
    finally:
        # Cleanup services if requested
        if args.cleanup:
            runner.cleanup_services()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
