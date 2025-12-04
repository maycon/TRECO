"""
Lazy connection strategy.

Creates connections on-demand when threads need them.
"""

import requests
from typing import TYPE_CHECKING

from .base import ConnectionStrategy

import logging

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from treco.http import HTTPClient


class LazyStrategy(ConnectionStrategy):
    """
    Lazy strategy - create connections on demand.

    How it works:
    1. No setup during prepare()
    2. Each thread creates its own session when needed
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
        session = strategy.get_session(thread_id)  # Creates new session
        response = session.post(url, json=data)  # Establishes connection here

    Timing comparison:
        Lazy strategy:
            Thread 1: [barrier] -> [TCP 50ms] [TLS 100ms] [request 10ms]
            Thread 2: [barrier] -> [TCP 50ms] [TLS 100ms] [request 10ms]
            Thread 3: [barrier] -> [TCP 50ms] [TLS 100ms] [request 10ms]

            Race window: ~300ms (very poor)
            Threads don't actually send simultaneously!

        Preconnect strategy:
            Thread 1: [barrier] -> [request 10ms]
            Thread 2: [barrier] -> [request 10ms]
            Thread 3: [barrier] -> [request 10ms]

            Race window: < 1μs (excellent)
    """

    def __init__(self):
        """Initialize lazy strategy."""
        self.client = None

    def prepare(self, num_threads: int, client: "HTTPClient") -> None:
        """
        Store client reference for later use.

        No actual connection setup is performed.

        Args:
            num_threads: Number of threads (not used in lazy mode)
            client: HTTP client for creating sessions
        """
        self.client = client
        logger.info(f"[LazyStrategy] Prepared for {num_threads} threads (lazy mode)")
        logger.warning(
            "[LazyStrategy] WARNING: Lazy connections are NOT recommended for race attacks!"
        )
        logger.info("[LazyStrategy] Each thread will establish connection on first request")

    def get_session(self, thread_id: int) -> requests.Session:
        """
        Create a new session on demand.

        Each call creates a brand new session with no pre-existing connection.
        The TCP/TLS handshake will occur on the first request.

        Args:
            thread_id: Thread identifier (not used, for interface compatibility)

        Returns:
            New requests.Session
        """
        # Create fresh session
        return self.client.create_session()  # type: ignore

    def cleanup(self) -> None:
        """
        No cleanup needed.

        Sessions are created by threads and should be closed by them.
        """
        logger.info("[LazyStrategy] No cleanup needed (sessions managed by threads)")
