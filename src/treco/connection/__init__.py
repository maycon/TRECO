"""
Connection strategies for race condition attacks.

This module provides different strategies for establishing and managing
HTTP connections in multi-threaded race attacks.

Strategies:
    - PreconnectStrategy: Pre-establish individual connections per thread
    - MultiplexedStrategy: Single HTTP/2 connection shared by all threads
    - LazyStrategy: Connect on-demand (NOT recommended for races)
    - PooledStrategy: Shared connection pool (NOT recommended for races)

Example:
    from treco.connection import create_connection_strategy
    from treco.sync import create_sync_mechanism
    
    sync = create_sync_mechanism("barrier")
    strategy = create_connection_strategy("preconnect", sync=sync)
    
    strategy.prepare(20, http_client)
    
    # In each thread:
    strategy.connect(thread_id)
    client = strategy.get_session(thread_id)
    response = client.send(request)
"""

from typing import Optional

from .base import ConnectionStrategy
from .preconnect import PreconnectStrategy
from .multiplexed import MultiplexedStrategy
from .lazy import LazyStrategy
from .pooled import PooledStrategy
from ..sync.base import SyncMechanism


# Registry of available strategies
CONNECTION_STRATEGIES = {
    "preconnect": PreconnectStrategy,
    "multiplexed": MultiplexedStrategy,
    "lazy": LazyStrategy,
    "pooled": PooledStrategy,
}


def create_connection_strategy(
    strategy_type: str,
    sync: Optional[SyncMechanism] = None,
    bypass_proxy: bool = False,
) -> ConnectionStrategy:
    """
    Factory function to create connection strategy by name.

    Args:
        strategy_type: Type of strategy ("preconnect", "multiplexed", "lazy", "pooled")
        sync: Optional sync mechanism for connection coordination
        bypass_proxy: Whether to bypass proxy for this strategy

    Returns:
        Instance of ConnectionStrategy

    Raises:
        ValueError: If strategy_type is not recognized

    Example:
        # Pre-established connections (recommended for races)
        strategy = create_connection_strategy("preconnect", sync=barrier)
        
        # HTTP/2 multiplexed (single connection)
        strategy = create_connection_strategy("multiplexed")
        
        # Bypass proxy for race attack
        strategy = create_connection_strategy("preconnect", bypass_proxy=True)
    """
    if strategy_type not in CONNECTION_STRATEGIES:
        raise ValueError(
            f"Unknown connection strategy: {strategy_type}. "
            f"Available: {list(CONNECTION_STRATEGIES.keys())}"
        )

    strategy_class = CONNECTION_STRATEGIES[strategy_type]
    
    # All strategies now accept bypass_proxy in base class
    return strategy_class(sync=sync, bypass_proxy=bypass_proxy)


__all__ = [
    "ConnectionStrategy",
    "PreconnectStrategy",
    "MultiplexedStrategy",
    "LazyStrategy",
    "PooledStrategy",
    "create_connection_strategy",
    "CONNECTION_STRATEGIES",
]
