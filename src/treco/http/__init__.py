"""
HTTP client and utilities.

This module provides HTTP request handling, parsing, and data extraction.
"""

from typing import Any
from .client import HTTPClient
from .parser import HTTPParser
from .extractor import ExtractorRegistry, get_extractor

__all__ = ["HTTPClient", "HTTPParser", "ExtractorRegistry", "get_extractor"]
