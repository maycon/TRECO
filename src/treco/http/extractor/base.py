"""
Base extractor module.
Defines the base classes and interfaces for data extractors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests


class BaseExtractor(ABC):
    """
    Abstract base class for data extractors.

    Extractors are responsible for extracting structured data
    from HTTP responses based on specific extraction logic.
    """

    @abstractmethod
    def extract(self, response: requests.Response, pattern: str) -> Optional[str]:
        """
        Extract data from the HTTP response.

        Args:
            response: HTTP response object
            patterns: Dictionary of variable_name -> extraction_pattern

        Returns:
            Dictionary of extracted variables
        """
        pass
