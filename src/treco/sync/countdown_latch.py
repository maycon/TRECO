"""
Countdown latch synchronization mechanism.

Threads wait until a counter reaches zero, then all are released.
"""

import threading

import logging

from typing import Optional
from .base import SyncMechanism

logger = logging.getLogger(__name__)


class CountdownLatchSync(SyncMechanism):
    """
    Countdown latch synchronization.

    How it works:
    1. Initialize counter to N
    2. Threads call wait() and block
    3. External thread(s) call release() to decrement counter
    4. When counter reaches 0, all waiting threads are released

    This is useful when you want external control over when threads start,
    or when you want to stagger the release based on external events.

    Example:
        sync = CountdownLatchSync()
        sync.prepare(20)

        # In worker threads:
        sync.wait(thread_id)  # Block here
        send_request()

        # In controller thread:
        for i in range(20):
            time.sleep(0.001)  # Small delay between releases
            sync.release()  # Decrement counter

    Visual:
        Thread 1: -----> [WAIT] ----------> [RELEASE] ----> send()
        Thread 2: -----> [WAIT] ----------> [RELEASE] ----> send()
        Thread 3: -----> [WAIT] ----------> [RELEASE] ----> send()

        Controller: release() release() ... release()
                    (count=19) (count=18)     (count=0) <-- triggers release

    Note:
        Unlike Barrier, this doesn't provide simultaneous release.
        Threads are released when the counter hits 0, which may not
        be as precise for race conditions.
    """

    def __init__(self):
        """Initialize countdown latch."""
        self.count = 0
        self.event: Optional[threading.Event] = None
        self.lock: threading.Lock = threading.Lock()

    def prepare(self, num_threads: int) -> None:
        """
        Initialize counter to N.

        Args:
            num_threads: Initial count value
        """
        self.count = num_threads
        self.event = threading.Event()
        logger.info(f"[CountdownLatchSync] Prepared latch with count={num_threads}")

    def wait(self, thread_id: int) -> None:
        """
        Block until counter reaches zero.

        Args:
            thread_id: Thread identifier (for logging)
        """
        if self.event is None:
            raise RuntimeError("Latch not prepared. Call prepare() first.")

        # Block until event is set (count reaches 0)
        self.event.wait()

    def release(self) -> None:
        """
        Decrement counter by 1.

        When counter reaches 0, all waiting threads are released.
        """

        if self.event is None:
            raise RuntimeError("Latch not prepared. Call prepare() first.")

        with self.lock:
            if self.count > 0:
                self.count -= 1

                if self.count == 0:
                    # Counter reached 0, release all threads
                    self.event.set()
                    logger.info("[CountdownLatchSync] Counter reached 0, releasing all threads")
