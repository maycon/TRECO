"""
Input configuration for dynamic race attacks.

Defines input sources and configuration for distributing different values
to threads during race condition attacks.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import List, Any, Optional

logger = logging.getLogger(__name__)


class InputSource(Enum):
    """Types of input sources for race attacks."""
    INLINE = "inline"           # Direct list of values
    FILE = "file"               # Load from file
    GENERATOR = "generator"     # Jinja2 expression
    RANGE = "range"             # Numeric range


class InputMode(Enum):
    """Distribution modes for input values across threads."""
    SAME = "same"               # All threads get same value (default)
    DISTRIBUTE = "distribute"   # Round-robin distribution
    PRODUCT = "product"         # Cartesian product
    RANDOM = "random"           # Random selection


class InputConfig:
    """
    Configuration for a single input source.
    
    Supports multiple input types:
    - Inline list: Direct list of values
    - File: Load values from file (one per line)
    - Generator: Generate values using Jinja2 expression
    - Range: Generate numeric range
    
    Examples:
        # Inline list
        config = InputConfig(values=["val1", "val2", "val3"])
        
        # File source
        config = InputConfig(source="file", path="wordlist.txt")
        
        # Generator
        config = InputConfig(
            source="generator",
            expression="ID-{{ '%03d' | format(index) }}",
            count=100
        )
        
        # Range
        config = InputConfig(source="range", start=1, count=100)
    """
    
    def __init__(
        self,
        values: Optional[List[Any]] = None,
        source: Optional[str] = None,
        path: Optional[str] = None,
        expression: Optional[str] = None,
        count: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ):
        """
        Initialize input configuration.
        
        Args:
            values: Direct list of values (inline mode)
            source: Source type ("file", "generator", "range")
            path: File path for file source
            expression: Jinja2 expression for generator source
            count: Number of values to generate
            start: Start value for range source
            end: End value for range source (exclusive)
        """
        self.values = values
        self.source = source
        self.path = path
        self.expression = expression
        self.count = count
        self.start = start
        self.end = end
    
    def resolve(self, template_engine=None) -> List[Any]:
        """
        Resolve input configuration to list of values.
        
        Args:
            template_engine: Template engine for generator source
            
        Returns:
            List of resolved values
            
        Raises:
            FileNotFoundError: If file source path doesn't exist
            ValueError: If configuration is invalid
        """
        # Inline list
        if self.values is not None:
            logger.debug(f"Resolving inline values: {len(self.values)} items")
            return self.values
        
        # File source
        if self.source == "file":
            return self._load_file()
        
        # Generator source
        if self.source == "generator":
            if template_engine is None:
                raise ValueError("Template engine required for generator source")
            return self._generate_values(template_engine)
        
        # Range source
        if self.source == "range":
            return self._generate_range()
        
        logger.warning("No input source configured, returning empty list")
        return []
    
    def _load_file(self) -> List[str]:
        """
        Load values from file, one per line.
        
        Returns:
            List of lines from file (stripped)
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not self.path:
            raise ValueError("File source requires 'path' parameter")
        
        path = Path(self.path)
        
        # Handle built-in wordlists
        if self.path.startswith("builtin:"):
            builtin_name = self.path.split(":", 1)[1]
            # Look in the wordlists directory relative to this module
            wordlists_dir = Path(__file__).parent.parent / "wordlists"
            path = wordlists_dir / f"{builtin_name}.txt"
            logger.debug(f"Using built-in wordlist: {path}")
        
        if not path.exists():
            raise FileNotFoundError(f"Wordlist not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            values = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(values)} values from {path}")
        return values
    
    def _generate_values(self, template_engine) -> List[Any]:
        """
        Generate values using Jinja2 expression.
        
        Args:
            template_engine: Template engine for rendering
            
        Returns:
            List of generated values
        """
        if not self.expression:
            raise ValueError("Generator source requires 'expression' parameter")
        
        count = self.count or 100
        values = []
        
        for i in range(count):
            context = {"index": i, "i": i}
            try:
                value = template_engine.render(self.expression, context)
                values.append(value)
            except Exception as e:
                logger.error(f"Failed to generate value at index {i}: {e}")
                raise
        
        logger.info(f"Generated {len(values)} values using expression")
        return values
    
    def _generate_range(self) -> List[int]:
        """
        Generate numeric range.
        
        Returns:
            List of integers in range
        """
        start_val = self.start or 0
        
        if self.end is not None:
            values = list(range(start_val, self.end))
        elif self.count is not None:
            values = list(range(start_val, start_val + self.count))
        else:
            raise ValueError("Range source requires either 'end' or 'count' parameter")
        
        logger.info(f"Generated range: {len(values)} values from {start_val}")
        return values
    
    @classmethod
    def from_dict(cls, data: dict) -> "InputConfig":
        """
        Create InputConfig from dictionary.
        
        Args:
            data: Dictionary with configuration
            
        Returns:
            InputConfig instance
        """
        return cls(
            values=data.get("values"),
            source=data.get("source"),
            path=data.get("path"),
            expression=data.get("expression"),
            count=data.get("count"),
            start=data.get("start"),
            end=data.get("end"),
        )
