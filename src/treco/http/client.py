"""
HTTP client implementation.

Provides HTTP/HTTPS communication with the target server.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional

import logging

logger = logging.getLogger(__name__)

from treco.models import ServerConfig
from treco.http.parser import HTTPParser


class HTTPClient:
    """
    HTTP client for sending requests to the target server.

    Features:
    - HTTP and HTTPS support
    - Configurable TLS verification
    - Connection pooling
    - Automatic retry on failure
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

        logger.info(response.status_code)  # 200
    """

    def __init__(self, config: ServerConfig):
        """
        Initialize HTTP client with server configuration.

        Args:
            config: Server configuration (host, port, TLS settings)
        """
        self.config = config
        self.parser = HTTPParser()

        # Build base URL
        scheme = "https" if config.tls.enabled else "http"
        self.base_url = f"{scheme}://{config.host}:{config.port}"

        # Create session with connection pooling
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Create a requests Session with retry logic and pooling.

        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Configure TLS verification
        if self.config.tls.enabled and not self.config.tls.verify_cert:
            session.verify = False
            # Suppress InsecureRequestWarning
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return session

    def send(self, http_raw: str) -> requests.Response:
        """
        Send an HTTP request from raw HTTP text.

        Args:
            http_raw: Raw HTTP request text (method, headers, body)

        Returns:
            requests.Response object

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
        response = self.session.request(
            method = method,
            url = url,
            headers = headers,
            allow_redirects = self.config.http.follow_redirects,
            verify=self.config.tls.verify_cert,
            data = body,
            timeout = 30,
        )

        return response

    def create_session(self) -> requests.Session:
        """
        Create a new session for multi-threaded usage.

        Each thread in a race condition attack should have its own session
        to avoid contention.

        Returns:
            New requests.Session
        """
        return self._create_session()

    def close(self) -> None:
        """Close the session and release resources."""
        self.session.close()
