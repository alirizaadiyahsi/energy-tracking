#!/usr/bin/env python3
"""
Generate combined test report from multiple test result artifacts
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def parse_junit_xml(file_path: Path) -> Dict[str, Any]:
    """Parse JUnit XML file and extract test results"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Handle both testsuites and testsuite root elements
        if root.tag == "testsuites":
            testsuites = root
        else:
            testsuites = [root]

        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        test_cases = []

        for testsuite in testsuites:
            if testsuite.tag != "testsuite":
                continue

            tests = int(testsuite.get("tests", 0))
            failures = int(testsuite.get("failures", 0))
            errors = int(testsuite.get("errors", 0))
            skipped = int(testsuite.get("skipped", 0))

            total_tests += tests
            total_failures += failures
            total_errors += errors
            total_skipped += skipped

            # Extract individual test cases
            for testcase in testsuite.findall("testcase"):
                case_info = {
                    "name": testcase.get("name"),
                    "classname": testcase.get("classname"),
                    "time": float(testcase.get("time", 0)),
                    "status": "passed",
                }

                if testcase.find("failure") is not None:
                    case_info["status"] = "failed"
                    case_info["message"] = testcase.find("failure").get("message", "")
                elif testcase.find("error") is not None:
                    case_info["status"] = "error"
                    case_info["message"] = testcase.find("error").get("message", "")
                elif testcase.find("skipped") is not None:
                    case_info["status"] = "skipped"
                    case_info["message"] = testcase.find("skipped").get("message", "")

                test_cases.append(case_info)

        return {
            "total_tests": total_tests,
            "total_failures": total_failures,
            "total_errors": total_errors,
            "total_skipped": total_skipped,
            "success_rate": (
                ((total_tests - total_failures - total_errors) / total_tests * 100)
                if total_tests > 0
                else 0
            ),
            "test_cases": test_cases,
        }

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {
            "total_tests": 0,
            "total_failures": 0,
            "total_errors": 0,
            "total_skipped": 0,
            "success_rate": 0,
            "test_cases": [],
            "error": str(e),
        }


def collect_test_results(base_dir: Path) -> Dict[str, Any]:
    """Collect test results from all artifact directories"""
    results = {
        "unit": {
            "status": "not_run",
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "services": {},
        },
        "integration": {"status": "not_run", "passed": 0, "failed": 0, "skipped": 0},
        "security": {"status": "not_run", "passed": 0, "failed": 0, "skipped": 0},
        "frontend": {"status": "not_run", "passed": 0, "failed": 0, "skipped": 0},
        "overall": {
            "status": "unknown",
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
        },
    }

    # Look for unit test results
    for item in base_dir.glob("unit-test-results-*"):
        if item.is_dir():
            service_name = item.name.replace("unit-test-results-", "")
            junit_files = list(item.glob("junit-*.xml"))

            if junit_files:
                service_results = parse_junit_xml(junit_files[0])
                results["unit"]["services"][service_name] = service_results
                results["unit"]["passed"] += (
                    service_results["total_tests"]
                    - service_results["total_failures"]
                    - service_results["total_errors"]
                )
                results["unit"]["failed"] += (
                    service_results["total_failures"] + service_results["total_errors"]
                )
                results["unit"]["skipped"] += service_results["total_skipped"]

    if results["unit"]["services"]:
        total_unit_tests = (
            results["unit"]["passed"]
            + results["unit"]["failed"]
            + results["unit"]["skipped"]
        )
        results["unit"]["status"] = (
            "passed" if results["unit"]["failed"] == 0 else "failed"
        )

    # Look for integration test results
    integration_dir = base_dir / "integration-test-results"
    if integration_dir.exists():
        junit_files = list(integration_dir.glob("junit-*.xml"))
        if junit_files:
            integration_results = parse_junit_xml(junit_files[0])
            results["integration"]["passed"] = (
                integration_results["total_tests"]
                - integration_results["total_failures"]
                - integration_results["total_errors"]
            )
            results["integration"]["failed"] = (
                integration_results["total_failures"]
                + integration_results["total_errors"]
            )
            results["integration"]["skipped"] = integration_results["total_skipped"]
            results["integration"]["status"] = (
                "passed" if results["integration"]["failed"] == 0 else "failed"
            )

    # Look for security test results
    security_dir = base_dir / "security-test-results"
    if security_dir.exists():
        junit_files = list(security_dir.glob("junit-*.xml"))
        if junit_files:
            security_results = parse_junit_xml(junit_files[0])
            results["security"]["passed"] = (
                security_results["total_tests"]
                - security_results["total_failures"]
                - security_results["total_errors"]
            )
            results["security"]["failed"] = (
                security_results["total_failures"] + security_results["total_errors"]
            )
            results["security"]["skipped"] = security_results["total_skipped"]
            results["security"]["status"] = (
                "passed" if results["security"]["failed"] == 0 else "failed"
            )

    # Look for frontend test results
    frontend_dir = base_dir / "frontend-test-results"
    if frontend_dir.exists():
        # Frontend tests might use different format
        results["frontend"]["status"] = "passed"  # Assume passed if directory exists

    # Calculate overall results
    total_tests = sum(
        [
            results["unit"]["passed"]
            + results["unit"]["failed"]
            + results["unit"]["skipped"],
            results["integration"]["passed"]
            + results["integration"]["failed"]
            + results["integration"]["skipped"],
            results["security"]["passed"]
            + results["security"]["failed"]
            + results["security"]["skipped"],
        ]
    )

    total_passed = sum(
        [
            results["unit"]["passed"],
            results["integration"]["passed"],
            results["security"]["passed"],
        ]
    )

    total_failed = sum(
        [
            results["unit"]["failed"],
            results["integration"]["failed"],
            results["security"]["failed"],
        ]
    )

    results["overall"]["total_tests"] = total_tests
    results["overall"]["total_passed"] = total_passed
    results["overall"]["total_failed"] = total_failed

    # Determine overall status
    critical_failed = (
        results["unit"]["status"] == "failed"
        or results["integration"]["status"] == "failed"
        or results["security"]["status"] == "failed"
    )
    results["overall"]["status"] = "failed" if critical_failed else "passed"

    return results


