"""
Base interface for synchronization mechanisms.

Defines the contract that all sync mechanisms must implement.
"""

from abc import ABC, abstractmethod


class SyncMechanism(ABC):
    """
    Abstract base class for synchronization mechanisms.

    All sync mechanisms must implement:
    - prepare(num_threads): Initialize for N threads
    - wait(thread_id): Block thread until ready
    - release(): Release waiting threads (if applicable)

    Sync mechanisms are used to coordinate multiple threads in race
    condition attacks, ensuring they send requests simultaneously.

    Example implementation:
        class MySync(SyncMechanism):
            def prepare(self, num_threads):
                self.num_threads = num_threads

            def wait(self, thread_id):
                # Block until all threads ready
                pass

            def release(self):
                # Release all threads
                pass
    """

    @abstractmethod
    def prepare(self, num_threads: int) -> None:
        """
        Prepare the synchronization mechanism for N threads.

        This method is called once before threads are created,
        allowing the mechanism to initialize its internal state.

        Args:
            num_threads: Number of threads that will participate
        """
        pass

    @abstractmethod
    def wait(self, thread_id: int) -> None:
        """
        Block the calling thread until synchronization point is reached.

        This method is called by each thread. The behavior depends on
        the specific synchronization strategy:
        - Barrier: Blocks until all N threads arrive
        - Semaphore: Blocks if limit is reached
        - Countdown Latch: Blocks until counter reaches 0

        Args:
            thread_id: Unique identifier for the calling thread (0 to N-1)
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """
        Release waiting threads (if applicable).

        Some mechanisms (like CountdownLatch) require explicit release
        from an external thread. Others (like Barrier) auto-release when
        all threads arrive.

        This method should be idempotent (safe to call multiple times).
        """
        pass
