"""
Orchestration module for TRECO framework.

Provides the main coordinator and supporting executors for
running race condition attacks.

Components:
    - RaceCoordinator: Main entry point for attack execution
    - RaceExecutor: Handles multi-threaded race attacks
    - ResultAnalyzer: Analyzes race results and timing
    - ParallelExecutor: Handles parallel thread propagation
"""

from .coordinator import RaceCoordinator
from .race_executor import RaceExecutor, RaceResult
from .result_analyzer import ResultAnalyzer
from .parallel_executor import ParallelExecutor

__all__ = [
    "RaceCoordinator",
    "RaceExecutor",
    "RaceResult",
    "ResultAnalyzer",
    "ParallelExecutor",
]