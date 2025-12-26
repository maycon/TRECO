"""
Regex extractor module.

Extracts data from HTTP responses using regular expression patterns.
"""

import re
import logging
from typing import Any, Optional, Dict

from treco.http.extractor.base import BaseExtractor, ResponseProtocol, register_extractor

logger = logging.getLogger(__name__)


@register_extractor('regex', aliases=['re', 'regexp', 'regular_expression'])
class RegExExtractor(BaseExtractor):
    """
    Extracts data from HTTP responses using regex patterns.

    The extractor applies regex patterns to response text and
    captures groups as variables.
    
    Registered as 'regex' with aliases 're', 'regexp', and 'regular_expression'.

    Example:
        extractor = RegExExtractor()

        patterns = {
            "token": r'"token":\\s*"([^"]+)"',
            "balance": r'"balance":\\s*(\\d+\\.?\\d*)'
        }

        response = requests.get("http://api.example.com/auth")
        data = extractor.extract(response, patterns)

        # data = {"token": "abc123", "balance": "1000.50"}
    """

    def extract(self, response: ResponseProtocol, pattern: str, context: Optional[Dict] = None) -> Optional[str]:
        """
        Extract data from response using regex patterns.

        Args:
            response: HTTP response object
            pattern: Regex pattern string

        Returns:
            Extracted value or None if not found

        Example:
            pattern = r'"bearer_token":\\s*"([^"]+)"'
            extracted = extractor.extract(response, pattern)
            # "xyz..."
        """
        response_text = response.text

        match = re.search(pattern, response_text)

        if match:
            # Extract first captured group
            if match.groups():
                value = match.group(1)
                return self._convert_type(value)
            else:
                # No capture group, use entire match
                return match.group(0)

        # Pattern didn't match, store None
        logger.warning(f"[Extractor] Pattern '{pattern}' not found in response.")
        return None

    def _convert_type(self, value: str) -> Any:
        """
        Attempt to convert string value to appropriate type.

        Tries to convert to int, float, or bool. Falls back to string.

        Args:
            value: String value to convert

        Returns:
            Converted value
        """
        # Try boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value