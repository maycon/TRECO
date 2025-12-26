"""
JSON Schema validation for YAML configuration files.

This module provides the first layer of validation - schema validation that
checks structure, types, and basic constraints before runtime validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import best_match

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Validates YAML configuration against JSON Schema.

    This is the first layer of validation that checks:
    - YAML structure and syntax
    - Required fields presence
    - Data types correctness
    - Enum values validity
    - Numeric ranges
    - Pattern matching (e.g., version format, CVE/CWE identifiers)

    Example:
        validator = SchemaValidator()
        validator.validate(yaml_data)  # Raises SchemaValidationError if invalid
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the schema validator.

        Args:
            schema_path: Path to JSON schema file. If None, uses bundled schema.
        """
        if schema_path is None:
            # Use bundled schema
            package_dir = Path(__file__).parent.parent.parent.parent
            schema_path = package_dir / "schema" / "treco-config.schema.json"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate(self, data: Dict[str, Any]) -> None:
        """
        Validate configuration data against JSON Schema.

        Args:
            data: Configuration data to validate

        Raises:
            SchemaValidationError: If validation fails with detailed error message
        """
        try:
            validate(instance=data, schema=self.schema)
            logger.debug("Schema validation passed")
        except ValidationError as e:
            # Find the most specific error
            error = best_match(self.validator.iter_errors(data))
            raise SchemaValidationError.from_validation_error(error) from e

    def validate_with_warnings(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate and return list of all validation errors as warnings.

        Useful for displaying all errors at once instead of failing on first error.

        Args:
            data: Configuration data to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = sorted(self.validator.iter_errors(data), key=lambda e: e.path)
        return [self._format_error(error) for error in errors]

    def _format_error(self, error: ValidationError) -> str:
        """Format a validation error into a human-readable message."""
        path = " -> ".join(str(p) for p in error.absolute_path) if error.path else "root"
        return f"  {path}: {error.message}"


class SchemaValidationError(Exception):
    """
    Exception raised when JSON Schema validation fails.

    Provides detailed error information including:
    - The path to the invalid field
    - The validation error message
    - The invalid value (if applicable)
    """

    def __init__(self, message: str, path: Optional[List[str]] = None, value: Any = None):
        """
        Initialize schema validation error.

        Args:
            message: Error message
            path: Path to the invalid field
            value: The invalid value
        """
        self.message = message
        self.path = path or []
        self.value = value
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with path information."""
        if self.path:
            path_str = " -> ".join(str(p) for p in self.path)
            msg = f"Schema validation failed at '{path_str}': {self.message}"
        else:
            msg = f"Schema validation failed: {self.message}"

        if self.value is not None:
            msg += f"\n  Invalid value: {self.value}"

        return msg

    @classmethod
    def from_validation_error(cls, error: ValidationError) -> "SchemaValidationError":
        """Create SchemaValidationError from jsonschema ValidationError."""
        path = [str(p) for p in error.absolute_path]
        value = error.instance if hasattr(error, "instance") else None

        return cls(
            message=error.message,
            path=path,
            value=value,
        )
