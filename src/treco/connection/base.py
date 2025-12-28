"""
Base interface for connection strategies.

Defines the contract that all connection strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

import httpx

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

    def __init__(
        self, 
        sync: Optional["SyncMechanism"] = None,
        bypass_proxy: bool = False,
        http2: bool = False,
        timeout: float = 30.0,
    ):
        """
        Initialize the connection strategy.
        
        Args:
            sync: Optional sync mechanism for coordinating connection
                  establishment across threads. If provided, connect()
                  will wait for all threads after establishing connection.
            bypass_proxy: Whether to bypass proxy for this strategy.
            http2: Whether to use HTTP/2.
            timeout: Request timeout in seconds.
        """
        self._sync = sync
        self._num_threads: int = 0
        self._bypass_proxy = bypass_proxy
        self._http2 = http2
        self._timeout = timeout
        
        # Configuration set in prepare()
        self._base_url: str = ""
        self._verify_cert: bool = True
        self._follow_redirects: bool = False
        self._proxy = None
        self._http_client: Optional["HTTPClient"] = None

    @property
    def sync(self) -> Optional["SyncMechanism"]:
        """Get the sync mechanism used for connection coordination."""
        return self._sync

    @sync.setter
    def sync(self, value: "SyncMechanism") -> None:
        """Set the sync mechanism for connection coordination."""
        self._sync = value

    def _build_client_kwargs(self, limits: Optional[httpx.Limits] = None) -> Dict[str, Any]:
        """
        Build common kwargs for httpx.Client construction.
        
        Centralizes the configuration logic shared across all strategies:
        proxy handling, mTLS certificates, timeouts, etc.
        
        Args:
            limits: Optional connection limits. If None, uses default limits.
            
        Returns:
            Dictionary of kwargs ready for httpx.Client()
        """
        # Default limits if not specified
        if limits is None:
            limits = httpx.Limits(
                max_keepalive_connections=1,
                max_connections=1,
                keepalive_expiry=30.0,
            )
        
        # Handle proxy bypass
        proxy_url = None
        if not self._bypass_proxy and self._proxy:
            proxy_url = self._proxy.to_client_proxy()
        
        # Get mTLS certificate if configured
        cert = None
        if self._http_client:
            cert = self._http_client._get_client_cert()
        
        return {
            "http2": self._http2,
            "verify": self._verify_cert,
            "timeout": httpx.Timeout(self._timeout),
            "base_url": self._base_url,
            "follow_redirects": self._follow_redirects,
            "limits": limits,
            "proxy": proxy_url,
            "cert": cert,
        }

    def _store_client_config(self, http_client: "HTTPClient") -> None:
        """
        Store common configuration from HTTP client.
        
        Args:
            http_client: HTTP client with configuration
        """
        config = http_client.config
        scheme = "https" if config.tls.enabled else "http"
        
        self._base_url = f"{scheme}://{config.host}:{config.port}"
        self._verify_cert = config.tls.verify_cert
        self._follow_redirects = config.http.follow_redirects
        self._proxy = config.proxy
        self._http_client = http_client

    def _warmup_connection(self, client: httpx.Client) -> None:
        """
        Establish TCP/TLS connection with a warmup request.
        
        Args:
            client: httpx.Client to warm up
        """
        try:
            with client.stream("GET", "/", headers={"Connection": "keep-alive"}) as _:
                pass
        except httpx.HTTPStatusError:
            # HTTP error is fine - connection is established
            pass
        except httpx.RequestError:
            # Connection error - but socket might still be ready
            pass

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
        
        # Store common configuration
        self._store_client_config(http_client)
        
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