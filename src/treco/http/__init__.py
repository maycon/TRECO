"""
HTTP client and utilities.

This module provides HTTP request handling, parsing, and data extraction.
"""

from typing import Any
from .client import HTTPClient
from .parser import HTTPParser
from .extractor import RegExExtractor

Extractors: dict[str, Any] = {
    "regex": RegExExtractor,
}

__all__ = ["HTTPClient", "HTTPParser", "Extractors"]
