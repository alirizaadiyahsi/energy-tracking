#!/usr/bin/env python3
"""
Security Report Generator
Aggregates security scan results from multiple tools and generates comprehensive reports.
"""

import argparse
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityReportGenerator:
    """Generate comprehensive security reports from multiple scan tools."""

    def __init__(self, input_dir: str, output_file: str):
        self.input_dir = Path(input_dir)
        self.output_file = output_file
        self.security_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
                "total": 0,
            },
            "categories": {
                "dependency_vulnerabilities": [],
                "container_vulnerabilities": [],
                "code_vulnerabilities": [],
                "secret_exposures": [],
                "infrastructure_issues": [],
                "license_issues": [],
            },
            "tools_executed": [],
            "compliance_status": {},
        }

    def parse_safety_report(self, report_file: Path) -> None:
        """Parse Safety (Python dependencies) security report."""
        try:
            with open(report_file, "r") as f:
                safety_data = json.load(f)

            self.security_data["tools_executed"].append("Safety")

            for vulnerability in safety_data:
                issue = {
                    "tool": "Safety",
                    "category": "dependency",
                    "severity": self._map_safety_severity(
                        vulnerability.get("severity", "medium")
                    ),
                    "package": vulnerability.get("package_name", "unknown"),
                    "version": vulnerability.get("installed_version", "unknown"),
                    "vulnerability_id": vulnerability.get("vulnerability_id", ""),
                    "title": vulnerability.get("advisory", "Dependency vulnerability"),
                    "description": vulnerability.get("advisory", ""),
                    "fixed_versions": vulnerability.get("fixed_versions", []),
                    "references": vulnerability.get("more_info_url", ""),
                }

                self.security_data["categories"]["dependency_vulnerabilities"].append(
                    issue
                )
                self._update_severity_count(issue["severity"])

        except Exception as e:
            logger.warning(f"Failed to parse Safety report {report_file}: {e}")

    def parse_bandit_report(self, report_file: Path) -> None:
        """Parse Bandit (Python SAST) security report."""
        try:
            with open(report_file, "r") as f:
                bandit_data = json.load(f)

            self.security_data["tools_executed"].append("Bandit")

            for result in bandit_data.get("results", []):
                issue = {
                    "tool": "Bandit",
                    "category": "code",
                    "severity": self._map_bandit_severity(
                        result.get("issue_severity", "medium")
                    ),
                    "confidence": result.get("issue_confidence", "medium"),
                    "title": result.get("issue_text", "Code security issue"),
                    "description": result.get("issue_text", ""),
                    "file": result.get("filename", ""),
                    "line": result.get("line_number", 0),
                    "test_id": result.get("test_id", ""),
                    "test_name": result.get("test_name", ""),
                    "code": result.get("code", ""),
                    "references": f"https://bandit.readthedocs.io/en/latest/plugins/{result.get('test_id', '').lower()}_test.html",
                }

                self.security_data["categories"]["code_vulnerabilities"].append(issue)
                self._update_severity_count(issue["severity"])

        except Exception as e:
            logger.warning(f"Failed to parse Bandit report {report_file}: {e}")

    def parse_npm_audit_report(self, report_file: Path) -> None:
        """Parse npm audit security report."""
        try:
            with open(report_file, "r") as f:
                npm_data = json.load(f)

            self.security_data["tools_executed"].append("npm audit")

            for vuln_id, vulnerability in npm_data.get("vulnerabilities", {}).items():
                issue = {
                    "tool": "npm audit",
                    "category": "dependency",
                    "severity": self._map_npm_severity(
                        vulnerability.get("severity", "moderate")
                    ),
                    "package": vulnerability.get("name", vuln_id),
                    "range": vulnerability.get("range", ""),
                    "title": vulnerability.get(
                        "title", "Node.js dependency vulnerability"
                    ),
                    "description": vulnerability.get("overview", ""),
                    "recommendation": vulnerability.get("recommendation", ""),
                    "references": vulnerability.get("url", ""),
                    "cwe": vulnerability.get("cwe", []),
                    "cvss": vulnerability.get("cvss", {}),
                }

                self.security_data["categories"]["dependency_vulnerabilities"].append(
                    issue
                )
                self._update_severity_count(issue["severity"])

        except Exception as e:
            logger.warning(f"Failed to parse npm audit report {report_file}: {e}")

    def parse_trivy_sarif(self, report_file: Path) -> None:
        """Parse Trivy container scan SARIF report."""
        try:
            with open(report_file, "r") as f:
                sarif_data = json.load(f)

            self.security_data["tools_executed"].append("Trivy")

            for run in sarif_data.get("runs", []):
                for result in run.get("results", []):
                    rule_id = result.get("ruleId", "")
                    rule = self._find_sarif_rule(run, rule_id)

                    issue = {
                        "tool": "Trivy",
                        "category": "container",
                        "severity": self._map_sarif_severity(
                            result.get("level", "warning")
                        ),
                        "rule_id": rule_id,
                        "title": rule.get("shortDescription", {}).get(
                            "text", "Container vulnerability"
                        ),
                        "description": rule.get("fullDescription", {}).get("text", ""),
                        "file": self._get_sarif_location_file(result),
                        "line": self._get_sarif_location_line(result),
                        "references": self._get_sarif_help_uri(rule),
                    }

                    self.security_data["categories"][
                        "container_vulnerabilities"
                    ].append(issue)
                    self._update_severity_count(issue["severity"])

        except Exception as e:
            logger.warning(f"Failed to parse Trivy SARIF report {report_file}: {e}")

    def parse_semgrep_sarif(self, report_file: Path) -> None:
        """Parse Semgrep SAST SARIF report."""
        try:
            with open(report_file, "r") as f:
                sarif_data = json.load(f)

            self.security_data["tools_executed"].append("Semgrep")

            for run in sarif_data.get("runs", []):
                for result in run.get("results", []):
                    rule_id = result.get("ruleId", "")
                    rule = self._find_sarif_rule(run, rule_id)

                    issue = {
                        "tool": "Semgrep",
                        "category": "code",
                        "severity": self._map_sarif_severity(
                            result.get("level", "warning")
                        ),
                        "rule_id": rule_id,
                        "title": rule.get("shortDescription", {}).get(
                            "text", "Code security issue"
                        ),
                        "description": rule.get("fullDescription", {}).get("text", ""),
                        "file": self._get_sarif_location_file(result),
                        "line": self._get_sarif_location_line(result),
                        "references": self._get_sarif_help_uri(rule),
                    }

                    self.security_data["categories"]["code_vulnerabilities"].append(
                        issue
                    )
                    self._update_severity_count(issue["severity"])

        except Exception as e:
            logger.warning(f"Failed to parse Semgrep SARIF report {report_file}: {e}")

    def parse_license_reports(self) -> None:
        """Parse license compliance reports."""
        # Parse Python licenses
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
                        issue = {
                            "tool": "pip-licenses",
                            "category": "license",
                            "severity": "medium",
                            "package": package.get("Name", ""),
                            "version": package.get("Version", ""),
                            "license": license_name,
                            "title": f"Problematic license: {license_name}",
                            "description": f"Package {package.get('Name', '')} uses {license_name} which may have compliance issues",
                        }

                        self.security_data["categories"]["license_issues"].append(issue)
                        self._update_severity_count("medium")

            except Exception as e:
                logger.warning(f"Failed to parse Python licenses: {e}")

        # Parse Node.js licenses
        nodejs_licenses_file = self.input_dir / "nodejs-licenses.json"
        if nodejs_licenses_file.exists():
            try:
                with open(nodejs_licenses_file, "r") as f:
                    nodejs_licenses = json.load(f)

                problematic_licenses = ["GPL-3.0", "AGPL-3.0", "GPL-2.0"]

                for package_name, package_info in nodejs_licenses.items():
                    license_name = package_info.get("licenses", "")
                    if any(prob in license_name for prob in problematic_licenses):
                        issue = {
                            "tool": "license-checker",
                            "category": "license",
                            "severity": "medium",
                            "package": package_name,
                            "version": package_info.get("version", ""),
                            "license": license_name,
                            "title": f"Problematic license: {license_name}",
                            "description": f"Package {package_name} uses {license_name} which may have compliance issues",
                        }

                        self.security_data["categories"]["license_issues"].append(issue)
                        self._update_severity_count("medium")

            except Exception as e:
                logger.warning(f"Failed to parse Node.js licenses: {e}")

    def collect_reports(self) -> None:
        """Collect and parse all available security reports."""
        logger.info("Collecting security reports...")

        # Find and parse all security report files
        report_patterns = {
            "safety-report.json": self.parse_safety_report,
            "bandit-report.json": self.parse_bandit_report,
            "npm-audit-report.json": self.parse_npm_audit_report,
            "trivy-results-*.sarif": self.parse_trivy_sarif,
            "semgrep.sarif": self.parse_semgrep_sarif,
        }

        for pattern, parser_func in report_patterns.items():
            if "*" in pattern:
                # Handle glob patterns
                for report_file in self.input_dir.rglob(pattern):
                    parser_func(report_file)
            else:
                report_file = self.input_dir / pattern
                if report_file.exists():
                    parser_func(report_file)

        # Parse license reports
        self.parse_license_reports()

        # Calculate total issues
        self.security_data["summary"]["total"] = sum(
            self.security_data["summary"][severity]
            for severity in ["critical", "high", "medium", "low", "info"]
        )

        logger.info(
            f"Found {self.security_data['summary']['total']} total security issues"
        )

    def generate_html_report(self) -> None:
        """Generate comprehensive HTML security report."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Dashboard - Energy Tracking</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
        .header p {{ opacity: 0.9; font-size: 1.1rem; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .summary-card {{ background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .summary-card h3 {{ color: #666; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 0.5rem; }}
        .summary-card .number {{ font-size: 2.5rem; font-weight: bold; }}
        .critical {{ color: #dc3545; }}
        .high {{ color: #fd7e14; }}
        .medium {{ color: #ffc107; }}
        .low {{ color: #28a745; }}
        .info {{ color: #17a2b8; }}
        .section {{ background: white; margin-bottom: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
        .section-header {{ background: #f8f9fa; padding: 1rem 1.5rem; border-bottom: 1px solid #e9ecef; }}
        .section-header h2 {{ color: #495057; }}
        .section-content {{ padding: 1.5rem; }}
        .issue-item {{ border: 1px solid #e9ecef; border-radius: 6px; margin-bottom: 1rem; overflow: hidden; }}
        .issue-header {{ padding: 1rem; background: #f8f9fa; display: flex; justify-content: between; align-items: center; }}
        .issue-title {{ font-weight: bold; flex: 1; }}
        .severity-badge {{ padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; color: white; }}
        .severity-critical {{ background: #dc3545; }}
        .severity-high {{ background: #fd7e14; }}
        .severity-medium {{ background: #ffc107; color: #212529; }}
        .severity-low {{ background: #28a745; }}
        .severity-info {{ background: #17a2b8; }}
        .issue-details {{ padding: 1rem; }}
        .issue-meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem; }}
        .meta-item {{ background: #f8f9fa; padding: 0.75rem; border-radius: 4px; }}
        .meta-label {{ font-weight: bold; color: #666; font-size: 0.8rem; text-transform: uppercase; }}
        .meta-value {{ margin-top: 0.25rem; }}
        .tools-list {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
        .tool-badge {{ background: #6c757d; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; }}
        .footer {{ text-align: center; color: #666; margin-top: 2rem; }}
        .no-issues {{ text-align: center; color: #666; padding: 2rem; }}
        .no-issues svg {{ width: 64px; height: 64px; margin-bottom: 1rem; opacity: 0.5; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Security Dashboard</h1>
            <p>Security scan results for Energy Tracking Platform</p>
            <p style="font-size: 0.9rem; opacity: 0.8;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Critical</h3>
                <div class="number critical">{self.security_data['summary']['critical']}</div>
            </div>
            <div class="summary-card">
                <h3>High</h3>
                <div class="number high">{self.security_data['summary']['high']}</div>
            </div>
            <div class="summary-card">
                <h3>Medium</h3>
                <div class="number medium">{self.security_data['summary']['medium']}</div>
            </div>
            <div class="summary-card">
                <h3>Low</h3>
                <div class="number low">{self.security_data['summary']['low']}</div>
            </div>
            <div class="summary-card">
                <h3>Total Issues</h3>
                <div class="number">{self.security_data['summary']['total']}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>🛠️ Tools Executed</h2>
            </div>
            <div class="section-content">
                <div class="tools-list">
                    {self._generate_tools_list()}
                </div>
            </div>
        </div>
        
        {self._generate_category_sections()}
        
        <div class="footer">
            <p>Generated by Energy Tracking Security Scanner</p>
            <p>For more information, visit the security documentation</p>
        </div>
    </div>
</body>
</html>
        """

        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Security report generated: {self.output_file}")

    def _generate_tools_list(self) -> str:
        """Generate HTML for tools list."""
        if not self.security_data["tools_executed"]:
            return '<p class="no-issues">No security tools were executed</p>'

        tools_html = ""
        for tool in set(self.security_data["tools_executed"]):
            tools_html += f'<span class="tool-badge">{tool}</span>'

        return tools_html

    def _generate_category_sections(self) -> str:
        """Generate HTML for all security categories."""
        sections_html = ""

        category_info = {
            "dependency_vulnerabilities": (
                "📦 Dependency Vulnerabilities",
                "Vulnerabilities in third-party dependencies",
            ),
            "container_vulnerabilities": (
                "🐳 Container Vulnerabilities",
                "Security issues in container images",
            ),
            "code_vulnerabilities": (
                "💻 Code Vulnerabilities",
                "Security issues in application code",
            ),
            "secret_exposures": (
                "🔑 Secret Exposures",
                "Exposed secrets and credentials",
            ),
            "infrastructure_issues": (
                "🏗️ Infrastructure Issues",
                "Infrastructure and configuration security issues",
            ),
            "license_issues": ("📄 License Issues", "License compliance issues"),
        }

        for category, issues in self.security_data["categories"].items():
            if category in category_info:
                title, description = category_info[category]
                sections_html += self._generate_category_section(
                    title, description, issues
                )

        return sections_html

    def _generate_category_section(
        self, title: str, description: str, issues: List[Dict]
    ) -> str:
        """Generate HTML for a specific security category."""
        if not issues:
            return f"""
            <div class="section">
                <div class="section-header">
                    <h2>{title}</h2>
                </div>
                <div class="section-content">
                    <div class="no-issues">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                        <p>No issues found in this category</p>
                    </div>
                </div>
            </div>
            """

        issues_html = ""
        for issue in issues:
            issues_html += self._generate_issue_html(issue)

        return f"""
        <div class="section">
            <div class="section-header">
                <h2>{title}</h2>
                <p style="color: #666; margin-top: 0.5rem;">{description}</p>
            </div>
            <div class="section-content">
                {issues_html}
            </div>
        </div>
        """

    def _generate_issue_html(self, issue: Dict) -> str:
        """Generate HTML for a single security issue."""
        severity = issue.get("severity", "info").lower()

        meta_items = []

        # Add relevant metadata based on issue type
        if issue.get("package"):
            meta_items.append(("Package", issue["package"]))
        if issue.get("version"):
            meta_items.append(("Version", issue["version"]))
        if issue.get("file"):
            meta_items.append(("File", issue["file"]))
        if issue.get("line"):
            meta_items.append(("Line", str(issue["line"])))
        if issue.get("rule_id"):
            meta_items.append(("Rule ID", issue["rule_id"]))
        if issue.get("tool"):
            meta_items.append(("Tool", issue["tool"]))
        if issue.get("confidence"):
            meta_items.append(("Confidence", issue["confidence"]))

        meta_html = ""
        for label, value in meta_items:
            meta_html += f"""
            <div class="meta-item">
                <div class="meta-label">{label}</div>
                <div class="meta-value">{value}</div>
            </div>
            """

        references_html = ""
        if issue.get("references"):
            references_html = f'<a href="{issue["references"]}" target="_blank" style="color: #007bff;">View Details</a>'

        return f"""
        <div class="issue-item">
            <div class="issue-header">
                <div class="issue-title">{issue.get('title', 'Security Issue')}</div>
                <span class="severity-badge severity-{severity}">{severity.upper()}</span>
            </div>
            <div class="issue-details">
                <p>{issue.get('description', 'No description available')}</p>
                {f'<div class="issue-meta">{meta_html}</div>' if meta_html else ''}
                {references_html}
            </div>
        </div>
        """

    def _update_severity_count(self, severity: str) -> None:
        """Update severity counts in summary."""
        severity = severity.lower()
        if severity in self.security_data["summary"]:
            self.security_data["summary"][severity] += 1

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

    def _find_sarif_rule(self, run: Dict, rule_id: str) -> Dict:
        """Find rule definition in SARIF run."""
        driver = run.get("tool", {}).get("driver", {})
        for rule in driver.get("rules", []):
            if rule.get("id") == rule_id:
                return rule
        return {}

    def _get_sarif_location_file(self, result: Dict) -> str:
        """Extract file path from SARIF result."""
        locations = result.get("locations", [])
        if locations:
            physical_location = locations[0].get("physicalLocation", {})
            artifact_location = physical_location.get("artifactLocation", {})
            return artifact_location.get("uri", "")
        return ""

    def _get_sarif_location_line(self, result: Dict) -> int:
        """Extract line number from SARIF result."""
        locations = result.get("locations", [])
        if locations:
            physical_location = locations[0].get("physicalLocation", {})
            region = physical_location.get("region", {})
            return region.get("startLine", 0)
        return 0

    def _get_sarif_help_uri(self, rule: Dict) -> str:
        """Extract help URI from SARIF rule."""
        return rule.get("helpUri", "")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate security report from scan results"
    )
    parser.add_argument(
        "--input-dir", required=True, help="Directory containing security scan results"
    )
    parser.add_argument("--output", required=True, help="Output HTML report file")

    args = parser.parse_args()

    try:
        generator = SecurityReportGenerator(args.input_dir, args.output)
        generator.collect_reports()
        generator.generate_html_report()

        # Output summary for CI
        summary = generator.security_data["summary"]
        print(f"Security scan completed successfully")
        print(f"Total issues: {summary['total']}")
        print(
            f"Critical: {summary['critical']}, High: {summary['high']}, Medium: {summary['medium']}"
        )

        # Exit with non-zero code if critical issues found
        if summary["critical"] > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Failed to generate security report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
