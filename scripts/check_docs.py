#!/usr/bin/env python3
"""
Documentation validation script for TRECO.

This script checks if documentation needs updating when source code changes.
Can be used as a pre-commit hook or run manually.

Usage:
    # From repository root
    python scripts/check_docs.py
    
    # From any directory (script auto-detects repo root)
    cd /path/to/treco/subdirectory
    python scripts/check_docs.py
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

# Colors for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def find_repo_root() -> Path:
    """Find the repository root by looking for pyproject.toml."""
    current = Path.cwd()
    
    # Try current directory and parents
    for parent in [current] + list(current.parents):
        if (parent / 'pyproject.toml').exists():
            return parent
    
    # If not found, assume current directory
    print_warning("Could not find repository root. Assuming current directory.")
    return current

def print_header(msg: str):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{msg}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def print_success(msg: str):
    print(f"{GREEN}✓{RESET} {msg}")

def print_warning(msg: str):
    print(f"{YELLOW}⚠{RESET} {msg}")

def print_error(msg: str):
    print(f"{RED}✗{RESET} {msg}")

def check_version_consistency(repo_root: Path) -> Tuple[bool, List[str]]:
    """Check if version is consistent across files."""
    issues = []
    
    # Get version from pyproject.toml
    pyproject_path = repo_root / 'pyproject.toml'
    if not pyproject_path.exists():
        return False, ["pyproject.toml not found"]
    
    with open(pyproject_path) as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if not match:
            return False, ["Could not find version in pyproject.toml"]
        pyproject_version = match.group(1)
    
    # Get version from __init__.py
    init_path = repo_root / 'src' / 'treco' / '__init__.py'
    if not init_path.exists():
        return False, ["src/treco/__init__.py not found"]
    
    with open(init_path) as f:
        content = f.read()
        match = re.search(r'__version__ = "([^"]+)"', content)
        if not match:
            return False, ["Could not find __version__ in __init__.py"]
        init_version = match.group(1)
    
    # Compare versions
    if pyproject_version != init_version:
        issues.append(f"Version mismatch: pyproject.toml={pyproject_version}, __init__.py={init_version}")
        return False, issues
    
    return True, []

def main():
    """Run all documentation checks."""
    print_header("TRECO Documentation Validation")
    
    # Find repository root
    repo_root = find_repo_root()
    print(f"Repository root: {repo_root}\n")
    
    # Change to repository root
    os.chdir(repo_root)
    
    all_passed = True
    
    # Check version consistency
    print_header("1. Version Consistency")
    passed, issues = check_version_consistency(repo_root)
    if passed:
        print_success("Version is consistent across files")
    else:
        all_passed = False
        for issue in issues:
            print_error(issue)
    
    # Summary
    print_header("Summary")
    if all_passed:
        print_success("All documentation checks passed!")
        return 0
    else:
        print_error("Some documentation checks failed")
        print(f"\n{YELLOW}See docs/CONTRIBUTING.md for guidelines.{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
