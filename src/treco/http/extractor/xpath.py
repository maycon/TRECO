"""
XPath extractor module.

Extracts data from XML/HTML responses using XPath expressions.
"""

import logging
from typing import Any, Optional, Dict
from lxml import etree # type: ignore

from treco.http.extractor.base import BaseExtractor, ResponseProtocol, register_extractor

logger = logging.getLogger(__name__)


@register_extractor('xpath', aliases=['xml_path', 'html_path'])
class XPathExtractor(BaseExtractor):
    """
    Extractor implementation using XPath.

    Supports XPath expressions to extract data from XML/HTML responses.
    Registered as 'xpath' with aliases 'xml_path' and 'html_path'.
    """

    def extract(self, response: ResponseProtocol, pattern: str, context: Optional[Dict] = None) -> Optional[Any]:
        """
        Extract data from response using XPath expression.

        Args:
            response: HTTP response object
            pattern: XPath expression string

        Returns:
            Extracted data or None if not found

        Example:
            extractor = XPathExtractor()
            response = requests.get("http://example.com/page")
            data = extractor.extract(response, '//input[@name="csrf_token"]/@value')
            # data = "abc123..."

        References:
            - https://www.w3.org/TR/xpath/
            - https://lxml.de/xpathxslt.html
        """
        content = response.text
        if not content:
            return None

        # Try to parse as HTML first (more lenient), fall back to XML
        tree = self._parse_content(content, response)
        if tree is None:
            return None

        try:
            matches = tree.xpath(pattern)
        except etree.XPathEvalError as e:
            logger.warning(f"[Extractor] Invalid XPath expression '{pattern}': {e}")
            return None

        if not matches:
            logger.warning(f"[Extractor] XPath pattern '{pattern}' not found in response.")
            return None

        # Return first match, converting element to text if needed
        return self._extract_value(matches[0])

    def _parse_content(
        self, content: str, response: ResponseProtocol
    ) -> Optional[etree._Element]:
        """
        Parse content as HTML or XML based on content-type.

        Args:
            content: Response text content
            response: HTTP response object (for content-type header)

        Returns:
            Parsed lxml tree or None if parsing fails
        """
        content_type = response.headers.get('Content-Type', '').lower()

        # Try XML parser for XML content types
        if 'xml' in content_type and 'html' not in content_type:
            try:
                return etree.fromstring(content.encode())
            except etree.XMLSyntaxError:
                pass  # Fall through to HTML parser

        # Use HTML parser (more lenient) for everything else
        try:
            return etree.HTML(content)
        except etree.ParserError as e:
            logger.warning(f"[Extractor] Failed to parse response content: {e}")
            return None

    def _extract_value(self, match: Any) -> Any:
        """
        Extract the value from an XPath match result.

        Args:
            match: XPath match result (element, attribute, or text)

        Returns:
            Extracted string value
        """
        if isinstance(match, etree._Element):
            # For elements, get text content
            return match.text or etree.tostring(match, encoding='unicode', method='text')
        elif isinstance(match, etree._ElementUnicodeResult):
            # For attributes and text nodes
            return str(match)
        else:
            # For other types (strings, numbers from XPath functions)
            return match