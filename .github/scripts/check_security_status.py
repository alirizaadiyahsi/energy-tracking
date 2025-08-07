#!/usr/bin/env python3
"""
Security Status Checker
Analyzes security scan results and outputs status information for CI/CD pipeline.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityStatusChecker:
    """Check security status from multiple scan results."""

    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        self.status = {
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "info_issues": 0,
            "total_issues": 0,
            "dependency_issues": 0,
            "container_issues": 0,
            "code_issues": 0,
            "secret_issues": 0,
            "infrastructure_issues": 0,
            "license_issues": 0,
            "tools_with_issues": [],
            "failed_scans": [],
            "compliance_status": "unknown",
        }

    def check_safety_report(self, report_file: Path) -> None:
        """Check Safety (Python dependencies) security report."""
        try:
            with open(report_file, "r") as f:
                safety_data = json.load(f)

            if isinstance(safety_data, list) and safety_data:
                self.status["tools_with_issues"].append("Safety")
                for vulnerability in safety_data:
                    severity = self._map_safety_severity(
                        vulnerability.get("severity", "medium")
                    )
                    self._update_counts(severity, "dependency")

        except Exception as e:
            logger.warning(f"Failed to check Safety report {report_file}: {e}")
            self.status["failed_scans"].append("Safety")

    def check_bandit_report(self, report_file: Path) -> None:
        """Check Bandit (Python SAST) security report."""
        try:
            with open(report_file, "r") as f:
                bandit_data = json.load(f)

            results = bandit_data.get("results", [])
            if results:
                self.status["tools_with_issues"].append("Bandit")
                for result in results:
                    severity = self._map_bandit_severity(
                        result.get("issue_severity", "medium")
                    )
                    self._update_counts(severity, "code")

        except Exception as e:
            logger.warning(f"Failed to check Bandit report {report_file}: {e}")
            self.status["failed_scans"].append("Bandit")

    def check_npm_audit_report(self, report_file: Path) -> None:
        """Check npm audit security report."""
        try:
            with open(report_file, "r") as f:
                npm_data = json.load(f)

            vulnerabilities = npm_data.get("vulnerabilities", {})
            if vulnerabilities:
                self.status["tools_with_issues"].append("npm audit")
                for vuln_id, vulnerability in vulnerabilities.items():
                    severity = self._map_npm_severity(
                        vulnerability.get("severity", "moderate")
                    )
                    self._update_counts(severity, "dependency")

        except Exception as e:
            logger.warning(f"Failed to check npm audit report {report_file}: {e}")
            self.status["failed_scans"].append("npm audit")

    def check_trivy_sarif(self, report_file: Path) -> None:
        """Check Trivy container scan SARIF report."""
        try:
            with open(report_file, "r") as f:
                sarif_data = json.load(f)

            has_results = False
            for run in sarif_data.get("runs", []):
                results = run.get("results", [])
                if results:
                    has_results = True
                    for result in results:
                        severity = self._map_sarif_severity(
                            result.get("level", "warning")
                        )
                        self._update_counts(severity, "container")

            if has_results:
                self.status["tools_with_issues"].append("Trivy")

        except Exception as e:
            logger.warning(f"Failed to check Trivy SARIF report {report_file}: {e}")
            self.status["failed_scans"].append("Trivy")

    def check_semgrep_sarif(self, report_file: Path) -> None:
        """Check Semgrep SAST SARIF report."""
        try:
            with open(report_file, "r") as f:
                sarif_data = json.load(f)

            has_results = False
            for run in sarif_data.get("runs", []):
                results = run.get("results", [])
                if results:
                    has_results = True
                    for result in results:
                        severity = self._map_sarif_severity(
                            result.get("level", "warning")
                        )
                        self._update_counts(severity, "code")

            if has_results:
                self.status["tools_with_issues"].append("Semgrep")

        except Exception as e:
            logger.warning(f"Failed to check Semgrep SARIF report {report_file}: {e}")
            self.status["failed_scans"].append("Semgrep")

    def check_secret_scans(self) -> None:
        """Check for secret scanning results."""
        # Check for TruffleHog results (usually in workflow output)
        # Check for GitLeaks results (usually in workflow output)
        # For now, we'll look for any indication of secret issues
        # This would be implemented based on actual tool outputs
        pass

    def check_license_compliance(self) -> None:
        """Check license compliance reports."""
        # Check Python licenses
        python_licenses_file = self.input_dir / "python-licenses.json"
        if python_licenses_file.exists():
            try:
                with open(python_licenses_file, "r") as f:
                    python_licenses = json.load(f)

                problematic_licenses = [
                    "GPL v3",
                    "AGPL v3",
                    "GPL v2",
                    "GPL-3.0",
                    "AGPL-3.0",
                    "GPL-2.0",
                ]

                for package in python_licenses:
                    license_name = package.get("License", "")
                    if any(prob in license_name for prob in problematic_licenses):
                        self._update_counts("medium", "license")

            except Exception as e:
                logger.warning(f"Failed to check Python licenses: {e}")

        # Check Node.js licenses
        nodejs_licenses_file = self.input_dir / "nodejs-licenses.json"
        if nodejs_licenses_file.exists():
            try:
                with open(nodejs_licenses_file, "r") as f:
                    nodejs_licenses = json.load(f)

                problematic_licenses = ["GPL-3.0", "AGPL-3.0", "GPL-2.0"]

                for package_name, package_info in nodejs_licenses.items():
                    license_name = package_info.get("licenses", "")
                    if any(prob in license_name for prob in problematic_licenses):
                        self._update_counts("medium", "license")

            except Exception as e:
                logger.warning(f"Failed to check Node.js licenses: {e}")

    def check_all_reports(self) -> None:
        """Check all available security reports."""
        logger.info("Checking security reports...")

        # Find and check all security report files
        report_patterns = {
            "safety-report.json": self.check_safety_report,
            "bandit-report.json": self.check_bandit_report,
            "npm-audit-report.json": self.check_npm_audit_report,
            "trivy-results-*.sarif": self.check_trivy_sarif,
            "semgrep.sarif": self.check_semgrep_sarif,
        }

        for pattern, checker_func in report_patterns.items():
            if "*" in pattern:
                # Handle glob patterns
                for report_file in self.input_dir.rglob(pattern):
                    checker_func(report_file)
            else:
                report_file = self.input_dir / pattern
                if report_file.exists():
                    checker_func(report_file)

        # Check secret scans
        self.check_secret_scans()

        # Check license compliance
        self.check_license_compliance()

        # Calculate total issues
        self.status["total_issues"] = (
            self.status["critical_issues"]
            + self.status["high_issues"]
            + self.status["medium_issues"]
            + self.status["low_issues"]
            + self.status["info_issues"]
        )

        # Determine compliance status
        self._determine_compliance_status()

        logger.info(
            f"Security check completed: {self.status['total_issues']} total issues found"
        )

    def output_github_vars(self, output_var: str) -> None:
        """Output variables for GitHub Actions."""
        if output_var:
            # Write to GitHub Actions output file
            with open(output_var, "a") as f:
                for key, value in self.status.items():
                    if isinstance(value, list):
                        value = ",".join(value)
                    f.write(f"{key}={value}\n")

        # Also output to stdout for logging
        print("Security Status Summary:")
        print(f"Critical Issues: {self.status['critical_issues']}")
        print(f"High Issues: {self.status['high_issues']}")
        print(f"Medium Issues: {self.status['medium_issues']}")
        print(f"Low Issues: {self.status['low_issues']}")
        print(f"Total Issues: {self.status['total_issues']}")
        print(f"Compliance Status: {self.status['compliance_status']}")

        if self.status["tools_with_issues"]:
            print(f"Tools with Issues: {', '.join(self.status['tools_with_issues'])}")

        if self.status["failed_scans"]:
            print(f"Failed Scans: {', '.join(self.status['failed_scans'])}")

    def _update_counts(self, severity: str, category: str) -> None:
        """Update issue counts."""
        # Update severity counts
        severity_key = f"{severity}_issues"
        if severity_key in self.status:
            self.status[severity_key] += 1

        # Update category counts
        category_key = f"{category}_issues"
        if category_key in self.status:
            self.status[category_key] += 1

    def _determine_compliance_status(self) -> None:
        """Determine overall compliance status."""
        if self.status["critical_issues"] > 0:
            self.status["compliance_status"] = "critical_failure"
        elif self.status["high_issues"] > 5:  # Threshold for high issues
            self.status["compliance_status"] = "high_risk"
        elif self.status["high_issues"] > 0 or self.status["medium_issues"] > 10:
            self.status["compliance_status"] = "medium_risk"
        elif self.status["medium_issues"] > 0 or self.status["low_issues"] > 0:
            self.status["compliance_status"] = "low_risk"
        else:
            self.status["compliance_status"] = "compliant"

    def _map_safety_severity(self, severity: str) -> str:
        """Map Safety severity to standard levels."""
        severity_map = {"high": "high", "medium": "medium", "low": "low"}
        return severity_map.get(severity.lower(), "medium")

    def _map_bandit_severity(self, severity: str) -> str:
        """Map Bandit severity to standard levels."""
        severity_map = {"high": "high", "medium": "medium", "low": "low"}
        return severity_map.get(severity.lower(), "medium")

    def _map_npm_severity(self, severity: str) -> str:
        """Map npm audit severity to standard levels."""
        severity_map = {
            "critical": "critical",
            "high": "high",
            "moderate": "medium",
            "low": "low",
            "info": "info",
        }
        return severity_map.get(severity.lower(), "medium")

    def _map_sarif_severity(self, level: str) -> str:
        """Map SARIF level to standard severity."""
        level_map = {
            "error": "high",
            "warning": "medium",
            "note": "low",
            "info": "info",
        }
        return level_map.get(level.lower(), "medium")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check security status from scan results"
    )
    parser.add_argument(
        "--input-dir", required=True, help="Directory containing security scan results"
    )
    parser.add_argument("--output-var", help="GitHub Actions output variable file")

    args = parser.parse_args()

    try:
        checker = SecurityStatusChecker(args.input_dir)
        checker.check_all_reports()
        checker.output_github_vars(args.output_var)

        # Exit with appropriate code based on severity
        if checker.status["critical_issues"] > 0:
            logger.error("Critical security issues found!")
            sys.exit(2)  # Critical failure
        elif checker.status["high_issues"] > 0:
            logger.warning("High severity security issues found!")
            sys.exit(1)  # High risk
        else:
            logger.info("Security check passed")
            sys.exit(0)  # Success

    except Exception as e:
        logger.error(f"Failed to check security status: {e}")
        sys.exit(3)  # Script failure


if __name__ == "__main__":
    main()
