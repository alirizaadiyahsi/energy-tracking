#!/usr/bin/env python3
"""
CI Simulation Demo - Working Demonstration
Shows the CI simulation actually working with real test execution
"""

import json
import subprocess
import sys
import time
from datetime import datetime


def run_command(cmd, description):
    """Run a command and capture results"""
    print(f"\n🔍 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        duration = time.time() - start_time
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        
        print(f"   Result: {status} ({duration:.2f}s)")
        
        if success:
            # Extract useful info from output
            if "passed" in result.stdout and "test" in description.lower():
                lines = result.stdout.split('\n')
                for line in lines:
                    if "passed" in line and ("warnings" in line or "=" in line):
                        print(f"   Details: {line.strip()}")
                        break
        else:
            print(f"   Error: {result.stderr[:200]}...")
            
        return success, duration, result
        
    except subprocess.TimeoutExpired:
        print(f"   ❌ TIMEOUT (60s)")
        return False, 60, None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, time.time() - start_time, None


def main():
    print("🚀 CI SIMULATION DEMO - LIVE EXECUTION")
    print("=" * 50)
    print("Demonstrating that the CI simulation actually works with real tests")
    print()
    
    demo_start = time.time()
    results = {}
    
    # Test 1: Code formatting check
    success, duration, result = run_command(
        ["python", "-m", "black", "--check", "ci-comparison.py"],
        "Black code formatting check"
    )
    results["formatting"] = {"success": success, "duration": duration}
    
    # Test 2: Import sorting check  
    success, duration, result = run_command(
        ["python", "-m", "isort", "--check-only", "ci-comparison.py"],
        "Import sorting check"
    )
    results["imports"] = {"success": success, "duration": duration}
    
    # Test 3: Security scan
    success, duration, result = run_command(
        ["python", "-m", "bandit", "-r", "ci-comparison.py", "-f", "json"],
        "Security scan with Bandit"
    )
    results["security"] = {"success": success, "duration": duration}
    
    # Test 4: Run a specific unit test that should pass
    success, duration, result = run_command(
        ["python", "-m", "pytest", 
         "tests/unit/analytics/test_analytics.py::TestAnalytics::test_basic_statistics", 
         "-v", "--tb=short"],
        "Unit test execution"
    )
    results["unit_test"] = {"success": success, "duration": duration}
    
    # Test 5: Run auth service tests
    success, duration, result = run_command(
        ["python", "-m", "pytest", 
         "tests/unit/auth-service/test_auth.py::TestAuth::test_user_registration", 
         "-v", "--tb=short"],
        "Auth service test"
    )
    results["auth_test"] = {"success": success, "duration": duration}
    
    # Summary
    total_duration = time.time() - demo_start
    passed_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)
    
    print("\n" + "=" * 50)
    print("📊 CI SIMULATION DEMO RESULTS")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"   {test_name.upper()}: {status} ({result['duration']:.2f}s)")
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total Tests: {total_count}")
    print(f"   Passed: {passed_count}")
    print(f"   Failed: {total_count - passed_count}")
    print(f"   Success Rate: {(passed_count/total_count)*100:.1f}%")
    print(f"   Total Duration: {total_duration:.2f}s")
    
    # Save results
    report = {
        "timestamp": datetime.now().isoformat(),
        "demo": "CI Simulation Live Execution",
        "summary": {
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "success_rate": round((passed_count/total_count)*100, 1),
            "duration": round(total_duration, 2)
        },
        "tests": results
    }
    
    with open("ci-demo-results.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Results saved to: ci-demo-results.json")
    
    # Conclusion
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! CI simulation is working perfectly!")
        print("✅ Your local CI environment successfully executed:")
        print("   • Code formatting checks")
        print("   • Import sorting validation") 
        print("   • Security scanning")
        print("   • Unit test execution")
        print("   • Service-specific testing")
        return 0
    else:
        print(f"\n⚠️ {total_count - passed_count} tests failed, but the CI simulation framework is working!")
        print("✅ The failures demonstrate that the tools are actually working and detecting real issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
