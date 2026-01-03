"""
Unified HTTP response interface for template access.

Provides a consistent, user-friendly interface for accessing HTTP response
data in Jinja2 templates, abstracting away differences between httpx.Response
and dictionary representations.
"""

from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ResponseWrapper:
    """
    Unified interface for HTTP response access in Jinja2 templates.
    
    Provides consistent property access for response data regardless of
    whether the underlying object is an httpx.Response or a dictionary.
    
    Features:
    - Unified property access (response.status, response.text, etc.)
    - Cookie extraction by name
    - Header extraction by name (case-insensitive)
    - JSON parsing with error handling
    - Boolean helpers (is_ok, is_redirect, is_error)
    
    Usage in templates:
        # Status code
        {{ response.status }}         # 200
        {{ response.status_code }}    # 200 (alias)
        
        # Body/content
        {{ response.text }}            # "Hello World"
        {{ response.body }}            # "Hello World" (alias)
        {{ response.content }}         # b"Hello World" (bytes)
        
        # Headers
        {{ response.headers }}                    # All headers dict
        {{ response.header('Content-Type') }}     # Specific header
        {{ response.header('content-type') }}     # Case-insensitive
        
        # Cookies
        {{ response.cookies }}                    # All cookies dict
        {{ response.cookie('session') }}          # Specific cookie
        
        # JSON
        {{ response.json() }}                     # Parsed JSON
        {{ response.json().user.name }}           # Access nested data
        
        # URL
        {{ response.url }}             # Request URL
        
        # Boolean helpers
        {{ response.is_ok }}           # True if 2xx
        {{ response.is_redirect }}     # True if 3xx
        {{ response.is_client_error }} # True if 4xx
        {{ response.is_server_error }} # True if 5xx
        {{ response.is_error }}        # True if 4xx or 5xx
    
    Examples:
        # Check successful login
        {% if response.is_ok and 'Welcome' in response.text %}
        ✅ Login successful
        {% endif %}
        
        # Extract session cookie
        {% set session = response.cookie('session') %}
        Cookie: session={{ session }}
        
        # Check redirect location
        {% if response.is_redirect %}
        Redirected to: {{ response.header('Location') }}
        {% endif %}
        
        # Parse JSON response
        {% set data = response.json() %}
        User ID: {{ data.user_id }}
        Token: {{ data.access_token }}
    """
    
    def __init__(self, response: Any):
        """
        Initialize ResponseWrapper.
        
        Args:
            response: httpx.Response object or dictionary
        """
        self._response = response
        self._is_httpx = hasattr(response, 'status_code')
        self._cached_json = None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Status Code Properties
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @property
    def status(self) -> int:
        """HTTP status code (200, 404, etc.)."""
        if self._is_httpx:
            return self._response.status_code
        return self._response.get('status_code', self._response.get('status', 0))
    
    @property
    def status_code(self) -> int:
        """Alias for status."""
        return self.status
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Body/Content Properties
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @property
    def text(self) -> str:
        """Response body as text/string."""
        if self._is_httpx:
            return self._response.text
        return self._response.get('text', '')
    
    @property
    def body(self) -> str:
        """Alias for text."""
        return self.text
    
    @property
    def content(self) -> bytes:
        """Response body as bytes."""
        if self._is_httpx:
            return self._response.content
        
        # If dict, try to get content or encode text
        content = self._response.get('content')
        if content is not None:
            return content
        
        text = self._response.get('text', '')
        return text.encode('utf-8') if isinstance(text, str) else b''
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Headers Access
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @property
    def headers(self) -> Dict[str, str]:
        """All response headers as dictionary."""
        if self._is_httpx:
            return dict(self._response.headers)
        return self._response.get('headers', {})
    
    def header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get specific header value (case-insensitive).
        
        Args:
            name: Header name (case-insensitive)
            default: Default value if header not found
            
        Returns:
            Header value or default
            
        Example:
            {{ response.header('Content-Type') }}
            {{ response.header('X-Rate-Limit', '0') }}
        """
        headers = self.headers
        
        # Case-insensitive lookup
        name_lower = name.lower()
        for key, value in headers.items():
            if key.lower() == name_lower:
                return value
        
        return default
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Cookies Access
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @property
    def cookies(self) -> Dict[str, str]:
        """All response cookies as dictionary."""
        if self._is_httpx:
            return dict(self._response.cookies) if hasattr(self._response, 'cookies') else {}
        return self._response.get('cookies', {})
    
    def cookie(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get specific cookie value.
        
        Args:
            name: Cookie name
            default: Default value if cookie not found
            
        Returns:
            Cookie value or default
            
        Example:
            {{ response.cookie('session') }}
            {{ response.cookie('user_id', 'guest') }}
        """
        return self.cookies.get(name, default)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # URL Property
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @property
    def url(self) -> str:
        """Request URL."""
        if self._is_httpx:
            return str(self._response.url) if hasattr(self._response, 'url') else ''
        return self._response.get('url', '')
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # JSON Parsing
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def json(self) -> Any:
        """
        Parse response body as JSON.
        
        Returns:
            Parsed JSON object (dict, list, etc.)
            
        Raises:
            ValueError: If response is not valid JSON
            
        Example:
            {% set data = response.json() %}
            Token: {{ data.access_token }}
            
            {% set users = response.json() %}
            {% for user in users %}
              - {{ user.name }}
            {% endfor %}
        """
        if self._cached_json is not None:
            return self._cached_json
        
        if self._is_httpx:
            try:
                self._cached_json = self._response.json()
                return self._cached_json
            except Exception as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                raise ValueError(f"Invalid JSON response: {e}")
        
        # For dict responses, try to parse text as JSON
        import json
        try:
            text = self._response.get('text', '{}')
            self._cached_json = json.loads(text)
            return self._cached_json
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from text: {e}")
            raise ValueError(f"Invalid JSON response: {e}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Boolean Helpers
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @property
    def is_ok(self) -> bool:
        """True if status code is 2xx (success)."""
        return 200 <= self.status < 300
    
    @property
    def is_redirect(self) -> bool:
        """True if status code is 3xx (redirect)."""
        return 300 <= self.status < 400
    
    @property
    def is_client_error(self) -> bool:
        """True if status code is 4xx (client error)."""
        return 400 <= self.status < 500
    
    @property
    def is_server_error(self) -> bool:
        """True if status code is 5xx (server error)."""
        return 500 <= self.status < 600
    
    @property
    def is_error(self) -> bool:
        """True if status code is 4xx or 5xx (any error)."""
        return self.status >= 400
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Utility Methods
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ResponseWrapper(status={self.status}, url='{self.url}')"
    
    def __str__(self) -> str:
        """String conversion returns response text."""
        return self.text
    
    def __bool__(self) -> bool:
        """Boolean conversion checks if response is OK."""
        return self.is_ok
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export response as dictionary.
        
        Returns:
            Dictionary with all response data
        """
        return {
            'status': self.status,
            'status_code': self.status_code,
            'text': self.text,
            'body': self.body,
            'content': self.content,
            'headers': self.headers,
            'cookies': self.cookies,
            'url': self.url,
            'is_ok': self.is_ok,
            'is_redirect': self.is_redirect,
            'is_client_error': self.is_client_error,
            'is_server_error': self.is_server_error,
            'is_error': self.is_error,
        }


def wrap_response(response: Any) -> Optional[ResponseWrapper]:
    """
    Wrap an httpx.Response or dict in ResponseWrapper.
    
    Args:
        response: httpx.Response, dict, or None
        
    Returns:
        ResponseWrapper instance or None if response is None
        
    Example:
        wrapped = wrap_response(httpx_response)
        status = wrapped.status
        session = wrapped.cookie('session')
    """
    if response is None:
        return None
    
    return ResponseWrapper(response)