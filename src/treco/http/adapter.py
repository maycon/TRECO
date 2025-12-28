from typing import Any


class HttpxResponseAdapter:
    """
    Adapter to make httpx.Response compatible with ResponseProtocol interface.
    
    This allows existing extractors and template code to work with httpx responses
    without modification.
    
    Attributes:
        status_code: HTTP status code
        text: Response body as text
        content: Response body as bytes
        headers: Response headers (dict-like)
        cookies: Response cookies
        url: Request URL
    """
    
    def __init__(self, httpx_response):
        """
        Create adapter from httpx.Response.
        
        Args:
            httpx_response: httpx.Response object
        """
        self._response = httpx_response
        
        # Direct mappings (same interface)
        self.status_code = httpx_response.status_code
        self.text = httpx_response.text
        self.content = httpx_response.content
        self.headers = dict(httpx_response.headers)
        self.url = str(httpx_response.url)
        
        # Cookies need conversion
        self.cookies = {name: value for name, value in httpx_response.cookies.items()}
    
    def json(self) -> Any:
        """Parse response body as JSON."""
        return self._response.json()
    
    @property
    def ok(self) -> bool:
        """Check if response was successful (2xx)."""
        return 200 <= self.status_code < 300
    
    @property
    def reason(self) -> str:
        """HTTP reason phrase."""
        return self._response.reason_phrase
    
    def __repr__(self) -> str:
        return f"<HttpxResponseAdapter [{self.status_code}]>"