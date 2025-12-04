"""
Data extractor using regex patterns.

Extracts structured data from HTTP responses.
"""

from abc import abstractmethod
import re
from typing import Dict, Any, Optional
import requests

import logging

from treco.http.extractor.base import BaseExtractor

logger = logging.getLogger(__name__)


class RegExExtractor(BaseExtractor):
    """
    Extracts data from HTTP responses using regex patterns.

    The extractor applies regex patterns to response text and
    captures groups as variables.

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

    def extract(self, response: requests.Response, pattern: str) -> Optional[str]:
        """
        Extract data from response using regex patterns.

        Args:
            response: HTTP response object
            patterns: Dictionary of variable_name -> regex_pattern

        Returns:
            Dictionary of extracted variables

        Example:
            patterns = {
                "bearer_token": r'"token":\\s*"([^"]+)"',
                "user_id": r'"id":\\s*(\\d+)',
                "balance": r'"balance":\\s*(\\d+\\.?\\d*)'
            }

            extracted = extractor.extract(response, patterns)
            # {"bearer_token": "xyz...", "user_id": "42", "balance": "1000"}
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
