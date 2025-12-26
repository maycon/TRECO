"""
Extractor package.

Provides data extractors for HTTP responses with auto-discovery support.
New extractors can be added simply by creating a new module and decorating
the extractor class with @register_extractor.

Example of creating a new extractor:

    # In a new file, e.g., xpath.py
    from treco.http.extractor.base import BaseExtractor
    from treco.http.extractor.registry import register_extractor
    
    @register_extractor('xpath', aliases=['xml_path'])
    class XPathExtractor(BaseExtractor):
        def extract(self, response, pattern):
            # Implementation here
            ...

The extractor will be automatically discovered and available via:
    get_extractor('xpath')
"""

from typing import Dict, Optional

from treco.models.config import ExtractPattern
from treco.http.extractor.base import BaseExtractor, ExtractorRegistry, ResponseProtocol, UnknownExtractorError, register_extractor

def get_extractor(pattern_type: str) -> BaseExtractor:
    """
    Return an extractor instance for the given pattern type.
    
    Args:
        pattern_type: The type or alias of the extractor (e.g., 'regex', 'jpath')
        
    Returns:
        An instance of the appropriate extractor class
        
    Raises:
        UnknownExtractorError: If no extractor is registered for the given type
    """
    return ExtractorRegistry.get_instance(pattern_type)


def extract_all(
    response: ResponseProtocol, extracts: Dict[str, ExtractPattern], context: Optional[Dict] = None
) -> Dict[str, Optional[str]]:
    """
    Run all patterns in `extracts` against `response`.

    Args:
        response: HTTP response object
        extracts: Dict[logical_name, ExtractPattern]
        context: Optional execution context for accessing variables
        
    Returns:
        Dictionary mapping logical names to extracted values
    """
    results: Dict[str, Optional[str]] = {}

    for name, pattern in extracts.items():
        extractor = get_extractor(pattern.pattern_type)
        results[name] = extractor.extract(response, pattern.pattern_data, context)

    return results


# Public API
__all__ = [
    # Core classes
    'BaseExtractor',
    'ExtractorRegistry',
    
    # Decorator
    'register_extractor',
    
    # Functions
    'get_extractor',
    'extract_all',
    
    # Exceptions
    'UnknownExtractorError',
]