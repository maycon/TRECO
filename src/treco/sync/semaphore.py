"""
Semaphore synchronization mechanism.

Limits the number of concurrent threads to N.
"""

import threading

import logging

from .base import SyncMechanism

logger = logging.getLogger(__name__)



class SemaphoreSync(SyncMechanism):
    """
    Semaphore synchronization using threading.Semaphore.

    How it works:
    1. Create semaphore with limit N
    2. Each thread acquires semaphore before critical section
    3. At most N threads can be in critical section simultaneously
    4. Threads release semaphore after completing

    Note: This is NOT ideal for race condition attacks!

    Unlike Barrier, semaphore doesn't synchronize threads to start
    simultaneously. Instead, it limits concurrent execution, which
    actually serializes requests and defeats the purpose of a race attack.

    Use case:
        - Rate limiting: Limit concurrent API calls to avoid overload
        - Resource management: Limit access to shared resources
        - NOT for race conditions!

    Example:
        sync = SemaphoreSync()
        sync.prepare(5)  # Allow max 5 concurrent threads

        # In worker thread:
        sync.wait(thread_id)  # Acquire (blocks if 5 already running)
        send_request()
        sync.release()  # Release slot for next thread

    Visual:
        Time  -->

        Slot 1: [T1]----[T6]----[T11]
        Slot 2: [T2]----[T7]----[T12]
        Slot 3: [T3]----[T8]----[T13]
        Slot 4: [T4]----[T9]----[T14]
        Slot 5: [T5]----[T10]---[T15]

        Only 5 threads run concurrently, others wait in queue.
        This serializes execution, not good for race attacks!
    """

    def __init__(self):
        """Initialize semaphore."""
        self.semaphore = None

    def prepare(self, num_threads: int) -> None:
        """
        Create semaphore with limit N.

        Args:
            num_threads: Maximum number of concurrent threads
        """
        self.semaphore = threading.Semaphore(num_threads)
        logger.info(f"[SemaphoreSync] Prepared semaphore with limit={num_threads}")
        logger.info("[SemaphoreSync] WARNING: Semaphore is not ideal for race conditions!")

    def wait(self, thread_id: int) -> None:
        """
        Acquire semaphore slot.

        Blocks if maximum concurrent threads already running.

        Args:
            thread_id: Thread identifier (for logging)
        """
        if self.semaphore is None:
            raise RuntimeError("Semaphore not prepared. Call prepare() first.")

        # Acquire slot (blocks if limit reached)
        self.semaphore.acquire()

    def release(self) -> None:
        """
        Release semaphore slot.

        This should be called after each thread completes its work
        to free up a slot for waiting threads.
        """
        if self.semaphore is not None:
            self.semaphore.release()
