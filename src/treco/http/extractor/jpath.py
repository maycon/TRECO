"""
JSONPath extractor module.

Extracts data from JSON responses using JSONPath expressions.
"""

from typing import Any, Optional
from jsonpath_ng import parse

from treco.http.extractor.base import BaseExtractor, ResponseProtocol, register_extractor


@register_extractor('jpath', aliases=['jsonpath', 'json_path'])
class JPathExtractor(BaseExtractor):
    """
    Extractor implementation using JSONPath (JPath).
    
    Supports JSONPath expressions to extract data from JSON responses.
    Registered as 'jpath' with aliases 'jsonpath' and 'json_path'.
    """

    def extract(self, response: ResponseProtocol, pattern: str) -> Optional[Any]:
        """
        Extract data from response using JSONPath expression.

        Args:
            response: HTTP response object
            pattern: JSONPath expression string

        Returns:
            Extracted data or None if not found

        Example:
            extractor = JPathExtractor()
            response = requests.get("http://api.example.com/auth")
            data = extractor.extract(response, '$.access_token')
            # data = "Sayings of the Century"

        References:
            - https://www.rfc-editor.org/rfc/rfc9535.html
            - https://goessner.net/articles/JsonPath/
            - https://jsonpath.com/
        """
        # assuming response is a JSON string or dict
        data = response.json()
        if data is None:
            return None

        # TODO: handle non-JSON responses gracefully
        # TODO: check content-type header for application/json

        expr = parse(pattern)
        matches = [match.value for match in expr.find(data)]
        if not matches:
            return None
        # return first match, or list if you prefer
        return matches[0]