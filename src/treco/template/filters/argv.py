"""
Command-line argument filter.

Provides access to CLI arguments from templates.
"""

from typing import Any, Optional

from treco.models.context import ExecutionContext


def argv_filter(var: str, default: Optional[Any] = None, **kwargs) -> Optional[Any]:
    """
    Read a command-line argument.

    This filter allows templates to access arguments passed via CLI,
    enabling dynamic configuration without modifying YAML files.

    Args:
        var: Argument name
        default: Default value if argument not provided
        **kwargs: Internal - receives _context from template engine

    Returns:
        CLI argument value or default

    Example in template:
        # Basic usage
        {{ argv('user', 'alice') }}

        # In JSON request body
        {
          "username": "{{ argv('user', 'default_user') }}",
          "threads": {{ argv('threads', 20) }}
        }

    Usage pattern:
        python run.py config.yaml --user alice --threads 50

    Note:
        This filter requires the ExecutionContext to be passed to
        the template engine. The context is automatically injected
        by the engine as '_context'.
    """
    # Extract context from kwargs (injected by template engine)
    context: Optional[ExecutionContext] = kwargs.get("_context")

    if context is None:
        # No context available, return default
        return default

    # Access argv from context
    return context.get_argv(var, default)
