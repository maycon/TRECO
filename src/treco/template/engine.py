"""
Jinja2 template engine wrapper with custom filters.

Provides a configured Jinja2 environment with custom filters for:
- TOTP generation
- Environment variable access
- CLI argument access
"""

import os
import jinja2
import logging

from typing import Dict, Any, Optional
from treco.models import ExecutionContext

logger = logging.getLogger(__name__)



class TemplateEngine:
    """
    Wrapper around Jinja2 with custom filters for Treco.

    The engine automatically discovers and registers all filters
    from the filters/ directory.

    Custom filters available:
    - totp(seed): Generate TOTP token
    - env(var, default): Read environment variable
    - argv(var, default): Read CLI argument

    Example:
        engine = TemplateEngine()

        # Simple variable interpolation
        result = engine.render(
            "Hello {{ username }}",
            {"username": "alice"}
        )

        # With custom filters
        result = engine.render(
            "Token: {{ totp(seed) }}",
            {"seed": "JBSWY3DPEHPK3PXP"},
            context=execution_context
        )
    """

    def __init__(self):
        """Initialize Jinja2 environment and register custom filters."""
        # Create Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.getcwd()),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Register custom filters
        self._register_filters()

    def _register_filters(self) -> None:
        """
        Auto-discover and register all custom filters.

        Filters are imported from the filters/ directory and registered
        both as filters and as global functions for flexible usage.
        """
        from .filters import totp, env, argv, md5, sha1, sha256, average

        # Register custom filters both as Jinja2 filters AND as global functions
        # This allows two usage patterns:
        #   1. Filter syntax: {{ value | totp }}
        #   2. Function syntax: {{ totp(value) }}
        #
        # Function syntax is more intuitive for users and reads better in templates

        # TOTP (Time-based One-Time Password) for 2FA
        self.env.filters["totp"] = totp.totp_filter
        self.env.globals["totp"] = totp.totp_filter

        # Environment variable access
        self.env.filters["env"] = env.env_filter
        self.env.globals["env"] = env.env_filter

        self.env.filters["md5"] = md5.md5_filter
        self.env.globals["md5"] = md5.md5_filter

        self.env.filters["sha1"] = sha1.sha1_filter
        self.env.globals["sha1"] = sha1.sha1_filter

        self.env.filters["sha256"] = sha256.sha256_filter
        self.env.globals["sha256"] = sha256.sha256_filter

        self.env.filters["average"] = average.average_filter
        self.env.globals["average"] = average.average_filter

        # argv filter needs special handling to access context
        # It's only available as a global function
        self.env.globals["argv"] = argv.argv_filter

    def render(
        self,
        template_str: str,
        variables: Dict[str, Any],
        context: Optional[ExecutionContext] = None,
    ) -> str:
        """
        Render a template string with provided variables.

        Args:
            template_str: Template string with Jinja2 syntax
            variables: Dictionary of variables to interpolate
            context: Optional ExecutionContext for argv/env access

        Returns:
            Rendered string

        Example:
            # Basic rendering
            engine.render("Hello {{ name }}", {"name": "Alice"})
            # Output: "Hello Alice"

            # With TOTP
            engine.render(
                "Code: {{ totp(seed) }}",
                {"seed": "JBSWY3DPEHPK3PXP"}
            )
            # Output: "Code: 123456"

            # With context
            engine.render(
                "User: {{ argv('user', 'default') }}",
                {},
                context=exec_context
            )
            # Output: "User: alice"
        """
        # Create a copy of variables and inject context for argv filter
        render_input = variables.copy()
        if context:
            render_input["_context"] = context

        # Parse and render template
        template = self.env.from_string(template_str)
        return template.render(**render_input)

    def render_dict(
        self,
        data: Dict[str, Any],
        variables: Dict[str, Any],
        context: Optional[ExecutionContext] = None,
    ) -> Dict[str, Any]:
        """
        Recursively render all string values in a dictionary.

        This is useful for rendering entire configuration sections
        where template strings might appear at any level.

        Args:
            data: Dictionary potentially containing template strings
            variables: Variables for template rendering
            context: Optional ExecutionContext

        Returns:
            New dictionary with all templates rendered

        Example:
            data = {
                "username": "{{ user }}",
                "password": "{{ env('PASSWORD', 'default') }}",
                "nested": {
                    "token": "{{ totp(seed) }}"
                }
            }

            result = engine.render_dict(data, {"user": "alice", "seed": "ABC"})
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.render(value, variables, context)
            elif isinstance(value, dict):
                result[key] = self.render_dict(value, variables, context)
            elif isinstance(value, list):
                result[key] = [
                    self.render(item, variables, context) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
