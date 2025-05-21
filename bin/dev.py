#!/usr/bin/env python3
"""
Development helper script for iffriendly.
Provides commands for common development tasks.
"""

import argparse
import os
import subprocess
import sys
from typing import List, Optional

def run_cmd(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, check=check)

def format_code() -> None:
    """Format code using black and isort."""
    print("Formatting code...")
    run_cmd(["black", "src", "tests"])
    run_cmd(["isort", "src", "tests"])

def run_tests(coverage: bool = True) -> None:
    """Run tests with optional coverage."""
    cmd = ["pytest"]
    if coverage:
        cmd.extend(["--cov=iffriendly", "--cov-report=term-missing"])
    run_cmd(cmd)

def type_check() -> None:
    """Run mypy type checking."""
    print("Running type checks...")
    run_cmd(["mypy", "src"])

def build_package() -> None:
    """Build the package."""
    print("Building package...")
    run_cmd(["python", "-m", "build"])

def clean() -> None:
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    artifacts = [
        "build",
        "dist",
        ".pytest_cache",
        ".coverage",
        "**/__pycache__",
        "**/*.pyc",
    ]
    for pattern in artifacts:
        run_cmd(["rm", "-rf", pattern], check=False)

def main() -> None:
    parser = argparse.ArgumentParser(description="iffriendly development helper")
    parser.add_argument("command", choices=[
        "format",
        "test",
        "typecheck",
        "build",
        "clean",
        "all"
    ])
    parser.add_argument("--no-coverage", action="store_true",
                      help="Disable coverage reporting in tests")

    args = parser.parse_args()

    if args.command == "format":
        format_code()
    elif args.command == "test":
        run_tests(not args.no_coverage)
    elif args.command == "typecheck":
        type_check()
    elif args.command == "build":
        build_package()
    elif args.command == "clean":
        clean()
    elif args.command == "all":
        format_code()
        type_check()
        run_tests(not args.no_coverage)
        build_package()

if __name__ == "__main__":
    main() 