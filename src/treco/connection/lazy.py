"""
Lazy connection strategy.

Creates connections on-demand when threads need them.
NOT recommended for race condition attacks.
"""

import logging
from typing import TYPE_CHECKING, Optional

import httpx

from ..sync.base import SyncMechanism
from .base import ConnectionStrategy

logger = logging.getLogger("treco")

if TYPE_CHECKING:
    from treco.http import HTTPClient


class LazyStrategy(ConnectionStrategy):
    """
    Lazy strategy - create connections on demand.

    How it works:
        1. No setup during prepare()
        2. Each thread creates its own client when get_session() is called
        3. Connection established on first request

    Advantages:
        - Minimal setup time
        - Lower resource usage initially

    Disadvantages:
        - Poor timing for race conditions (> 100ms race window)
        - Each thread incurs TCP/TLS handshake overhead
        - NOT RECOMMENDED for race attacks

    Use cases:
        - Load testing (not race conditions)
        - Scenarios where connection timing doesn't matter
        - Testing connection establishment overhead

    Example:
        strategy = LazyStrategy()
        strategy.prepare(20, http_client)

        # In thread:
        client = strategy.get_session(thread_id)
        response = client.post(url, content=data)  # Connection happens HERE
    """

    def __init__(self, sync: Optional[SyncMechanism] = None):
        """
        Initialize lazy strategy.
        
        Args:
            sync: Sync mechanism (usually not needed for lazy strategy)
        """
        super().__init__(sync)
        self._base_url: str = ""
        self._verify_cert: bool = True
        self._follow_redirects: bool = False
        self._timeout: float = 30.0

    def _prepare(self, num_threads: int, http_client: "HTTPClient") -> None:
        """
        Store configuration for later use.

        No actual connection setup is performed.

        Args:
            num_threads: Number of threads (for logging only)
            http_client: HTTP client with configuration
        """
        config = http_client.config
        scheme = "https" if config.tls.enabled else "http"
        
        self._base_url = f"{scheme}://{config.host}:{config.port}"
        self._verify_cert = config.tls.verify_cert
        self._follow_redirects = config.http.follow_redirects
        
        logger.info(f"LazyStrategy prepared for {num_threads} threads")
        logger.warning("LazyStrategy: NOT recommended for race attacks!")
        logger.warning("Each thread will establish connection on first request")

    def _connect(self, thread_id: int) -> None:
        """
        No-op for lazy strategy.
        
        Connection happens on first request, not during connect phase.
        
        Args:
            thread_id: Thread ID (unused)
        """
        logger.debug(f"[Thread {thread_id}] LazyStrategy - connection deferred to first request")

    def get_session(self, thread_id: int) -> httpx.Client:
        """
        Create a new httpx client on demand.

        Each call creates a brand new client with no pre-existing connection.
        The TCP/TLS handshake will occur on the first request.

        Args:
            thread_id: Thread identifier (for logging)

        Returns:
            New httpx.Client
        """
        logger.debug(f"[Thread {thread_id}] Creating new httpx.Client (lazy)")
        
        return httpx.Client(
            http2=True,
            verify=self._verify_cert,
            timeout=httpx.Timeout(self._timeout),
            base_url=self._base_url,
            follow_redirects=self._follow_redirects,
        )

    def cleanup(self) -> None:
        """
        No cleanup needed.

        Clients are created by threads and should be closed by them.
        """
        logger.debug("LazyStrategy cleanup (nothing to do)")