"""
Module entry point for running Treco as a module.

Usage:
    python -m treco configs/attack.yaml --user alice
"""

from .cli import main

if __name__ == "__main__":
    main()
