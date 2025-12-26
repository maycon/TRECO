"""
Base extractor module.
Defines the base classes and interfaces for data extractors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, List, Optional, Any, Protocol, runtime_checkable
from pathlib import Path
import pkgutil
import importlib


@runtime_checkable
class ResponseProtocol(Protocol):
    """
    Protocol defining the interface for HTTP responses.
    
    This allows extractors to work with any response object that has
    these attributes, whether from httpx, requests, or custom adapters.
    """
    status_code: int
    text: str
    content: bytes
    headers: Any  # Dict-like
    cookies: Any  # Dict-like (httpx.Cookies or RequestsCookieJar)
    
    def json(self) -> Any: ...


class BaseExtractor(ABC):
    """
    Abstract base class for data extractors.

    Extractors are responsible for extracting structured data
    from HTTP responses based on specific extraction logic.
    """

    _extractor_type: str = ""
    _extractor_aliases: List[str] = []

    @abstractmethod
    def extract(self, response: ResponseProtocol, pattern: Any, context: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Extract data from the HTTP response.

        Args:
            response: HTTP response object (httpx.Response or compatible)
            pattern: Extraction pattern (string or dict for complex extractors)
            context: Optional execution context for accessing variables

        Returns:
            Extracted value or None
        """
        pass


class ExtractorRegistry:
    """
    Registry for extractor classes.
    
    Maintains a mapping of extractor types (and aliases) to their implementing classes.
    Supports auto-discovery of extractors in the package directory.
    """
    
    _extractors: Dict[str, Type["BaseExtractor"]] = {}
    _discovered: bool = False
    
    @classmethod
    def register(
        cls, 
        extractor_type: str, 
        aliases: Optional[List[str]] = None
    ):
        """
        Decorator to register an extractor class.
        
        Args:
            extractor_type: Primary identifier for the extractor (e.g., 'regex', 'jpath')
            aliases: Optional list of alternative names for the extractor
            
        Returns:
            Decorator function
            
        Example:
            @register_extractor('jpath', aliases=['jsonpath', 'json_path'])
            class JPathExtractor(BaseExtractor):
                ...
        """
        aliases = aliases or []
        
        def decorator(extractor_cls: Type["BaseExtractor"]) -> Type["BaseExtractor"]:
            # Register primary type
            cls._extractors[extractor_type] = extractor_cls
            
            # Register all aliases
            for alias in aliases:
                cls._extractors[alias] = extractor_cls
            
            # Store metadata on the class for introspection
            extractor_cls._extractor_type = extractor_type
            extractor_cls._extractor_aliases = aliases
            
            return extractor_cls
        
        return decorator
    
    @classmethod
    def get(cls, extractor_type: str) -> Type["BaseExtractor"]:
        """
        Get an extractor class by type or alias.
        
        Args:
            extractor_type: The type or alias of the extractor
            
        Returns:
            The extractor class
            
        Raises:
            UnknownExtractorError: If no extractor is registered for the given type
        """
        # Ensure discovery has run
        cls.discover()
        
        if extractor_type not in cls._extractors:
            raise UnknownExtractorError(
                f"Unknown extractor type: '{extractor_type}'. "
                f"Available types: {list(cls.get_registered_types())}"
            )
        return cls._extractors[extractor_type]
    
    @classmethod
    def get_instance(cls, extractor_type: str) -> "BaseExtractor":
        """
        Get an instance of an extractor by type or alias.
        
        Args:
            extractor_type: The type or alias of the extractor
            
        Returns:
            An instance of the extractor class
        """
        extractor_cls = cls.get(extractor_type)
        return extractor_cls()
    
    @classmethod
    def get_registered_types(cls) -> List[str]:
        """
        Get all registered extractor types (excluding aliases).
        
        Returns:
            List of primary extractor type identifiers
        """
        cls.discover()
        
        # Return only primary types, not aliases
        seen = set()
        types = []
        for type_name, extractor_cls in cls._extractors.items():
            if extractor_cls not in seen:
                seen.add(extractor_cls)
                types.append(getattr(extractor_cls, '_extractor_type', type_name))
        return types
    
    @classmethod
    def get_all_names(cls) -> List[str]:
        """
        Get all registered names (types and aliases).
        
        Returns:
            List of all registered identifiers
        """
        cls.discover()
        return list(cls._extractors.keys())
    
    @classmethod
    def discover(cls) -> None:
        """
        Auto-discover and import all extractor modules in the package.
        
        This method imports all Python modules in the extractor package directory,
        triggering their @register_extractor decorators to register them.
        """
        if cls._discovered:
            return
        
        # Get the package directory
        package_dir = Path(__file__).parent
        package_name = "treco.http.extractor"
        
        # Import all modules in the package
        for module_info in pkgutil.iter_modules([str(package_dir)]):
            module_name = module_info.name
            
            # Skip special modules
            if module_name in ('__init__', 'base', 'registry'):
                continue
            
            # Import the module to trigger registration
            full_module_name = f"{package_name}.{module_name}"
            try:
                importlib.import_module(full_module_name)
            except ImportError as e:
                # Log but don't fail - allows graceful degradation
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to import extractor module '{full_module_name}': {e}"
                )
        
        cls._discovered = True
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the registry. Primarily useful for testing.
        """
        cls._extractors.clear()
        cls._discovered = False


class UnknownExtractorError(Exception):
    """Raised when an unknown extractor type is requested."""
    pass


# Convenience function for the decorator
def register_extractor(
    extractor_type: str, 
    aliases: Optional[List[str]] = None
):
    """
    Decorator to register an extractor class.
    
    Args:
        extractor_type: Primary identifier for the extractor
        aliases: Optional list of alternative names
        
    Returns:
        Decorator function
        
    Example:
        @register_extractor('regex', aliases=['re', 'regexp'])
        class RegExExtractor(BaseExtractor):
            ...
    """
    return ExtractorRegistry.register(extractor_type, aliases)