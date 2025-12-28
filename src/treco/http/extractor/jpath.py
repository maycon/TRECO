"""
JSONPath extractor module.

Extracts data from JSON responses using JSONPath expressions.
"""

import json
import logging
from typing import Any, Optional, Dict
from jsonpath_ng import parse

from treco.http.extractor.base import BaseExtractor, ResponseProtocol, register_extractor

logger = logging.getLogger(__name__)


@register_extractor('jpath', aliases=['jsonpath', 'json_path'])
class JPathExtractor(BaseExtractor):
    """
    Extractor implementation using JSONPath (JPath).
    
    Supports JSONPath expressions to extract data from JSON responses.
    Registered as 'jpath' with aliases 'jsonpath' and 'json_path'.
    """

    def extract(self, response: ResponseProtocol, pattern: str, context: Optional[Dict] = None) -> Optional[Any]:
        """
        Extract data from response using JSONPath expression.

        Args:
            response: HTTP response object
            pattern: JSONPath expression string
            context: Optional context dict (unused)

        Returns:
            Extracted data or None if not found

        Example:
            extractor = JPathExtractor()
            response = requests.get("http://api.example.com/auth")
            data = extractor.extract(response, '$.access_token')
        """
        # Check if response has content
        if not response.content:
            logger.debug(f"Empty response body, cannot extract with jpath: {pattern}")
            return None
        
        # Try to parse JSON
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Response is not valid JSON, cannot extract with jpath: {pattern}. Error: {e}")
            return None
        
        if data is None:
            return None

        # Parse and execute JSONPath expression
        try:
            expr = parse(pattern)
            matches = [match.value for match in expr.find(data)]
        except Exception as e:
            logger.debug(f"JSONPath parse/find error for pattern '{pattern}': {e}")
            return None
        
        if not matches:
            return None
        
        # Return first match
        return matches[0]