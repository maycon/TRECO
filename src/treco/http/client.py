"""
HTTP client implementation.

Provides HTTP/HTTPS communication with the target server using httpx.
"""

import httpx
from typing import Optional, Union, Tuple
from pathlib import Path

import logging

from treco.models import TargetConfig
from treco.http.parser import HTTPParser

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    HTTP client for sending requests to the target server.

    Features:
    - HTTP/1.1 and HTTP/2 support
    - Configurable TLS verification
    - Connection pooling
    - Proxy support with bypass option
    - mTLS (mutual TLS) client certificate authentication
    """

    def __init__(self, target: TargetConfig, http2: bool = False):
        """
        Initialize HTTP client with server configuration.

        Args:
            target: Server configuration (host, port, TLS settings, proxy)
            http2: Whether to use HTTP/2 (default: False for compatibility)
        """
        self.config = target
        self.parser = HTTPParser()
        self._http2 = http2

        # Build base URL
        scheme = "https" if target.tls.enabled else "http"
        self.base_url = f"{scheme}://{target.host}:{target.port}"

        # Create both clients: one with proxy, one without
        self._client_no_proxy = self._create_client(use_proxy=False)
        self._client_with_proxy = self._create_client(use_proxy=True)
    
    def _get_client_cert(self) -> Optional[Union[str, Tuple[str, str], Tuple[str, str, str]]]:
        """
        Build the client certificate parameter for httpx.
        
        Returns:
            None if no mTLS configured, otherwise one of:
            - str: path to combined PEM file
            - Tuple[str, str]: (cert_path, key_path)
            - Tuple[str, str, str]: (cert_path, key_path, password)
        
        Raises:
            FileNotFoundError: If certificate files don't exist
            ValueError: If PKCS12 format is specified (not supported by httpx directly)
        """
        tls = self.config.tls
        
        # Check for PKCS12 format (not directly supported by httpx)
        if tls.client_pfx:
            raise ValueError(
                "PKCS12 (.pfx/.p12) format is not directly supported by httpx. "
                "Please convert to PEM format or use separate cert/key files. "
                "Conversion: openssl pkcs12 -in client.pfx -out client.pem -nodes"
            )
        
        # Combined PEM file
        if tls.client_pem:
            pem_path = Path(tls.client_pem)
            if not pem_path.exists():
                raise FileNotFoundError(f"Client PEM file not found: {tls.client_pem}")
            return str(pem_path)
        
        # Separate cert and key files
        if tls.client_cert and tls.client_key:
            cert_path = Path(tls.client_cert)
            key_path = Path(tls.client_key)
            
            if not cert_path.exists():
                raise FileNotFoundError(f"Client certificate file not found: {tls.client_cert}")
            if not key_path.exists():
                raise FileNotFoundError(f"Client key file not found: {tls.client_key}")
            
            if tls.client_key_password:
                return (str(cert_path), str(key_path), tls.client_key_password)
            else:
                return (str(cert_path), str(key_path))
        
        return None

    def _create_client(self, use_proxy: bool = False) -> httpx.Client:
        """
        Create an httpx Client with connection pooling.

        Args:
            use_proxy: Whether to configure proxy for this client

        Returns:
            Configured httpx.Client
        """
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0,
        )

        timeout = httpx.Timeout(30.0)
        verify_cert = self.config.tls.verify_cert if self.config.tls.enabled else True
        
        # Only set proxy if use_proxy=True AND proxy is configured
        proxy_url = None
        if use_proxy and self.config.proxy:
            proxy_url = self.config.proxy.to_client_proxy()
        
        # Get client certificate for mTLS if configured
        cert = self._get_client_cert() if self.config.tls.enabled else None

        client = httpx.Client(
            http2=self._http2,
            verify=verify_cert,
            timeout=timeout,
            limits=limits,
            follow_redirects=self.config.http.follow_redirects,
            proxy=proxy_url,
            cert=cert
        )

        return client

    def get_client(self, bypass_proxy: bool = False) -> httpx.Client:
        """
        Get appropriate client based on proxy bypass setting.
        
        Args:
            bypass_proxy: If True, return client WITHOUT proxy
            
        Returns:
            httpx.Client configured appropriately
        """
        return self._client_no_proxy if bypass_proxy else self._client_with_proxy

    def send(self, http_raw: str, bypass_proxy: bool = False) -> httpx.Response:
        """
        Send an HTTP request from raw HTTP text.

        Args:
            http_raw: Raw HTTP request text (method, headers, body)
            bypass_proxy: If True, send without proxy

        Returns:
            httpx.Response object
        """
        method, path, headers, body = self.parser.parse(http_raw)
        url = self.base_url + path
        
        client = self.get_client(bypass_proxy)

        response = client.request(
            method=method,
            url=url,
            headers=headers,
            content=body if body else None,
        )

        return response

    def create_client(self, http2: bool = False, use_proxy: bool = True) -> httpx.Client:
        """
        Create a new client for multi-threaded usage.

        Each thread in a race condition attack should have its own client
        to avoid contention.

        Args:
            http2: Whether to use HTTP/2
            use_proxy: Whether to use proxy (default: True)

        Returns:
            New httpx.Client
        """
        limits = httpx.Limits(
            max_keepalive_connections=1,
            max_connections=1,
            keepalive_expiry=30.0,
        )
        
        proxy_url = None
        if use_proxy and self.config.proxy:
            proxy_url = self.config.proxy.to_client_proxy()
        
        # Get client certificate for mTLS if configured
        cert = self._get_client_cert() if self.config.tls.enabled else None

        return httpx.Client(
            http2=http2,
            verify=self.config.tls.verify_cert if self.config.tls.enabled else True,
            timeout=httpx.Timeout(30.0),
            limits=limits,
            follow_redirects=self.config.http.follow_redirects,
            base_url=self.base_url,
            proxy=proxy_url,
            cert=cert
        )

    def close(self) -> None:
        """Close the clients and release resources."""
        self._client_no_proxy.close()
        self._client_with_proxy.close()