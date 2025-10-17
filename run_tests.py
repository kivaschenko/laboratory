#!/usr/bin/env python3
"""
Test runner script for the Laboratory Management System.

This script provides an easy way to run different types of tests.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'=' * 60}")
    print(f"🧪 {description}")
    print(f"{'=' * 60}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)

    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run tests for Laboratory Management System"
    )
    parser.add_argument(
        "--type",
        choices=["all", "unit", "functional", "models", "coverage"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Run tests with verbose output"
    )
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run with coverage report"
    )

    args = parser.parse_args()

    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    if not (project_root / "laboratory").exists():
        print("❌ Error: Must run from project root directory")
        sys.exit(1)

    # Base pytest command
    base_cmd = [sys.executable, "-m", "pytest"]
    if args.verbose:
        base_cmd.append("-v")

    success = True

    print("🚀 Laboratory Management System Test Runner")
    print(f"📁 Project directory: {project_root}")

    if args.type == "all":
        # Run all tests
        tests = [
            (base_cmd + ["laboratory/tests.py"], "Unit Tests"),
            (base_cmd + ["test_functional.py"], "Functional Tests"),
        ]

        for cmd, description in tests:
            if not run_command(cmd, description):
                success = False

    elif args.type == "unit":
        success = run_command(base_cmd + ["laboratory/tests.py"], "Unit Tests")

    elif args.type == "functional":
        success = run_command(base_cmd + ["test_functional.py"], "Functional Tests")

    elif args.type == "models":
        success = run_command(
            base_cmd
            + [
                "laboratory/tests.py::TestSubstanceModel",
                "laboratory/tests.py::TestUserModel",
                "laboratory/tests.py::TestSolutionModel",
                "laboratory/tests.py::TestAnalysisModel",
            ],
            "Model Tests",
        )

    elif args.type == "coverage":
        success = run_command(
            base_cmd
            + [
                "--cov=laboratory",
                "--cov-report=html",
                "--cov-report=term-missing",
                "laboratory/tests.py",
                "test_functional.py",
            ],
            "Tests with Coverage",
        )
        if success:
            print("\n📊 Coverage report generated in htmlcov/index.html")

    # Summary
    print(f"\n{'=' * 60}")
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ Your code is ready for deployment.")
    else:
        print("💥 Some tests failed!")
        print("❌ Please fix the failing tests before proceeding.")
    print(f"{'=' * 60}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
