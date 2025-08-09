#!/usr/bin/env python3
"""
CI/CD Pipeline Comparison Tool
Compare local CI simulation with actual GitHub Actions workflow
"""

import json
from pathlib import Path
from typing import Dict, Set

import yaml


def load_github_workflow() -> Dict:
    """Load the main GitHub Actions workflow"""
    workflow_path = Path(".github/workflows/ci-cd.yml")
    if not workflow_path.exists():
        return {}

    with open(workflow_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_workflow_stages(workflow: Dict) -> Set[str]:
    """Extract stage names from GitHub workflow"""
    if "jobs" not in workflow:
        return set()

    stages = set()
    for job_name, job_config in workflow["jobs"].items():
        # Map job names to our stage names
        stage_mapping = {
            "lint": "lint",
            "unit-tests": "unit",
            "integration-tests": "integration",
            "frontend-tests": "frontend",
            "security-tests": "security",
            "docker-build": "docker",
            "e2e-tests": "e2e",
            "performance-tests": "performance",
        }

        if job_name in stage_mapping:
            stages.add(stage_mapping[job_name])
        else:
            stages.add(job_name)

    return stages


def get_local_stages() -> Set[str]:
    """Get stages supported by local simulation"""
    return {
        "lint",
        "unit",
        "integration",
        "frontend",
        "security",
        "docker",
        "e2e",
        "performance",
    }


def compare_tool_coverage() -> Dict:
    """Compare tool coverage between GitHub and local"""
    github_tools = {
        "lint": ["black", "isort", "flake8", "mypy", "eslint"],
        "unit": ["pytest", "npm test", "coverage"],
        "integration": ["pytest", "docker-compose", "psql"],
        "security": ["bandit", "safety", "semgrep"],
        "docker": ["docker build"],
        "e2e": ["pytest", "docker-compose"],
        "performance": ["locust"],
    }

    local_tools = {
        "lint": ["black", "isort", "flake8", "mypy", "eslint"],
        "unit": ["pytest", "npm test", "coverage"],
        "integration": ["pytest", "docker-compose", "psql"],
        "security": ["bandit", "safety"],  # semgrep optional
        "docker": ["docker build"],
        "e2e": ["pytest", "docker-compose"],
        "performance": ["locust"],
    }

    comparison = {}
    for stage in github_tools:
        github_set = set(github_tools[stage])
        local_set = set(local_tools.get(stage, []))

        comparison[stage] = {
            "github_only": list(github_set - local_set),
            "local_only": list(local_set - github_set),
            "common": list(github_set & local_set),
            "coverage_percent": (
                round((len(github_set & local_set) / len(github_set)) * 100, 1)
                if github_set
                else 100
            ),
        }

    return comparison


def generate_comparison_report() -> Dict:
    """Generate comprehensive comparison report"""
    workflow = load_github_workflow()
    github_stages = extract_workflow_stages(workflow)
    local_stages = get_local_stages()
    tool_comparison = compare_tool_coverage()

    # Calculate overall coverage
    common_stages = github_stages & local_stages
    stage_coverage = (
        (len(common_stages) / len(github_stages)) * 100 if github_stages else 0
    )

    # Calculate tool coverage
    tool_coverages = [comp["coverage_percent"] for comp in tool_comparison.values()]
    avg_tool_coverage = (
        sum(tool_coverages) / len(tool_coverages) if tool_coverages else 0
    )

    report = {
        "summary": {
            "stage_coverage_percent": round(stage_coverage, 1),
            "tool_coverage_percent": round(avg_tool_coverage, 1),
            "overall_accuracy": round((stage_coverage + avg_tool_coverage) / 2, 1),
        },
        "stages": {
            "github_only": list(github_stages - local_stages),
            "local_only": list(local_stages - github_stages),
            "common": list(common_stages),
            "total_github": len(github_stages),
            "total_local": len(local_stages),
            "total_common": len(common_stages),
        },
        "tools": tool_comparison,
        "recommendations": [],
    }

    # Add recommendations
    if report["summary"]["overall_accuracy"] < 90:
        report["recommendations"].append(
            "Consider adding missing tools to improve CI accuracy"
        )

    if github_stages - local_stages:
        report["recommendations"].append(
            f"Add local support for: {', '.join(github_stages - local_stages)}"
        )

    if any(comp["coverage_percent"] < 80 for comp in tool_comparison.values()):
        low_coverage_stages = [
            stage
            for stage, comp in tool_comparison.items()
            if comp["coverage_percent"] < 80
        ]
        report["recommendations"].append(
            f"Improve tool coverage for: {', '.join(low_coverage_stages)}"
        )

    return report


def print_comparison_report():
    """Print a formatted comparison report"""
    report = generate_comparison_report()

    print("🔍 CI/CD Pipeline Comparison Report")
    print("=" * 50)
    print()

    # Summary
    summary = report["summary"]
    print("📊 SUMMARY")
    print(f"   Stage Coverage: {summary['stage_coverage_percent']}%")
    print(f"   Tool Coverage: {summary['tool_coverage_percent']}%")
    print(f"   Overall Accuracy: {summary['overall_accuracy']}%")
    print()

    # Stage comparison
    stages = report["stages"]
    print("🎯 STAGE COMPARISON")
    print(f"   GitHub Stages: {stages['total_github']}")
    print(f"   Local Stages: {stages['total_local']}")
    print(f"   Common Stages: {stages['total_common']}")

    if stages["common"]:
        print(f"   ✅ Supported: {', '.join(stages['common'])}")

    if stages["github_only"]:
        print(f"   ❌ Missing: {', '.join(stages['github_only'])}")

    if stages["local_only"]:
        print(f"   ➕ Extra: {', '.join(stages['local_only'])}")
    print()

    # Tool comparison
    print("🔧 TOOL COMPARISON")
    for stage, comparison in report["tools"].items():
        coverage = comparison["coverage_percent"]
        status = "✅" if coverage >= 90 else "⚠️" if coverage >= 70 else "❌"

        print(f"   {status} {stage.upper()}: {coverage}% coverage")

        if comparison["common"]:
            print(f"      ✅ Common: {', '.join(comparison['common'])}")

        if comparison["github_only"]:
            print(f"      ❌ Missing: {', '.join(comparison['github_only'])}")

        if comparison["local_only"]:
            print(f"      ➕ Extra: {', '.join(comparison['local_only'])}")
        print()

    # Recommendations
    if report["recommendations"]:
        print("💡 RECOMMENDATIONS")
        for rec in report["recommendations"]:
            print(f"   • {rec}")
        print()

    # Conclusion
    accuracy = summary["overall_accuracy"]
    if accuracy >= 95:
        print("🎉 EXCELLENT! Your local CI simulation is highly accurate.")
    elif accuracy >= 85:
        print("✅ GOOD! Your local CI simulation provides solid coverage.")
    elif accuracy >= 70:
        print("⚠️ FAIR! Consider improving your local CI simulation.")
    else:
        print("❌ POOR! Significant improvements needed for local CI simulation.")


if __name__ == "__main__":
    print_comparison_report()

    # Also save JSON report
    report = generate_comparison_report()
    with open("ci-comparison-report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("📄 Detailed report saved to: ci-comparison-report.json")
