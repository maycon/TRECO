"""
Custom Jinja2 filters for Treco.

This module contains custom filters for template rendering:
- totp: Generate TOTP tokens
- env: Access environment variables
- argv: Access CLI arguments
"""

from . import totp, env, argv, md5, sha1, average

__all__ = ["totp", "env", "argv", "md5", "sha1", "average"]
