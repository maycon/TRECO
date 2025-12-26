"""
Cookie extractor module.

Extracts cookie values from HTTP response Set-Cookie headers.
"""

import logging
from typing import Any, Optional, Dict

from treco.http.extractor.base import BaseExtractor, ResponseProtocol, register_extractor

logger = logging.getLogger(__name__)


@register_extractor('cookie', aliases=['cookies', 'set_cookie', 'set-cookie'])
class CookieExtractor(BaseExtractor):
    """
    Extractor implementation for HTTP cookies.

    Extracts cookie values from Set-Cookie response headers using
    the requests library's built-in cookie handling.
    Registered as 'cookie' with aliases 'cookies', 'set_cookie', and 'set-cookie'.
    """

    def extract(self, response: ResponseProtocol, pattern: str, context: Optional[Dict] = None) -> Optional[Any]:
        """
        Extract cookie value from response.

        Args:
            response: HTTP response object
            pattern: Cookie name to extract

        Returns:
            Cookie value or None if not found

        Example:
            extractor = CookieExtractor()
            response = requests.get("http://example.com/login")
            
            # Extract session cookie value
            session = extractor.extract(response, 'session_id')
            # session = "abc123xyz"
            
            # Extract CSRF token cookie
            csrf = extractor.extract(response, 'csrf_token')
            # csrf = "token456"

        References:
            - https://www.rfc-editor.org/rfc/rfc6265
        """
        cookie_name = pattern.strip()

        if not cookie_name:
            logger.warning("[Extractor] Empty cookie name provided.")
            return None

        # Use requests' built-in cookie jar (RequestsCookieJar)
        # which automatically parses Set-Cookie headers
        value = response.cookies.get(cookie_name)

        if value is None:
            logger.warning(f"[Extractor] Cookie '{cookie_name}' not found in response.")
            return None

        return value