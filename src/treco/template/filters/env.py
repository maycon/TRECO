"""
Environment variable filter.

Provides access to environment variables from templates.
"""

import os
from typing import Optional


def env_filter(var: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read an environment variable.

    This filter allows templates to access environment variables,
    useful for storing sensitive data like passwords outside the config file.

    Args:
        var: Environment variable name
        default: Default value if variable doesn't exist

    Returns:
        Environment variable value or default

    Example in template:
        # With default
        {{ env('PASSWORD', 'default_password') }}

        # Without default (returns None if not set)
        {{ env('API_KEY') }}

        # In JSON request body
        {
          "username": "alice",
          "password": "{{ env('PASSWORD', 'alice123') }}"
        }

    Usage pattern:
        export PASSWORD='my_secret_password'
        python run.py config.yaml

    Note:
        It's recommended to use environment variables for sensitive data
        rather than hardcoding them in YAML files.
    """
    return os.getenv(var, default)
