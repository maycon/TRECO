"""
Header extractor module.

Extracts data from HTTP response headers.
"""

import logging
from typing import Any, Optional, Dict

from treco.http.extractor.base import BaseExtractor, ResponseProtocol, register_extractor

logger = logging.getLogger(__name__)


@register_extractor('header', aliases=['headers', 'http_header'])
class HeaderExtractor(BaseExtractor):
    """
    Extractor implementation for HTTP headers.

    Extracts values from HTTP response headers in a case-insensitive manner.
    Registered as 'header' with aliases 'headers' and 'http_header'.
    """

    def extract(self, response: ResponseProtocol, pattern: str, context: Optional[Dict] = None) -> Optional[Any]:
        """
        Extract data from response headers.

        Args:
            response: HTTP response object
            pattern: Header name (case-insensitive)

        Returns:
            Header value or None if not found

        Example:
            extractor = HeaderExtractor()
            response = requests.get("http://example.com/api")
            
            # All of these work the same way (case-insensitive):
            token = extractor.extract(response, 'X-Auth-Token')
            token = extractor.extract(response, 'x-auth-token')
            token = extractor.extract(response, 'X-AUTH-TOKEN')
            # token = "abc123..."

        References:
            - https://www.rfc-editor.org/rfc/rfc7230#section-3.2
        """
        # ResponseProtocol.headers is already a CaseInsensitiveDict
        # so we can access headers regardless of case
        header_name = pattern.strip()

        if not header_name:
            logger.warning("[Extractor] Empty header name provided.")
            return None

        value = response.headers.get(header_name)

        if value is None:
            logger.warning(f"[Extractor] Header '{header_name}' not found in response.")
            return None

        return value