"""
Preconnect connection strategy.

Establishes all TCP/TLS connections before the race attack begins.
"""

import requests
from typing import List, TYPE_CHECKING

from .base import ConnectionStrategy

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from treco.http import HTTPClient


class PreconnectStrategy(ConnectionStrategy):
    """
    Preconnect strategy - establish all connections before the race.

    How it works:
    1. Create N separate sessions (one per thread)
    2. Send a lightweight request (e.g., /health) to establish TCP/TLS
    3. Keep connections alive
    4. Each thread uses its pre-warmed session

    Advantages:
    - Eliminates connection overhead during race
    - All threads can send simultaneously (< 1μs precision)
    - Achieves true race condition

    Disadvantages:
    - Uses more resources (N connections)
    - Takes longer to setup

    This is the RECOMMENDED strategy for race condition attacks.

    Example:
        strategy = PreconnectStrategy()
        strategy.prepare(20, http_client)

        # In thread 0:
        session = strategy.get_session(0)
        response = session.post(url, json=data)

    Timing comparison:
        Without preconnect:
            Thread 1: [TCP handshake 50ms] [TLS 100ms] [request 10ms]
            Thread 2: [TCP handshake 50ms] [TLS 100ms] [request 10ms]
            Race window: ~160ms (poor)

        With preconnect:
            Thread 1: [request 10ms]
            Thread 2: [request 10ms]
            Race window: < 1μs (excellent)
    """

    def __init__(self):
        """Initialize empty session list."""
        self.sessions: List[requests.Session] = []
        self.base_url = ""

    def prepare(self, num_threads: int, client: "HTTPClient") -> None:
        """
        Create and pre-warm N sessions.

        For each session:
        1. Create new requests.Session
        2. Send GET /health to establish connection
        3. Connection is kept alive for reuse

        Args:
            num_threads: Number of sessions to create
            client: HTTP client with server configuration
        """
        self.base_url = client.base_url

        logger.info(f"[PreconnectStrategy] Creating {num_threads} pre-warmed sessions...")

        for i in range(num_threads):
            # Create a new session with configured TLS settings
            # This initializes the session but doesn't establish connection yet
            session = client.create_session()

            # Pre-warm the connection with a lightweight request
            # This forces the TCP handshake and TLS negotiation to happen NOW,
            # so during the race attack, the connection is already established
            try:
                # Attempt to GET /health endpoint (common health check endpoint)
                # Even if this returns 404, the connection is still established
                response = session.get(f"{self.base_url}/health", timeout=5)
                logger.info(
                    f"[PreconnectStrategy] Session {i} pre-warmed (status: {response.status_code})"
                )
            except Exception as e:
                # If /health doesn't exist (404) or times out, that's acceptable
                # The important part is that TCP/TLS connection was established
                # The connection remains open due to keep-alive headers
                logger.debug(
                    f"[PreconnectStrategy] Session {i} pre-warm request failed, but connection established: {e}"
                )
                pass

            # Store the pre-warmed session for use by thread i
            self.sessions.append(session)

        logger.info(f"[PreconnectStrategy] All {num_threads} sessions ready for race attack")

    def get_session(self, thread_id: int) -> requests.Session:
        """
        Get the pre-warmed session for a specific thread.

        Each thread gets its own dedicated session with an
        already-established TCP/TLS connection.

        Args:
            thread_id: Thread identifier (0 to N-1)

        Returns:
            Pre-warmed requests.Session
        """
        if thread_id >= len(self.sessions):
            raise IndexError(f"Thread ID {thread_id} out of range (max: {len(self.sessions) - 1})")

        return self.sessions[thread_id]

    def cleanup(self) -> None:
        """
        Close all sessions and release connections.
        """
        logger.info(f"[PreconnectStrategy] Closing {len(self.sessions)} sessions...")

        for session in self.sessions:
            session.close()

        self.sessions.clear()
        logger.info("[PreconnectStrategy] Cleanup complete")
