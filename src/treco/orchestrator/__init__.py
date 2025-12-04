"""
Main orchestrator for Treco framework.

The orchestrator coordinates all components and manages the complete
attack flow, including race condition attacks.
"""

from .coordinator import RaceCoordinator

__all__ = ["RaceCoordinator"]
