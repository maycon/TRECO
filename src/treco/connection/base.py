"""
Base interface for connection strategies.

Defines the contract that all connection strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from treco.http import HTTPClient
    from treco.sync.base import SyncMechanism


class ConnectionStrategy(ABC):
    """
    Abstract base class for connection management strategies.

    Connection strategies control when and how HTTP connections are
    established for multi-threaded race attacks.
    
    Lifecycle:
        1. __init__(sync): Create strategy with optional sync mechanism
        2. prepare(num_threads, client): Setup configuration (main thread)
        3. connect(thread_id): Establish connection (each worker thread)
        4. get_session(thread_id): Get session for requests
        5. cleanup(): Release resources (main thread)

    The choice of strategy significantly impacts race timing:
        - preconnect: Individual HTTP/2 connections per thread (< 10ms window)
        - multiplexed: Single HTTP/2 connection shared (< 1ms window)
        - lazy: Connect on-demand (> 100ms window, not recommended)
        - pooled: Shared pool (serialized, defeats race purpose)

    Example implementation:
        class MyStrategy(ConnectionStrategy):
            def __init__(self, sync=None):
                super().__init__(sync)
                self._sessions = {}
            
            def _prepare(self, num_threads, client):
                # Store configuration
                pass

            def _connect(self, thread_id):
                # Establish connection for this thread
                pass

            def get_session(self, thread_id):
                return self._sessions[thread_id]

            def cleanup(self):
                # Clean up resources
                pass
    """

    def __init__(self, sync: Optional["SyncMechanism"] = None):
        """
        Initialize the connection strategy.
        
        Args:
            sync: Optional sync mechanism for coordinating connection
                  establishment across threads. If provided, connect()
                  will wait for all threads after establishing connection.
        """
        self._sync = sync
        self._num_threads: int = 0

    @property
    def sync(self) -> Optional["SyncMechanism"]:
        """Get the sync mechanism used for connection coordination."""
        return self._sync

    @sync.setter
    def sync(self, value: "SyncMechanism") -> None:
        """Set the sync mechanism for connection coordination."""
        self._sync = value

    def prepare(self, num_threads: int, http_client: "HTTPClient") -> None:
        """
        Prepare the strategy for the given number of threads.
        
        Called once from the main thread before worker threads are spawned.
        This method handles sync mechanism preparation and delegates to
        subclass-specific _prepare() method.

        Args:
            num_threads: Number of threads that will need connections
            http_client: HTTP client with configuration
        """
        self._num_threads = num_threads
        
        # Prepare sync mechanism if provided
        if self._sync:
            self._sync.prepare(num_threads)
        
        # Call subclass-specific preparation
        self._prepare(num_threads, http_client)

    @abstractmethod
    def _prepare(self, num_threads: int, http_client: "HTTPClient") -> None:
        """
        Subclass-specific preparation logic.
        
        Override this instead of prepare() to ensure sync is prepared.

        Args:
            num_threads: Number of threads that will need connections
            http_client: HTTP client with configuration
        """
        pass

    def connect(self, thread_id: int) -> None:
        """
        Establish connection for a specific thread.
        
        Called from WITHIN each worker thread, BEFORE the race sync point.
        This method:
            1. Calls subclass _connect() to establish connection
            2. Waits at sync barrier (if sync mechanism is configured)
        
        Args:
            thread_id: ID of the calling thread
            
        Raises:
            ConnectionError: If connection establishment fails
        """
        # Establish connection (subclass implementation)
        self._connect(thread_id)
        
        # Wait for all threads to connect (if sync is configured)
        if self._sync:
            self._sync.wait(thread_id)

    def _connect(self, thread_id: int) -> None:
        """
        Subclass-specific connection logic.
        
        Override this to implement actual connection establishment.
        Default does nothing (for strategies that don't pre-connect).
        
        Args:
            thread_id: ID of the calling thread
        """
        pass

    @abstractmethod
    def get_session(self, thread_id: int) -> Any:
        """
        Get the HTTP client/session for a specific thread.

        This method is called by each thread to obtain a client
        for making HTTP requests.

        Args:
            thread_id: Unique identifier for the calling thread (0 to N-1)

        Returns:
            HTTP client object (httpx.Client or similar)
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