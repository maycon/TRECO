"""
Boundary extractor module.

Extracts data between left and right delimiters from HTTP responses.
"""

import logging
from typing import Any, Optional, Dict

from treco.http.extractor.base import BaseExtractor, ResponseProtocol, register_extractor

logger = logging.getLogger(__name__)

# Default separator between left and right boundaries
BOUNDARY_SEPARATOR = "|||"

# Special markers
MARKER_EOL = "$"   # End of line
MARKER_BOL = "^"   # Beginning of line


@register_extractor('boundary', aliases=['between', 'delimited'])
class BoundaryExtractor(BaseExtractor):
    """
    Extractor implementation using boundary delimiters.

    Extracts text found between a left boundary and a right boundary.
    This is a simpler alternative to regex for common extraction patterns.
    Registered as 'boundary' with aliases 'between' and 'delimited'.
    
    Pattern format: left_boundary|||right_boundary
    
    Special markers:
        ^  - Beginning of line (for left boundary)
        $  - End of line (for right boundary)
    
    The separator '|||' can be escaped if needed in your boundaries
    by using a different separator (see extract method).
    """

    def extract(
        self, 
        response: ResponseProtocol, 
        pattern: str,
        context: Optional[Dict] = None,
        separator: str = BOUNDARY_SEPARATOR
    ) -> Optional[Any]:
        """
        Extract data from response between boundary delimiters.

        Args:
            response: HTTP response object
            pattern: Boundary pattern in format "left|||right"
            context: Optional execution context (not used by this extractor)
            separator: Separator between boundaries (default: '|||')

        Returns:
            Extracted text or None if not found

        Example:
            extractor = BoundaryExtractor()
            response = requests.get("http://example.com/api")
            
            # Response body: {"token":"abc123","user":"john"}
            
            # Extract token value
            token = extractor.extract(response, '"token":"|||"')
            # token = "abc123"
            
            # Extract from HTML
            # Response: <input name="csrf" value="xyz789"/>
            csrf = extractor.extract(response, 'name="csrf" value="|||"')
            # csrf = "xyz789"
            
            # Extract with empty right boundary (until end)
            # Response: Balance: 1000.50
            balance = extractor.extract(response, 'Balance: |||')
            # balance = "1000.50"
            
            # Extract until end of line using $ marker
            # Response: Authorization: Bearer abc123\\nContent-Type: json
            token = extractor.extract(response, 'Bearer |||$')
            # token = "abc123"
            
            # Extract from beginning of line using ^ marker
            # Response: X-Request-Id: req-456
            header = extractor.extract(response, '^|||: req-456')
            # header = "X-Request-Id"

        References:
            - Similar to Apache JMeter's Boundary Extractor
        """
        if separator not in pattern:
            logger.warning(
                f"[Extractor] Invalid boundary pattern: separator '{separator}' "
                f"not found in pattern '{pattern}'."
            )
            return None

        parts = pattern.split(separator, 1)
        left_boundary = parts[0]
        right_boundary = parts[1] if len(parts) > 1 else ""

        response_text = response.text

        # Handle ^ marker (beginning of line)
        use_bol = left_boundary == MARKER_BOL
        if use_bol:
            left_boundary = ""

        # Handle $ marker (end of line)
        use_eol = right_boundary == MARKER_EOL
        if use_eol:
            right_boundary = ""

        # Find left boundary
        if left_boundary:
            left_index = response_text.find(left_boundary)
            if left_index == -1:
                logger.warning(
                    f"[Extractor] Left boundary '{left_boundary}' not found in response."
                )
                return None
            start_index = left_index + len(left_boundary)
        elif use_bol:
            # ^ marker: find the beginning of the line containing right_boundary
            # First find where right_boundary is, then go back to line start
            if right_boundary:
                right_pos = response_text.find(right_boundary)
                if right_pos == -1:
                    logger.warning(
                        f"[Extractor] Right boundary '{right_boundary}' not found in response."
                    )
                    return None
                # Find the beginning of this line
                line_start = response_text.rfind('\n', 0, right_pos)
                start_index = line_start + 1 if line_start != -1 else 0
            else:
                start_index = 0
        else:
            # Empty left boundary means start from beginning
            start_index = 0

        # Find right boundary
        if right_boundary:
            right_index = response_text.find(right_boundary, start_index)
            if right_index == -1:
                logger.warning(
                    f"[Extractor] Right boundary '{right_boundary}' not found in response."
                )
                return None
            end_index = right_index
        elif use_eol:
            # $ marker: find the end of line from start_index
            newline_index = response_text.find('\n', start_index)
            if newline_index == -1:
                # No newline found, use end of text
                end_index = len(response_text)
            else:
                end_index = newline_index
        else:
            # Empty right boundary means extract until end
            end_index = len(response_text)

        extracted = response_text[start_index:end_index]

        # Strip only if not using special markers (preserve intentional whitespace)
        if not use_bol and not use_eol:
            extracted = extracted.strip()

        return extracted if extracted else None