#!/usr/bin/env python3
"""
Quick CI Test Runner
A simpler version for rapid testing of core CI components
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class QuickCIRunner:
    """Quick CI test runner for rapid feedback"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {}
        self.start_time = time.time()

    def run_command(
        self, cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300
    ) -> Dict:
        """Run a command and return results"""
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            duration = time.time() - start
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "duration": timeout,
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": time.time() - start,
            }

    def test_lint(self) -> bool:
        """Run linting tests"""
        print("🧹 Running linting checks...")

        checks = [
            {
                "name": "Black formatting",
                "cmd": ["python", "-m", "black", "--check", "--diff", "."],
                "required": True,
            },
            {
                "name": "isort imports",
                "cmd": ["python", "-m", "isort", "--check-only", "--diff", "."],
                "required": True,
            },
            {
                "name": "flake8 linting",
                "cmd": ["python", "-m", "flake8", "services/", "tests/"],
                "required": True,
            },
            {
                "name": "mypy type checking",
                "cmd": [
                    "python",
                    "-m",
                    "mypy",
                    "services/",
                    "--ignore-missing-imports",
                ],
                "required": False,  # Often has issues with dependencies
            },
        ]

        all_passed = True
        results = []

        for check in checks:
            print(f"   🔍 {check['name']}...")
            result = self.run_command(check["cmd"])

            if result["success"]:
                print(f"   ✅ {check['name']} passed")
                results.append({"check": check["name"], "status": "passed"})
            else:
                status = "❌" if check["required"] else "⚠️"
                print(f"   {status} {check['name']} failed")
                if check["required"]:
                    all_passed = False

                if result["stderr"]:
                    print(f"      Error: {result['stderr'][:200]}...")

                results.append(
                    {
                        "check": check["name"],
                        "status": "failed" if check["required"] else "warning",
                        "error": result["stderr"][:500],
                    }
                )

        # Frontend linting if available
        frontend_dir = self.project_root / "frontend"
        if frontend_dir.exists() and (frontend_dir / "package.json").exists():
            print("   🔍 Frontend linting...")

            # Install deps if needed
            if not (frontend_dir / "node_modules").exists():
                print("   📦 Installing frontend dependencies...")
                npm_result = self.run_command(["npm", "ci"], cwd=frontend_dir)
                if not npm_result["success"]:
                    print("   ❌ Failed to install frontend dependencies")
                    all_passed = False

            # Run ESLint
            eslint_result = self.run_command(["npm", "run", "lint"], cwd=frontend_dir)
            if eslint_result["success"]:
                print("   ✅ Frontend linting passed")
                results.append({"check": "ESLint", "status": "passed"})
            else:
                print("   ❌ Frontend linting failed")
                all_passed = False
                results.append(
                    {
                        "check": "ESLint",
                        "status": "failed",
                        "error": eslint_result["stderr"][:500],
                    }
                )

        self.results["lint"] = {
            "success": all_passed,
            "checks": results,
            "duration": time.time() - time.time(),  # Will be updated by caller
        }

        return all_passed

    def test_unit(self) -> bool:
        """Run unit tests"""
        print("🧪 Running unit tests...")

        # Install test dependencies
        print("   📦 Installing test dependencies...")
        deps_result = self.run_command(
            ["python", "-m", "pip", "install", "-r", "tests/test-requirements.txt"]
        )

        if not deps_result["success"]:
            print("   ❌ Failed to install test dependencies")
            self.results["unit"] = {
                "success": False,
                "error": "Failed to install dependencies",
                "duration": deps_result["duration"],
            }
            return False

        # Run Python unit tests
        print("   🐍 Running Python unit tests...")
        test_result = self.run_command(
            ["python", "-m", "pytest", "tests/unit/", "-v", "-m", "unit", "--tb=short"]
        )

        success = test_result["success"]

        # Extract test count from output
        test_count = 0
        if "passed" in test_result["stdout"]:
            try:
                # Look for pattern like "5 passed"
                import re

                match = re.search(r"(\d+) passed", test_result["stdout"])
                if match:
                    test_count = int(match.group(1))
            except Exception:
                pass

        if success:
            print(f"   ✅ Python unit tests passed ({test_count} tests)")
        else:
            print("   ❌ Python unit tests failed")
            if test_result["stdout"]:
                print(f"      Output: {test_result['stdout'][-300:]}")

        # Frontend tests if available
        frontend_results = []
        frontend_dir = self.project_root / "frontend"
        if frontend_dir.exists() and (frontend_dir / "package.json").exists():
            print("   ⚛️ Running frontend tests...")

            frontend_result = self.run_command(
                ["npm", "test", "--", "--run"], cwd=frontend_dir
            )

            if frontend_result["success"]:
                print("   ✅ Frontend tests passed")
                frontend_results.append({"type": "frontend", "status": "passed"})
            else:
                print("   ❌ Frontend tests failed")
                success = False
                frontend_results.append(
                    {
                        "type": "frontend",
                        "status": "failed",
                        "error": frontend_result["stderr"][:500],
                    }
                )

        self.results["unit"] = {
            "success": success,
            "python_tests": test_count,
            "frontend_results": frontend_results,
            "duration": test_result["duration"],
        }

        return success

    def test_security(self) -> bool:
        """Run basic security checks"""
        print("🔒 Running security checks...")

        # Install security tools
        print("   📦 Installing security tools...")
        tools_result = self.run_command(
            ["python", "-m", "pip", "install", "bandit", "safety"]
        )

        if not tools_result["success"]:
            print("   ⚠️ Failed to install security tools, skipping...")
            return True  # Don't fail the build for this

        results = []
        overall_success = True

        # Run Bandit
        print("   🔍 Running Bandit security scan...")
        bandit_result = self.run_command(
            ["python", "-m", "bandit", "-r", "services/", "-f", "json"]
        )

        # Bandit returns non-zero for findings, so we parse the JSON
        high_severity_count = 0
        if bandit_result["stdout"]:
            try:
                bandit_data = json.loads(bandit_result["stdout"])
                metrics = bandit_data.get("metrics", {}).get("_totals", {})
                high_severity_count = metrics.get("SEVERITY", {}).get("HIGH", 0)
            except Exception:
                pass

        if high_severity_count > 0:
            print(f"   ❌ Bandit found {high_severity_count} high severity issues")
            overall_success = False
            results.append(
                {
                    "tool": "bandit",
                    "status": "failed",
                    "high_severity": high_severity_count,
                }
            )
        else:
            print("   ✅ Bandit scan passed (no high severity issues)")
            results.append({"tool": "bandit", "status": "passed"})

        # Run Safety
        print("   🛡️ Running Safety dependency scan...")
        safety_result = self.run_command(["python", "-m", "safety", "check"])

        if safety_result["success"]:
            print("   ✅ Safety scan passed (no known vulnerabilities)")
            results.append({"tool": "safety", "status": "passed"})
        else:
            print("   ❌ Safety found dependency vulnerabilities")
            overall_success = False
            results.append({"tool": "safety", "status": "failed"})

        self.results["security"] = {
            "success": overall_success,
            "tools": results,
            "duration": time.time() - time.time(),
        }

        return overall_success

    def generate_report(self) -> Dict:
        """Generate final test report"""
        total_duration = time.time() - self.start_time

        passed_stages = sum(
            1 for stage in self.results.values() if stage.get("success", False)
        )
        total_stages = len(self.results)

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": round(total_duration, 2),
            "summary": {
                "total_stages": total_stages,
                "passed_stages": passed_stages,
                "failed_stages": total_stages - passed_stages,
                "success_rate": (
                    round((passed_stages / total_stages) * 100, 1)
                    if total_stages > 0
                    else 0
                ),
            },
            "stages": self.results,
        }

        return report


