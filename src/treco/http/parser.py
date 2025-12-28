"""
HTTP request parser.

Parses raw HTTP text into structured components.
"""

import logging

import re
from typing import Tuple, Dict, Optional

logger = logging.getLogger(__name__)

class HTTPParser:
    """
    Parses raw HTTP request text into components.

    Converts raw HTTP format:
        POST /api/login HTTP/1.1
        Host: localhost
        Content-Type: application/json

        {"username": "alice"}

    Into structured components:
        method = "POST"
        path = "/api/login"
        headers = {"Host": "localhost", "Content-Type": "application/json"}
        body = '{"username": "alice"}'

    Example:
        parser = HTTPParser()
        method, path, headers, body = parser.parse(http_text)
    """

    def parse(self, http_raw: str) -> Tuple[str, str, Dict[str, str], Optional[str]]:
        """
        Parse raw HTTP request text.

        Args:
            http_raw: Raw HTTP request as string

        Returns:
            Tuple of (method, path, headers_dict, body)

        Raises:
            ValueError: If HTTP format is invalid

        Example:
            method, path, headers, body = parser.parse('''
                POST /api/login HTTP/1.1
                Host: localhost
                Content-Type: application/json

                {"username": "alice"}
            ''')
        """
        # Split the raw HTTP text into individual lines
        # This gives us access to request line, headers, and body separately
        lines = http_raw.strip().split("\n")

        if not lines:
            raise ValueError("Empty HTTP request")

        # Parse the first line: "METHOD /path HTTP/1.1"
        # Example: "POST /api/login HTTP/1.1" -> method="POST", path="/api/login"
        request_line = lines[0].strip()
        method, path = self._parse_request_line(request_line)

        # Find the blank line separating headers from body
        # HTTP spec: headers and body are separated by an empty line (\n\n)
        separator_idx = None
        for idx, line in enumerate(lines[1:], start=1):
            if not line.strip():
                separator_idx = idx
                break

        # Split lines into header section and body section
        if separator_idx:
            header_lines = lines[1:separator_idx]  # Lines between request line and blank line
            body_lines = lines[separator_idx + 1 :]  # Lines after blank line
        else:
            # No separator found - all remaining lines are headers
            header_lines = lines[1:]
            body_lines = []

        # Parse headers into a dictionary: {"Host": "localhost", "Content-Type": "application/json"}
        headers = self._parse_headers(header_lines)

        # Parse body (if present)
        # Body is everything after the blank line, joined back together
        body = None
        if body_lines:
            body = "\n".join(line for line in body_lines).strip()

        return method, path, headers, body

    def _parse_request_line(self, line: str) -> Tuple[str, str]:
        """
        Parse HTTP request line.

        Args:
            line: Request line (e.g., "GET /api/users HTTP/1.1")

        Returns:
            Tuple of (method, path)
        """
        # Use regex to extract HTTP method and path
        # Pattern matches: "METHOD /path HTTP/version" or "METHOD /path"
        # Examples:
        #   "GET /api/users HTTP/1.1" -> method="GET", path="/api/users"
        #   "POST /login" -> method="POST", path="/login"
        pattern = r"^(\w+)\s+(\S+)(?:\s+HTTP/[\d.]+)?$"
        match = re.match(pattern, line)

        if not match:
            raise ValueError(f"Invalid HTTP request line: {line}")

        # Extract method (group 1) and convert to uppercase
        method = match.group(1).upper()
        # Extract path (group 2)
        path = match.group(2)

        return method, path

    def _parse_headers(self, lines: list) -> Dict[str, str]:
        """
        Parse HTTP headers.

        Args:
            lines: List of header lines

        Returns:
            Dictionary of header name -> value
        """
        headers = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            # Each header line has format: "Name: Value"
            # Example: "Content-Type: application/json"
            if ":" not in line:
                continue  # Skip malformed lines

            # Split on the FIRST colon only
            # This handles headers like "Authorization: Bearer token:with:colons"
            name, value = line.split(":", 1)
            headers[name.strip()] = value.strip()

        return headers
