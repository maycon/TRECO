"""
Connection strategies for race condition attacks.

This module provides different connection management strategies (Strategy Pattern)
for handling HTTP connections in multi-threaded race attacks.
"""

from .base import ConnectionStrategy
from .preconnect import PreconnectStrategy
from .lazy import LazyStrategy
from .pooled import PooledStrategy


# Factory for creating connection strategies
CONNECTION_STRATEGIES = {
    "preconnect": PreconnectStrategy,
    "lazy": LazyStrategy,
    "pooled": PooledStrategy,
}


def create_connection_strategy(strategy_type: str) -> ConnectionStrategy:
    """
    Factory function to create connection strategy by name.

    Args:
        strategy_type: Type of strategy ("preconnect", "lazy", "pooled")

    Returns:
        Instance of ConnectionStrategy

    Raises:
        ValueError: If strategy_type is not recognized

    Example:
        strategy = create_connection_strategy("preconnect")
        strategy.prepare(20, http_client)
    """
    if strategy_type not in CONNECTION_STRATEGIES:
        raise ValueError(
            f"Unknown connection strategy: {strategy_type}. "
            f"Valid options: {list(CONNECTION_STRATEGIES.keys())}"
        )

    strategy_class = CONNECTION_STRATEGIES[strategy_type]
    return strategy_class()


__all__ = [
    "ConnectionStrategy",
    "PreconnectStrategy",
    "LazyStrategy",
    "PooledStrategy",
    "create_connection_strategy",
    "CONNECTION_STRATEGIES",
]
