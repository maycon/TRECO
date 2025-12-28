"""
Pooled connection strategy.

Shares a pool of connections among threads.
NOT recommended for race condition attacks.
"""

import queue
import logging
from typing import Optional

import httpx

from .base import ConnectionStrategy
from ..sync.base import SyncMechanism

logger = logging.getLogger("treco")


class PooledStrategy(ConnectionStrategy):
    """
    Pooled strategy - share a pool of M connections among N threads.

    How it works:
        1. Create a pool of M clients (M < N typically)
        2. Threads request clients from the pool
        3. If pool is empty, thread blocks until a client is returned
        4. After use, thread returns client to pool

    Advantages:
        - Limits total number of connections
        - Good for resource-constrained scenarios

    Disadvantages:
        - Serializes requests (threads wait for clients)
        - Defeats the purpose of race conditions!
        - NOT RECOMMENDED for race attacks

    Use cases:
        - Load testing with connection limits
        - Simulating connection pools in production
        - NOT for race condition exploits

    Why this doesn't work for race conditions:
        Time ->

        Pool (5 clients):
        [C1] [C2] [C3] [C4] [C5]

        20 threads compete for 5 clients:
        T1,T2,T3,T4,T5 -> Get clients, send requests
        T6,T7,T8,T9,T10 -> WAIT for clients
        T11...T20 -> WAIT even longer

        Result: Requests are serialized in groups of 5
        Not a race condition, just slow sequential requests!
    """

    def __init__(
        self, 
        sync: Optional[SyncMechanism] = None, 
        pool_size: int = 5,
    ):
        """
        Initialize pool.
        
        Args:
            sync: Sync mechanism (usually not needed for pooled strategy)
            pool_size: Maximum number of clients in the pool
        """
        # Use HTTP/2 by default
        super().__init__(sync=sync, http2=True)
        self._pool: queue.Queue = queue.Queue()
        self._pool_size = pool_size

    def _prepare(self, num_threads: int, http_client) -> None:
        """
        Create a pool of M clients.

        Args:
            num_threads: Number of threads (pool will be smaller)
            http_client: HTTP client with configuration
        """
        # Create pool (smaller than thread count)
        actual_pool_size = min(num_threads, self._pool_size)
        
        logger.info(f"PooledStrategy: Creating pool with {actual_pool_size} clients")
        logger.info(f"PooledStrategy: {num_threads} threads will share these connections")
        logger.warning("PooledStrategy: NOT suitable for race condition attacks!")

        # Create pool clients with pre-established connections
        for i in range(actual_pool_size):
            client = httpx.Client(**self._build_client_kwargs())
            
            # Warm up connection
            self._warmup_connection(client)
            
            self._pool.put(client)
            logger.debug(f"Created pooled client {i+1}/{actual_pool_size}")

    def _connect(self, thread_id: int) -> None:
        """
        No-op for pooled strategy.
        
        Clients are already created in the pool.
        
        Args:
            thread_id: Thread ID (unused)
        """
        logger.debug(f"[Thread {thread_id}] Will use pooled client")

    def get_session(self, thread_id: int) -> httpx.Client:
        """
        Get a client from the pool.

        If pool is empty, this blocks until a client becomes available.
        This blocking serializes thread execution, defeating race conditions.

        Args:
            thread_id: Thread identifier (for logging)

        Returns:
            Client from pool
        """
        logger.debug(f"[Thread {thread_id}] Waiting for pooled client...")
        client = self._pool.get()  # Blocks if empty!
        logger.debug(f"[Thread {thread_id}] Got pooled client")
        return client

    def return_session(self, client: httpx.Client) -> None:
        """
        Return a client to the pool.

        Args:
            client: Client to return
        """
        self._pool.put(client)

    def cleanup(self) -> None:
        """Close all clients in the pool."""
        logger.debug("PooledStrategy: Closing pooled clients...")

        # Drain pool and close clients
        while not self._pool.empty():
            try:
                client = self._pool.get_nowait()
                client.close()
            except queue.Empty:
                break

        logger.debug("PooledStrategy: Cleanup complete")