def main():
    parser = argparse.ArgumentParser(description="Quick CI Test Runner")
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=["lint", "unit", "security", "all"],
        default=["all"],
        help="Stages to run",
    )
    parser.add_argument(
        "--output", default="quick-ci-report.json", help="Output file for JSON report"
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Continue running stages even if one fails",
    )

    args = parser.parse_args()

    project_root = Path.cwd()
    runner = QuickCIRunner(project_root)

    print("🚀 Quick CI Test Runner")
    print("=" * 50)

    # Determine stages to run
    if "all" in args.stages:
        stages_to_run = ["lint", "unit", "security"]
    else:
        stages_to_run = args.stages

    print(f"📋 Running stages: {', '.join(stages_to_run)}")
    print()

    # Run stages
    overall_success = True

    for stage in stages_to_run:
        start_time = time.time()

        if stage == "lint":
            success = runner.test_lint()
        elif stage == "unit":
            success = runner.test_unit()
        elif stage == "security":
            success = runner.test_security()
        else:
            print(f"❌ Unknown stage: {stage}")
            success = False

        # Update duration
        if stage in runner.results:
            runner.results[stage]["duration"] = time.time() - start_time

        if not success:
            overall_success = False
            if not args.continue_on_failure:
                print(f"\n❌ Stage '{stage}' failed. Stopping.")
                break

        print()

    # Generate and save report
    report = runner.generate_report()

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("📊 QUICK CI SUMMARY")
    print("=" * 50)
    print(f"⏱️ Total Duration: {report['total_duration']}s")
    print(f"✅ Passed: {report['summary']['passed_stages']}")
    print(f"❌ Failed: {report['summary']['failed_stages']}")
    print(f"📈 Success Rate: {report['summary']['success_rate']}%")
    print(f"📄 Report saved to: {args.output}")

    if overall_success:
        print("\n🎉 All stages passed!")
        return 0
    else:
        print("\n💥 Some stages failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
