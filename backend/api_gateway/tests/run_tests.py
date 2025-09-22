#!/usr/bin/env python3
"""
Test runner script for ITAPIA API Gateway.

This script provides a convenient way to run tests with different options.
"""

import argparse
import subprocess
import sys


def run_tests(test_args=None):
    """
    Run tests with the given arguments.

    Args:
        test_args (list): List of arguments to pass to pytest
    """
    if test_args is None:
        test_args = []

    # Base command
    cmd = [sys.executable, "-m", "pytest"] + test_args

    # Run the command
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run ITAPIA API Gateway tests")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run tests with coverage report"
    )
    parser.add_argument(
        "--html", action="store_true", help="Generate HTML coverage report"
    )
    parser.add_argument("--test-file", "-f", type=str, help="Run a specific test file")
    parser.add_argument(
        "--test-dir", "-d", type=str, help="Run tests in a specific directory"
    )

    args = parser.parse_args()

    # Build test arguments
    test_args = []

    if args.verbose:
        test_args.append("-v")

    if args.coverage:
        test_args.extend(["--cov=app", "--cov-report=term-missing"])

    if args.html:
        test_args.append("--cov-report=html")

    if args.test_file:
        test_args.append(args.test_file)
    elif args.test_dir:
        test_args.append(args.test_dir)

    # Run tests
    exit_code = run_tests(test_args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
