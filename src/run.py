#!/usr/bin/env python3
"""
Treco - Race Condition PoC Framework
Main execution script.

Usage:
    python run.py configs/attack.yaml --user alice --seed JBSWY3DPEHPK3PXP
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from treco.cli import main

if __name__ == "__main__":
    main()
