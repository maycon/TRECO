"""
Connection strategies for race condition attacks.

This module provides different connection management strategies (Strategy Pattern)
for handling HTTP connections in multi-threaded race attacks.

Available strategies:
    - preconnect: Pre-establish individual connections per thread (httpx, HTTP/2)
    - multiplexed: Single HTTP/2 connection shared by all threads (tightest race window)
    - lazy: Connect on-demand when sending request
    - pooled: Use a shared connection pool
"""

from typing import Optional

from ..sync.base import SyncMechanism
from .base import ConnectionStrategy
from .preconnect import PreconnectStrategy
from .multiplexed import MultiplexedStrategy
from .lazy import LazyStrategy
from .pooled import PooledStrategy


# Factory for creating connection strategies
CONNECTION_STRATEGIES = {
    "preconnect": PreconnectStrategy,
    "multiplexed": MultiplexedStrategy,
    "lazy": LazyStrategy,
    "pooled": PooledStrategy,
}


def create_connection_strategy(
    strategy_type: str,
    sync: Optional[SyncMechanism] = None,
) -> ConnectionStrategy:
    """
    Factory function to create connection strategy by name.

    Args:
        strategy_type: Type of strategy ("preconnect", "multiplexed", "lazy", "pooled")
        sync: Optional sync mechanism for connection coordination

    Returns:
        Instance of ConnectionStrategy

    Raises:
        ValueError: If strategy_type is not recognized

    Example:
        # With sync mechanism
        conn_sync = create_sync_mechanism("barrier")
        strategy = create_connection_strategy("preconnect", sync=conn_sync)
        
        # Without sync (for lazy/pooled)
        strategy = create_connection_strategy("lazy")
        
        # HTTP/2 multiplexed (single connection)
        strategy = create_connection_strategy("multiplexed")
    """
    if strategy_type not in CONNECTION_STRATEGIES:
        raise ValueError(
            f"Unknown connection strategy: {strategy_type}. "
            f"Valid options: {list(CONNECTION_STRATEGIES.keys())}"
        )

    strategy_class = CONNECTION_STRATEGIES[strategy_type]
    return strategy_class(sync=sync)


__all__ = [
    "ConnectionStrategy",
    "PreconnectStrategy",
    "MultiplexedStrategy",
    "LazyStrategy",
    "PooledStrategy",
    "create_connection_strategy",
    "CONNECTION_STRATEGIES",
]