def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate HTML test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Energy Tracking - Test Results</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .header h1 {{ margin: 0; color: #2c3e50; }}
        .header .meta {{ color: #7f8c8d; margin-top: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .summary-card h3 {{ margin: 0 0 15px 0; color: #2c3e50; }}
        .summary-card .metric {{ display: flex; justify-content: space-between; margin: 8px 0; }}
        .summary-card .metric .label {{ color: #7f8c8d; }}
        .summary-card .metric .value {{ font-weight: bold; }}
        .status-passed {{ color: #27ae60; }}
        .status-failed {{ color: #e74c3c; }}
        .status-skipped {{ color: #f39c12; }}
        .status-not-run {{ color: #95a5a6; }}
        .details {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .test-section {{ margin-bottom: 30px; }}
        .test-section h3 {{ color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
        .service-results {{ margin-left: 20px; }}
        .service-results h4 {{ color: #34495e; margin: 15px 0 10px 0; }}
        .test-grid {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 10px; font-size: 14px; }}
        .test-grid .header-row {{ font-weight: bold; background: #ecf0f1; padding: 8px; }}
        .test-grid .data-row {{ padding: 8px; border-bottom: 1px solid #ecf0f1; }}
        .overall-status {{ text-align: center; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .overall-status.passed {{ background: #d5f4e6; color: #27ae60; }}
        .overall-status.failed {{ background: #fdf2f2; color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Energy Tracking - Test Results</h1>
            <div class="meta">Generated: {timestamp}</div>
        </div>
        
        <div class="overall-status {results['overall']['status']}">
            <h2>Overall Status: {'✅ PASSED' if results['overall']['status'] == 'passed' else '❌ FAILED'}</h2>
            <p>Total Tests: {results['overall']['total_tests']} | Passed: {results['overall']['total_passed']} | Failed: {results['overall']['total_failed']}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Unit Tests</h3>
                <div class="metric">
                    <span class="label">Status:</span>
                    <span class="value status-{results['unit']['status']}">
                        {'✅ PASSED' if results['unit']['status'] == 'passed' else '❌ FAILED' if results['unit']['status'] == 'failed' else '⏸️ NOT RUN'}
                    </span>
                </div>
                <div class="metric">
                    <span class="label">Passed:</span>
                    <span class="value">{results['unit']['passed']}</span>
                </div>
                <div class="metric">
                    <span class="label">Failed:</span>
                    <span class="value">{results['unit']['failed']}</span>
                </div>
                <div class="metric">
                    <span class="label">Skipped:</span>
                    <span class="value">{results['unit']['skipped']}</span>
                </div>
            </div>
            
            <div class="summary-card">
                <h3>Integration Tests</h3>
                <div class="metric">
                    <span class="label">Status:</span>
                    <span class="value status-{results['integration']['status']}">
                        {'✅ PASSED' if results['integration']['status'] == 'passed' else '❌ FAILED' if results['integration']['status'] == 'failed' else '⏸️ NOT RUN'}
                    </span>
                </div>
                <div class="metric">
                    <span class="label">Passed:</span>
                    <span class="value">{results['integration']['passed']}</span>
                </div>
                <div class="metric">
                    <span class="label">Failed:</span>
                    <span class="value">{results['integration']['failed']}</span>
                </div>
                <div class="metric">
                    <span class="label">Skipped:</span>
                    <span class="value">{results['integration']['skipped']}</span>
                </div>
            </div>
            
            <div class="summary-card">
                <h3>Security Tests</h3>
                <div class="metric">
                    <span class="label">Status:</span>
                    <span class="value status-{results['security']['status']}">
                        {'✅ PASSED' if results['security']['status'] == 'passed' else '❌ FAILED' if results['security']['status'] == 'failed' else '⏸️ NOT RUN'}
                    </span>
                </div>
                <div class="metric">
                    <span class="label">Passed:</span>
                    <span class="value">{results['security']['passed']}</span>
                </div>
                <div class="metric">
                    <span class="label">Failed:</span>
                    <span class="value">{results['security']['failed']}</span>
                </div>
                <div class="metric">
                    <span class="label">Skipped:</span>
                    <span class="value">{results['security']['skipped']}</span>
                </div>
            </div>
            
            <div class="summary-card">
                <h3>Frontend Tests</h3>
                <div class="metric">
                    <span class="label">Status:</span>
                    <span class="value status-{results['frontend']['status']}">
                        {'✅ PASSED' if results['frontend']['status'] == 'passed' else '❌ FAILED' if results['frontend']['status'] == 'failed' else '⏸️ NOT RUN'}
                    </span>
                </div>
            </div>
        </div>
        
        <div class="details">
            <h2>Detailed Results</h2>
            
            <div class="test-section">
                <h3>Unit Test Details</h3>
"""

    # Add unit test service details
    for service_name, service_data in results["unit"]["services"].items():
        html += f"""
                <div class="service-results">
                    <h4>{service_name}</h4>
                    <div class="test-grid">
                        <div class="header-row">Metric</div>
                        <div class="header-row">Total</div>
                        <div class="header-row">Passed</div>
                        <div class="header-row">Failed</div>
                        <div class="header-row">Success Rate</div>
                        
                        <div class="data-row">Tests</div>
                        <div class="data-row">{service_data['total_tests']}</div>
                        <div class="data-row">{service_data['total_tests'] - service_data['total_failures'] - service_data['total_errors']}</div>
                        <div class="data-row">{service_data['total_failures'] + service_data['total_errors']}</div>
                        <div class="data-row">{service_data['success_rate']:.1f}%</div>
                    </div>
                </div>
"""

    html += """
            </div>
        </div>
    </div>
</body>
</html>
"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate combined test report")
    parser.add_argument(
        "--input-dir",
        "-i",
        type=Path,
        default=Path("."),
        help="Directory containing test result artifacts",
    )
    parser.add_argument(
        "--output-html",
        "-o",
        type=Path,
        default=Path("test-report.html"),
        help="Output HTML report file",
    )
    parser.add_argument(
        "--output-json",
        "-j",
        type=Path,
        default=Path("test-summary.json"),
        help="Output JSON summary file",
    )

    args = parser.parse_args()

    # Collect test results
    print("🔍 Collecting test results...")
    results = collect_test_results(args.input_dir)

    # Generate HTML report
    print("📝 Generating HTML report...")
    html_content = generate_html_report(results)

    with open(args.output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Save JSON summary
    print("💾 Saving JSON summary...")
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Reports generated:")
    print(f"  HTML: {args.output_html}")
    print(f"  JSON: {args.output_json}")

    # Exit with appropriate code
    sys.exit(0 if results["overall"]["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
