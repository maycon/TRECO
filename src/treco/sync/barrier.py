"""
Barrier synchronization mechanism.

All threads wait until N threads arrive, then all are released simultaneously.
"""

import threading

import logging

from .base import SyncMechanism

logger = logging.getLogger(__name__)



class BarrierSync(SyncMechanism):
    """
    Barrier synchronization using threading.Barrier.

    How it works:
    1. Create barrier for N threads
    2. Each thread calls wait()
    3. When Nth thread arrives, all threads are released simultaneously

    This is ideal for race condition attacks because it provides
    the most precise timing - all threads start at nearly the same instant.

    Race window achieved: < 1 microsecond

    Example:
        sync = BarrierSync()
        sync.prepare(20)  # Prepare for 20 threads

        # In each thread:
        sync.wait(thread_id)  # Block until all 20 arrive
        # ... threads released simultaneously ...
        send_request()  # All threads send at once

    Visual:
        Thread 1: -----> [WAIT] ----> [RELEASE] ----> send()
        Thread 2: -----> [WAIT] ----> [RELEASE] ----> send()
        Thread 3: -----> [WAIT] ----> [RELEASE] ----> send()
        ...
        Thread N: -----> [WAIT] ----> [RELEASE] ----> send()
                               ^
                               |
                    All threads synchronized here
    """

    def __init__(self):
        """Initialize empty barrier."""
        self.barrier = None

    def prepare(self, num_threads: int) -> None:
        """
        Create barrier for N threads.

        Args:
            num_threads: Number of threads that will participate
        """
        self.barrier = threading.Barrier(num_threads)
        logger.info(f"[BarrierSync] Prepared barrier for {num_threads} threads")

    def wait(self, thread_id: int) -> None:
        """
        Block until all threads arrive at barrier.

        This method blocks until exactly N threads have called wait().
        Once the Nth thread arrives, all threads are released simultaneously.

        Args:
            thread_id: Thread identifier (for logging)
        """
        if self.barrier is None:
            raise RuntimeError("Barrier not prepared. Call prepare() first.")

        # This blocks until all threads arrive
        self.barrier.wait()

        # All threads released simultaneously at this point

    def release(self) -> None:
        """
        No-op for barrier.

        Barriers automatically release when all threads arrive,
        so explicit release is not needed.
        """
        pass  # Barrier auto-releases when all threads arrive
