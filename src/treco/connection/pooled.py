"""
Pooled connection strategy.

Shares a pool of connections among threads.
"""

import requests
import queue
from typing import TYPE_CHECKING

import logging

logger = logging.getLogger(__name__)

from .base import ConnectionStrategy

if TYPE_CHECKING:
    from treco.http import HTTPClient


class PooledStrategy(ConnectionStrategy):
    """
    Pooled strategy - share a pool of M connections among N threads.

    How it works:
    1. Create a pool of M sessions (M < N typically)
    2. Threads request sessions from the pool
    3. If pool is empty, thread blocks until a session is returned
    4. After use, thread returns session to pool

    Advantages:
    - Limits total number of connections
    - Good for resource-constrained scenarios

    Disadvantages:
    - Serializes requests (threads wait for sessions)
    - Defeats the purpose of race conditions!
    - NOT RECOMMENDED for race attacks

    Use cases:
    - Load testing with connection limits
    - Simulating connection pools in production
    - NOT for race condition exploits

    Example:
        strategy = PooledStrategy()
        strategy.prepare(20, http_client)  # 20 threads, but only 5 connections

        # In thread:
        session = strategy.get_session(thread_id)  # May block waiting for session
        response = session.post(url, json=data)
        # Session automatically returned to pool after use

    Why this doesn't work for race conditions:
        Time ->

        Pool (5 sessions):
        [S1] [S2] [S3] [S4] [S5]

        20 threads compete for 5 sessions:
        T1,T2,T3,T4,T5 -> Get sessions, send requests
        T6,T7,T8,T9,T10 -> WAIT for sessions
        T11...T20 -> WAIT even longer

        Result: Requests are serialized in groups of 5
        Not a race condition, just slow sequential requests!
    """

    def __init__(self):
        """Initialize pool."""
        self.pool: queue.Queue = queue.Queue()
        self.pool_size = 0

    def prepare(self, num_threads: int, client: "HTTPClient") -> None:
        """
        Create a pool of M sessions.

        By default, creates min(num_threads, 5) sessions.
        This limits concurrent connections.

        Args:
            num_threads: Number of threads (pool will be smaller)
            client: HTTP client for creating sessions
        """
        # Create a smaller pool than number of threads
        self.pool_size = min(num_threads, 5)

        logger.info(f"[PooledStrategy] Creating connection pool with {self.pool_size} sessions")
        logger.info(f"[PooledStrategy] {num_threads} threads will share these connections")
        logger.warning("[PooledStrategy] WARNING: Pooled connections serialize requests!")
        logger.warning("[PooledStrategy] This is NOT suitable for race condition attacks!")

        # Create pool sessions
        for i in range(self.pool_size):
            session = client.create_session()
            self.pool.put(session)

    def get_session(self, thread_id: int) -> requests.Session:
        """
        Get a session from the pool.

        If pool is empty, this blocks until a session becomes available.
        This blocking serializes thread execution, defeating race conditions.

        Args:
            thread_id: Thread identifier (for logging)

        Returns:
            Session from pool
        """
        # This blocks if pool is empty!
        session = self.pool.get()
        return session

    def return_session(self, session: requests.Session) -> None:
        """
        Return a session to the pool.

        Args:
            session: Session to return
        """
        self.pool.put(session)

    def cleanup(self) -> None:
        """
        Close all sessions in the pool.
        """
        logger.info(f"[PooledStrategy] Closing {self.pool_size} pooled sessions...")

        # Drain pool and close sessions
        while not self.pool.empty():
            try:
                session = self.pool.get_nowait()
                session.close()
            except queue.Empty:
                break

        logger.info("[PooledStrategy] Cleanup complete")
