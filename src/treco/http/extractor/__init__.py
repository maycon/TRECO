from typing import Dict, Optional, Type

import requests

from treco.models.config import ExtractPattern

from treco.http.extractor.base import BaseExtractor
from treco.http.extractor.regex import RegExExtractor
from treco.http.extractor.jpath import JPathExtractor


# Map pattern_type to extractor class
EXTRACTOR_REGISTRY: Dict[str, Type[BaseExtractor]] = {
    "regex": RegExExtractor,
    # "xpath": XPathExtractor,
    "jpath": JPathExtractor,
}


class UnknownExtractorError(Exception):
    pass


def get_extractor(pattern_type: str) -> BaseExtractor:
    """Return an extractor instance for the given pattern type."""
    try:
        extractor_cls = EXTRACTOR_REGISTRY[pattern_type]
    except KeyError:
        raise UnknownExtractorError(f"Unknown pattern_type: {pattern_type}")
    return extractor_cls()


def extract_all(
    response: requests.Response, extracts: Dict[str, ExtractPattern]
) -> Dict[str, Optional[str]]:
    """Run all patterns in `extracts` against `response`.

    extracts: Dict[logical_name, ExtractPattern]
    """
    results: Dict[str, Optional[str]] = {}

    for name, pattern in extracts.items():
        extractor = get_extractor(pattern.pattern_type)
        results[name] = extractor.extract(response, pattern.pattern_data)

    return results
