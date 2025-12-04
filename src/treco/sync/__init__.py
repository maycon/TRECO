"""
Synchronization mechanisms for race condition attacks.

This module provides different synchronization strategies (Strategy Pattern)
for coordinating concurrent threads in race attacks.
"""

from .base import SyncMechanism
from .barrier import BarrierSync
from .countdown_latch import CountdownLatchSync
from .semaphore import SemaphoreSync


# Factory for creating sync mechanisms
SYNC_MECHANISMS = {
    "barrier": BarrierSync,
    "countdown_latch": CountdownLatchSync,
    "semaphore": SemaphoreSync,
}


def create_sync_mechanism(mechanism_type: str) -> SyncMechanism:
    """
    Factory function to create sync mechanism by name.

    Args:
        mechanism_type: Type of sync mechanism ("barrier", "countdown_latch", "semaphore")

    Returns:
        Instance of SyncMechanism

    Raises:
        ValueError: If mechanism_type is not recognized

    Example:
        sync = create_sync_mechanism("barrier")
        sync.prepare(20)
    """
    if mechanism_type not in SYNC_MECHANISMS:
        raise ValueError(
            f"Unknown sync mechanism: {mechanism_type}. "
            f"Valid options: {list(SYNC_MECHANISMS.keys())}"
        )

    mechanism_class = SYNC_MECHANISMS[mechanism_type]
    return mechanism_class()


__all__ = [
    "SyncMechanism",
    "BarrierSync",
    "CountdownLatchSync",
    "SemaphoreSync",
    "create_sync_mechanism",
    "SYNC_MECHANISMS",
]
