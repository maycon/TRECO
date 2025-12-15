"""
Preconnect connection strategy using httpx.

Establishes persistent HTTP/1.1 or HTTP/2 connections before the race
window, ensuring minimal latency during the actual attack.
"""

import threading
import logging
from typing import Dict, Optional

import httpx

from ..sync.base import SyncMechanism
from .base import ConnectionStrategy

logger = logging.getLogger("treco")


class PreconnectStrategy(ConnectionStrategy):
    """
    Pre-establish connections using httpx with HTTP/2 support.
    
    Each thread gets its own httpx.Client with a persistent connection.
    The connection is established during connect() phase, before the
    race synchronization point.
    
    Features:
        - HTTP/2 support (multiplexing, lower latency)
        - True persistent connections
        - Clean prepare/send separation
        - Proper TLS certificate verification control
    
    Example:
        strategy = PreconnectStrategy(sync=BarrierSync())
        strategy.prepare(num_threads, http_client)
        
        # In each thread:
        strategy.connect(thread_id)
        client = strategy.get_session(thread_id)
        request = client.build_request("POST", "/api", content=body)
        # ... wait at barrier ...
        response = client.send(request)
    """

    def __init__(self, sync: Optional[SyncMechanism] = None, http2: bool = False):
        """
        Initialize the preconnect strategy.
        
        Args:
            sync: Sync mechanism for coordinating connection establishment
            http2: Whether to use HTTP/2 (default: False for better race timing)
                   HTTP/1.1 creates separate connections per thread which
                   gives more reliable parallel request timing.
        """
        super().__init__(sync)
        self._clients: Dict[int, httpx.Client] = {}
        self._lock = threading.Lock()
        
        # Connection configuration (set in _prepare)
        self._base_url: str = ""
        self._host: str = ""
        self._port: int = 443
        self._verify_cert: bool = True
        self._use_http2: bool = http2
        self._timeout: float = 30.0
        self._follow_redirects: bool = False

    def _prepare(self, num_threads: int, http_client) -> None:
        """
        Store connection configuration from HTTP client.
        
        Args:
            num_threads: Number of threads that will connect
            http_client: HTTP client with configuration
        """
        config = http_client.config
        scheme = "https" if config.tls.enabled else "http"
        
        self._host = config.host
        self._port = config.port
        self._base_url = f"{scheme}://{config.host}:{config.port}"
        self._verify_cert = config.tls.verify_cert
        self._follow_redirects = config.http.follow_redirects
        
        # Clear any existing clients from previous runs
        self._cleanup_clients()
        
        logger.info(f"PreconnectStrategy (httpx) ready: {num_threads} threads")
        logger.debug(f"Target: {self._base_url} (HTTP/2: {self._use_http2}, verify: {self._verify_cert})")

    def _connect(self, thread_id: int) -> None:
        """
        Establish a persistent connection for this thread.
        
        Creates an httpx.Client and forces connection establishment
        by making a minimal request. The connection is kept alive for
        subsequent requests.
        
        Args:
            thread_id: ID of the connecting thread
            
        Raises:
            ConnectionError: If connection fails
        """
        logger.debug(f"[Thread {thread_id}] Connecting to {self._base_url}...")
        
        try:
            # Create httpx client with its own connection pool (no sharing)
            # Setting pool limits to 1 ensures this client uses exactly 1 connection
            limits = httpx.Limits(
                max_keepalive_connections=1,
                max_connections=1,
                keepalive_expiry=30.0
            )
            
            client = httpx.Client(
                http2=self._use_http2,
                verify=self._verify_cert,
                timeout=httpx.Timeout(self._timeout),
                base_url=self._base_url,
                follow_redirects=self._follow_redirects,
                limits=limits,
            )
            
            # Force TCP/TLS connection establishment
            # Use GET with stream=True to avoid downloading body
            # This is more compatible than HEAD (some servers return body on HEAD)
            try:
                with client.stream("GET", "/", headers={"Connection": "keep-alive"}) as response:
                    # Just establish connection, don't read body
                    pass
            except httpx.HTTPStatusError:
                # HTTP error is fine - connection is still established
                pass
            except httpx.RequestError as e:
                # Connection error - but socket might still be ready
                logger.debug(f"[Thread {thread_id}] Warmup request failed ({e}), connection may still be established")
            
            with self._lock:
                self._clients[thread_id] = client
            
            logger.debug(f"[Thread {thread_id}] Connected successfully")
            
        except Exception as e:
            logger.error(f"[Thread {thread_id}] Connection failed: {e}")
            raise ConnectionError(f"Thread {thread_id} failed to connect: {e}") from e

    def get_session(self, thread_id: int) -> httpx.Client:
        """
        Get the httpx client for a thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            httpx.Client with established connection
            
        Raises:
            KeyError: If connect() wasn't called for this thread
        """
        return self._clients[thread_id]

    def _cleanup_clients(self) -> None:
        """Close all existing clients."""
        with self._lock:
            for client in self._clients.values():
                try:
                    client.close()
                except Exception:
                    pass
            self._clients.clear()

    def cleanup(self) -> None:
        """Close all clients and release resources."""
        self._cleanup_clients()
        logger.debug("PreconnectStrategy cleaned up")