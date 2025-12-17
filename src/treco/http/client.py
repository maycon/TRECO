"""
HTTP client implementation.

Provides HTTP/HTTPS communication with the target server using httpx.
"""

import httpx
from typing import Optional, Union

import logging

logger = logging.getLogger(__name__)

from treco.models import ServerConfig
from treco.http.parser import HTTPParser


class HTTPClient:
    """
    HTTP client for sending requests to the target server.

    Features:
    - HTTP/1.1 and HTTP/2 support
    - Configurable TLS verification
    - Connection pooling
    - Session management

    Example:
        config = ServerConfig(host="localhost", port=8000)
        client = HTTPClient(config)

        response = client.send('''
            POST /api/login HTTP/1.1
            Host: localhost
            Content-Type: application/json

            {"username": "alice"}
        ''')

        print(response.status_code)  # 200
    """

    def __init__(self, config: ServerConfig, http2: bool = False):
        """
        Initialize HTTP client with server configuration.

        Args:
            config: Server configuration (host, port, TLS settings)
            http2: Whether to use HTTP/2 (default: False for compatibility)
        """
        self.config = config
        self.parser = HTTPParser()
        self._http2 = http2

        # Build base URL
        scheme = "https" if config.tls.enabled else "http"
        self.base_url = f"{scheme}://{config.host}:{config.port}"

        # Create client with connection pooling
        self.client = self._create_client()

    def _create_client(self) -> httpx.Client:
        """
        Create an httpx Client with connection pooling.

        Returns:
            Configured httpx.Client
        """
        # Configure connection limits
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0,
        )

        # Configure timeout
        timeout = httpx.Timeout(30.0)

        client = httpx.Client(
            http2=self._http2,
            verify=self.config.tls.verify_cert if self.config.tls.enabled else True,
            timeout=timeout,
            limits=limits,
            follow_redirects=self.config.http.follow_redirects,
            proxy=self.config.proxy.to_client_proxy() if self.config.proxy else None,
        )

        return client

    def send(self, http_raw: str) -> httpx.Response:
        """
        Send an HTTP request from raw HTTP text.

        Args:
            http_raw: Raw HTTP request text (method, headers, body)

        Returns:
            httpx.Response object

        Example:
            response = client.send('''
                GET /api/health HTTP/1.1
                Host: localhost
            ''')
        """
        # Parse raw HTTP into components
        method, path, headers, body = self.parser.parse(http_raw)

        # Build full URL
        url = self.base_url + path

        # Send request
        response = self.client.request(
            method=method,
            url=url,
            headers=headers,
            content=body if body else None,
        )

        return response

    def create_client(self, http2: bool = False) -> httpx.Client:
        """
        Create a new client for multi-threaded usage.

        Each thread in a race condition attack should have its own client
        to avoid contention.

        Args:
            http2: Whether to use HTTP/2

        Returns:
            New httpx.Client
        """
        limits = httpx.Limits(
            max_keepalive_connections=1,
            max_connections=1,
            keepalive_expiry=30.0,
        )

        return httpx.Client(
            http2=http2,
            verify=self.config.tls.verify_cert if self.config.tls.enabled else True,
            timeout=httpx.Timeout(30.0),
            limits=limits,
            follow_redirects=self.config.http.follow_redirects,
            base_url=self.base_url,
        )

    # Alias for backwards compatibility
    def create_session(self) -> httpx.Client:
        """Alias for create_client() for backwards compatibility."""
        return self.create_client()

    def close(self) -> None:
        """Close the client and release resources."""
        self.client.close()