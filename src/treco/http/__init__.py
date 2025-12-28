"""
HTTP client and utilities.

This module provides HTTP request handling, parsing, and data extraction.
"""

from .client import HTTPClient
from .parser import HTTPParser
from .extractor import ExtractorRegistry, get_extractor
from .adapter import HttpxResponseAdapter

__all__ = ["HTTPClient", "HTTPParser", "HttpxResponseAdapter", "ExtractorRegistry", "get_extractor"]
