"""
Multiplexed connection strategy using HTTP/2.

Uses a single HTTP/2 connection shared by all threads, leveraging
HTTP/2 multiplexing for maximum race window precision.
"""

import logging
from typing import Optional

import httpx

from .base import ConnectionStrategy
from ..sync.base import SyncMechanism

logger = logging.getLogger("treco")


class MultiplexedStrategy(ConnectionStrategy):
    """
    Single HTTP/2 connection shared by all threads.
    
    HTTP/2 allows multiple concurrent streams over a single TCP connection.
    This strategy leverages that to achieve the tightest possible race window,
    as all requests go through the same socket.
    
    Benefits:
        - Single TCP/TLS handshake (faster setup)
        - All requests share the same connection
        - HTTP/2 multiplexing for true parallelism
        - Minimal race window (< 1ms typically)
    
    Limitations:
        - Requires HTTP/2 support on the server
        - Falls back to HTTP/1.1 if server doesn't support HTTP/2
        - Single connection = single point of failure
    
    Example:
        strategy = MultiplexedStrategy()
        strategy.prepare(num_threads, http_client)
        
        # In each thread:
        client = strategy.get_session(thread_id)  # Same client for all
        request = client.build_request("POST", "/api", content=body)
        # ... wait at barrier ...
        response = client.send(request)
    """

    def __init__(
        self, 
        sync: Optional[SyncMechanism] = None, 
        bypass_proxy: bool = False,
    ):
        """
        Initialize the multiplexed strategy.
        
        Args:
            sync: Sync mechanism (optional, mainly for API consistency)
            bypass_proxy: Whether to bypass proxy for this strategy
        """
        # Always use HTTP/2 for multiplexed strategy
        super().__init__(sync=sync, bypass_proxy=bypass_proxy, http2=True)
        self._client: Optional[httpx.Client] = None

    def _prepare(self, num_threads: int, http_client) -> None:
        """
        Create the shared HTTP/2 client and establish connection.
        
        Args:
            num_threads: Number of threads (for logging only)
            http_client: HTTP client with configuration
        """
        # Close existing client if any
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        
        # Create single shared HTTP/2 client (no per-connection limits)
        kwargs = self._build_client_kwargs(limits=None)
        self._client = httpx.Client(**kwargs)
        
        # Warm up connection
        self._warmup_connection(self._client)
        
        logger.info(f"MultiplexedStrategy ready: 1 HTTP/2 connection for {num_threads} threads")
        logger.debug(f"Target: {self._base_url} (verify: {self._verify_cert})")

    def _connect(self, thread_id: int) -> None:
        """
        No-op for multiplexed strategy.
        
        Connection is already established in _prepare(). Individual threads
        don't need to establish their own connections.
        
        Args:
            thread_id: Thread ID (unused)
        """
        logger.debug(f"[Thread {thread_id}] Using shared HTTP/2 connection")

    def get_session(self, thread_id: int) -> httpx.Client:
        """
        Get the shared httpx client.
        
        All threads receive the same client instance, which handles
        multiplexing internally.
        
        Args:
            thread_id: Thread ID (unused, all get same client)
            
        Returns:
            Shared httpx.Client with HTTP/2 connection
            
        Raises:
            RuntimeError: If prepare() wasn't called
        """
        if not self._client:
            raise RuntimeError("MultiplexedStrategy.prepare() must be called before get_session()")
        return self._client

    def cleanup(self) -> None:
        """Close the shared client."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
        logger.debug("MultiplexedStrategy cleaned up")