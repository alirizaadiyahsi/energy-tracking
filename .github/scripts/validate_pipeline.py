#!/usr/bin/env python3
"""
CI/CD Pipeline Validation Script
Validates the complete CI/CD setup and provides a summary of all workflows.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineValidator:
    """Validate CI/CD pipeline configuration."""

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.workflows_dir = self.repo_root / ".github" / "workflows"
        self.scripts_dir = self.repo_root / ".github" / "scripts"
        self.validation_results = {
            "workflows": {},
            "scripts": {},
            "config_files": {},
            "issues": [],
            "recommendations": [],
        }

    def validate_workflows(self) -> None:
        """Validate all GitHub Actions workflow files."""
        logger.info("Validating workflow files...")

        expected_workflows = {
            "ci.yml": "Main CI pipeline",
            "performance.yml": "Performance testing",
            "e2e.yml": "End-to-end testing",
            "security.yml": "Security scanning",
            "release.yml": "Release pipeline",
        }

        for workflow_file, description in expected_workflows.items():
            workflow_path = self.workflows_dir / workflow_file

            if not workflow_path.exists():
                self.validation_results["issues"].append(
                    f"Missing workflow file: {workflow_file}"
                )
                continue

            try:
                with open(workflow_path, "r", encoding="utf-8") as f:
                    workflow_data = yaml.safe_load(f)

                validation = self._validate_workflow_structure(
                    workflow_data, workflow_file
                )
                self.validation_results["workflows"][workflow_file] = {
                    "description": description,
                    "status": "valid" if validation["valid"] else "invalid",
                    "jobs": validation["jobs"],
                    "triggers": validation["triggers"],
                    "issues": validation["issues"],
                }

                if validation["issues"]:
                    self.validation_results["issues"].extend(
                        [f"{workflow_file}: {issue}" for issue in validation["issues"]]
                    )

            except Exception as e:
                self.validation_results["issues"].append(
                    f"Failed to parse {workflow_file}: {e}"
                )
                self.validation_results["workflows"][workflow_file] = {
                    "description": description,
                    "status": "error",
                    "error": str(e),
                }

    def validate_scripts(self) -> None:
        """Validate supporting scripts."""
        logger.info("Validating support scripts...")

        expected_scripts = {
            "generate_test_report.py": "Test report generation",
            "run_critical_path_tests.py": "Critical path testing",
            "generate_security_report.py": "Security report generation",
            "check_security_status.py": "Security status checking",
        }

        for script_file, description in expected_scripts.items():
            script_path = self.scripts_dir / script_file

            if not script_path.exists():
                self.validation_results["issues"].append(
                    f"Missing script file: {script_file}"
                )
                continue

            try:
                # Basic syntax validation
                with open(script_path, "r", encoding="utf-8") as f:
                    script_content = f.read()

                # Check for main function and basic structure
                has_main = "def main(" in script_content
                has_shebang = script_content.startswith("#!/usr/bin/env python3")
                has_docstring = '"""' in script_content

                self.validation_results["scripts"][script_file] = {
                    "description": description,
                    "status": "valid",
                    "has_main": has_main,
                    "has_shebang": has_shebang,
                    "has_docstring": has_docstring,
                    "size_kb": round(len(script_content) / 1024, 2),
                }

                if not has_main:
                    self.validation_results["issues"].append(
                        f"{script_file}: Missing main() function"
                    )

            except Exception as e:
                self.validation_results["issues"].append(
                    f"Failed to validate {script_file}: {e}"
                )
                self.validation_results["scripts"][script_file] = {
                    "description": description,
                    "status": "error",
                    "error": str(e),
                }

    def validate_config_files(self) -> None:
        """Validate configuration files."""
        logger.info("Validating configuration files...")

        config_files = {
            ".github/codeql/codeql-config.yml": "CodeQL configuration",
            "frontend/.eslintrc-security.json": "ESLint security configuration",
            "docs/CI_CD_PIPELINE.md": "CI/CD documentation",
        }

        for config_file, description in config_files.items():
            config_path = self.repo_root / config_file

            if not config_path.exists():
                self.validation_results["issues"].append(
                    f"Missing config file: {config_file}"
                )
                continue

            try:
                file_size = config_path.stat().st_size

                self.validation_results["config_files"][config_file] = {
                    "description": description,
                    "status": "exists",
                    "size_kb": round(file_size / 1024, 2),
                }

                # Specific validations
                if config_file.endswith(".yml") or config_file.endswith(".yaml"):
                    with open(config_path, "r", encoding="utf-8") as f:
                        yaml.safe_load(f)  # Validate YAML syntax

                elif config_file.endswith(".json"):
                    with open(config_path, "r", encoding="utf-8") as f:
                        json.load(f)  # Validate JSON syntax

            except Exception as e:
                self.validation_results["issues"].append(
                    f"Invalid config file {config_file}: {e}"
                )
                self.validation_results["config_files"][config_file] = {
                    "description": description,
                    "status": "invalid",
                    "error": str(e),
                }

    def check_dependencies(self) -> None:
        """Check for required dependencies and tools."""
        logger.info("Checking pipeline dependencies...")

        # Check Python requirements in test directories
        test_requirements = self.repo_root / "tests" / "test-requirements.txt"
        if not test_requirements.exists():
            self.validation_results["recommendations"].append(
                "Consider adding tests/test-requirements.txt for test dependencies"
            )

        # Check for Docker files
        docker_files = list(self.repo_root.rglob("Dockerfile*"))
        if not docker_files:
            self.validation_results["issues"].append(
                "No Dockerfile found in the repository"
            )

        # Check for package.json in frontend
        frontend_package = self.repo_root / "frontend" / "package.json"
        if not frontend_package.exists():
            self.validation_results["issues"].append("Missing frontend/package.json")

        # Check for Python requirements in services
        services_dir = self.repo_root / "services"
        if services_dir.exists():
            for service_dir in services_dir.iterdir():
                if service_dir.is_dir():
                    requirements_file = service_dir / "requirements.txt"
                    if not requirements_file.exists():
                        self.validation_results["recommendations"].append(
                            f"Missing requirements.txt in {service_dir.name} service"
                        )

    def generate_recommendations(self) -> None:
        """Generate recommendations for pipeline improvements."""
        logger.info("Generating recommendations...")

        # Workflow-specific recommendations
        workflows = self.validation_results["workflows"]

        if "ci.yml" in workflows:
            ci_workflow = workflows["ci.yml"]
            if ci_workflow.get("status") == "valid":
                if len(ci_workflow.get("jobs", [])) < 6:
                    self.validation_results["recommendations"].append(
                        "Consider adding more comprehensive testing jobs to CI workflow"
                    )

        # Security recommendations
        if "security.yml" in workflows:
            self.validation_results["recommendations"].append(
                "Ensure all security scan results are properly reviewed and addressed"
            )

        # Performance recommendations
        if "performance.yml" in workflows:
            self.validation_results["recommendations"].append(
                "Set up performance baselines and alerting thresholds"
            )

        # General recommendations
        self.validation_results["recommendations"].extend(
            [
                "Regularly update workflow dependencies and GitHub Actions versions",
                "Monitor workflow execution times and optimize for performance",
                "Set up branch protection rules for main and develop branches",
                "Configure required status checks for all critical workflows",
                "Implement proper secret management and rotation policies",
            ]
        )

    def validate_pipeline(self) -> Dict[str, Any]:
        """Run complete pipeline validation."""
        logger.info("Starting CI/CD pipeline validation...")

        self.validate_workflows()
        self.validate_scripts()
        self.validate_config_files()
        self.check_dependencies()
        self.generate_recommendations()

        # Calculate overall status
        total_issues = len(self.validation_results["issues"])
        workflow_count = len(self.validation_results["workflows"])
        script_count = len(self.validation_results["scripts"])

        self.validation_results["summary"] = {
            "total_workflows": workflow_count,
            "total_scripts": script_count,
            "total_issues": total_issues,
            "overall_status": "healthy" if total_issues == 0 else "needs_attention",
            "completion_percentage": self._calculate_completion_percentage(),
        }

        logger.info(
            f"Pipeline validation completed: {self.validation_results['summary']['overall_status']}"
        )

        return self.validation_results

    def _validate_workflow_structure(
        self, workflow_data: Dict, workflow_file: str
    ) -> Dict:
        """Validate individual workflow structure."""
        validation = {"valid": True, "jobs": [], "triggers": [], "issues": []}

        # Check required fields
        if "name" not in workflow_data:
            validation["issues"].append("Missing 'name' field")
            validation["valid"] = False

        if "on" not in workflow_data and True not in workflow_data:
            validation["issues"].append("Missing 'on' (triggers) field")
            validation["valid"] = False
        else:
            # Handle YAML quirk where 'on' becomes True
            trigger_key = "on" if "on" in workflow_data else True
            trigger_data = workflow_data[trigger_key]
            validation["triggers"] = (
                list(trigger_data.keys())
                if isinstance(trigger_data, dict)
                else [trigger_data]
            )

        if "jobs" not in workflow_data:
            validation["issues"].append("Missing 'jobs' field")
            validation["valid"] = False
        else:
            validation["jobs"] = list(workflow_data["jobs"].keys())

            # Check job structure
            for job_name, job_data in workflow_data["jobs"].items():
                if "runs-on" not in job_data:
                    validation["issues"].append(
                        f"Job '{job_name}' missing 'runs-on' field"
                    )
                    validation["valid"] = False

                if "steps" not in job_data:
                    validation["issues"].append(
                        f"Job '{job_name}' missing 'steps' field"
                    )
                    validation["valid"] = False

        # Workflow-specific validations
        if workflow_file == "ci.yml":
            required_jobs = ["code-quality", "unit-tests", "integration-tests"]
            missing_jobs = [
                job for job in required_jobs if job not in validation["jobs"]
            ]
            if missing_jobs:
                validation["issues"].append(f"Missing required CI jobs: {missing_jobs}")

        elif workflow_file == "security.yml":
            required_jobs = ["dependency-scan", "container-scan", "sast-scan"]
            missing_jobs = [
                job for job in required_jobs if job not in validation["jobs"]
            ]
            if missing_jobs:
                validation["issues"].append(
                    f"Missing required security jobs: {missing_jobs}"
                )

        return validation

    def _calculate_completion_percentage(self) -> float:
        """Calculate pipeline completion percentage."""
        expected_items = {
            "workflows": 5,  # 5 main workflows
            "scripts": 4,  # 4 support scripts
            "config_files": 3,  # 3 config files
        }

        actual_items = {
            "workflows": len(
                [
                    w
                    for w in self.validation_results["workflows"].values()
                    if w.get("status") == "valid"
                ]
            ),
            "scripts": len(
                [
                    s
                    for s in self.validation_results["scripts"].values()
                    if s.get("status") == "valid"
                ]
            ),
            "config_files": len(
                [
                    c
                    for c in self.validation_results["config_files"].values()
                    if c.get("status") in ["exists", "valid"]
                ]
            ),
        }

        total_expected = sum(expected_items.values())
        total_actual = sum(actual_items.values())

        return round((total_actual / total_expected) * 100, 1)

    def print_summary(self) -> None:
        """Print validation summary."""
        results = self.validation_results
        summary = results["summary"]

        print("\n" + "=" * 80)
        print("CI/CD PIPELINE VALIDATION SUMMARY")
        print("=" * 80)

        print(f"\n📊 Overall Status: {summary['overall_status'].upper()}")
        print(f"📈 Completion: {summary['completion_percentage']}%")
        print(f"🔧 Workflows: {summary['total_workflows']}")
        print(f"📜 Scripts: {summary['total_scripts']}")
        print(f"⚠️  Issues: {summary['total_issues']}")

        # Workflows summary
        print(f"\n🔄 WORKFLOWS ({len(results['workflows'])})")
        print("-" * 40)
        for workflow, info in results["workflows"].items():
            status_icon = (
                "✅"
                if info["status"] == "valid"
                else "❌" if info["status"] == "invalid" else "⚠️"
            )
            print(f"{status_icon} {workflow:<20} {info['description']}")
            if info.get("jobs"):
                print(f"   Jobs: {', '.join(info['jobs'])}")

        # Scripts summary
        print(f"\n📜 SCRIPTS ({len(results['scripts'])})")
        print("-" * 40)
        for script, info in results["scripts"].items():
            status_icon = "✅" if info["status"] == "valid" else "❌"
            print(f"{status_icon} {script:<30} {info['description']}")
            if info.get("size_kb"):
                print(f"   Size: {info['size_kb']} KB")

        # Configuration files
        print(f"\n⚙️  CONFIG FILES ({len(results['config_files'])})")
        print("-" * 40)
        for config, info in results["config_files"].items():
            status_icon = "✅" if info["status"] in ["exists", "valid"] else "❌"
            print(f"{status_icon} {config}")
            print(f"   {info['description']}")

        # Issues
        if results["issues"]:
            print(f"\n⚠️  ISSUES ({len(results['issues'])})")
            print("-" * 40)
            for issue in results["issues"]:
                print(f"❗ {issue}")

        # Recommendations
        if results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS ({len(results['recommendations'])})")
            print("-" * 40)
            for rec in results["recommendations"]:
                print(f"💡 {rec}")

        print("\n" + "=" * 80)
        print("Validation completed successfully!")
        print("=" * 80 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate CI/CD pipeline configuration"
    )
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--json-output", help="Output results as JSON to file")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress output except errors"
    )

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    try:
        validator = PipelineValidator(args.repo_root)
        results = validator.validate_pipeline()

        if not args.quiet:
            validator.print_summary()

        if args.json_output:
            with open(args.json_output, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.json_output}")

        # Exit with appropriate code
        if results["summary"]["total_issues"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline validation failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
