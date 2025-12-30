"""
Treco - Race Condition PoC Framework

A powerful and flexible framework for executing Proof-of-Concept (PoC)
race condition attacks against web APIs.

Main components:
- models: Data structures for configuration and context
- parser: YAML loading and validation
- template: Jinja2 engine with custom filters
- state: State machine and executor
- http: HTTP client and parsers
- sync: Synchronization mechanisms
- connection: Connection strategies
- orchestrator: Main coordinator

Example:
    from treco import RaceCoordinator

    coordinator = RaceCoordinator(
        "configs/attack.yaml",
        cli_args={"user": "alice", "threads": 20}
    )

    results = coordinator.run()
"""


__version__ = "1.8.0"
__author__ = "Hack N' Roll Security Team"

from .orchestrator import RaceCoordinator
from .logging import setup_logging, get_logger, user_output

__all__ = [
    "RaceCoordinator",
    "setup_logging",
    "get_logger",
    "user_output",
]
