"""
Base interface for connection strategies.

Defines the contract that all connection strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests
    from treco.http import HTTPClient


class ConnectionStrategy(ABC):
    """
    Abstract base class for connection management strategies.

    Connection strategies control when and how HTTP connections are
    established for multi-threaded race attacks.

    All strategies must implement:
    - prepare(num_threads, client): Setup connections
    - get_session(thread_id): Get session for a thread
    - cleanup(): Release resources

    The choice of strategy significantly impacts race timing:
    - Preconnect: Best timing (< 1μs race window)
    - Lazy: Poor timing (> 100ms race window)
    - Pooled: Serialized (defeats race purpose)

    Example implementation:
        class MyStrategy(ConnectionStrategy):
            def prepare(self, num_threads, client):
                # Setup connections
                pass

            def get_session(self, thread_id):
                # Return session for thread
                return session

            def cleanup(self):
                # Clean up resources
                pass
    """

    @abstractmethod
    def prepare(self, num_threads: int, client: "HTTPClient") -> None:
        """
        Prepare connections for N threads.

        This method is called once before threads are created.
        Strategies can pre-establish connections, create pools,
        or do nothing (lazy initialization).

        Args:
            num_threads: Number of threads that will need connections
            client: HTTP client to use for creating sessions
        """
        pass

    @abstractmethod
    def get_session(self, thread_id: int) -> "requests.Session":
        """
        Get an HTTP session for a specific thread.

        This method is called by each thread to obtain a session
        for making HTTP requests.

        Args:
            thread_id: Unique identifier for the calling thread (0 to N-1)

        Returns:
            requests.Session object
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up resources and close connections.

        This method is called after all threads complete.
        It should close sessions, release resources, etc.
        """
        pass
