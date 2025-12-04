"""
Execution context for maintaining state across attack stages.

The ExecutionContext stores variables extracted during the attack flow,
such as authentication tokens, account balances, IDs, etc.
"""

import logging

logger = logging.getLogger(__name__)

from typing import Any, Dict, Optional


class ExecutionContext:
    """
    Runtime context that stores variables shared between states.

    This context maintains:
    - Variables extracted from HTTP responses (bearer_token, fund_balance, etc.)
    - Command-line arguments (argv)
    - Environment variables (env)

    Example:
        context = ExecutionContext(
            argv={"user": "alice", "threads": 20},
            env={"PASSWORD": "alice123"}
        )

        # Set extracted variables
        context.set("bearer_token", "eyJhbGc...")
        context.set("fund_balance", 5000)

        # Read variables
        token = context.get("bearer_token")

        # Template access
        user = context.get_argv("user", "default_user")
        password = context.get_env("PASSWORD", "default_pass")
    """

    def __init__(self, argv: Optional[Dict[str, Any]] = None, env: Optional[Dict[str, str]] = None):
        """
        Initialize the execution context.

        Args:
            argv: Command-line arguments dictionary
            env: Environment variables dictionary
        """
        self._input: Dict[str, Any] = {}
        self._argv = argv or {}
        self._env = env or {}

    def set(self, key: str, value: Any) -> None:
        """
        Store a variable in the context.

        Args:
            key: Variable name
            value: Variable value (can be any type)
        """
        self._input[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a variable from the context.

        Args:
            key: Variable name
            default: Default value if key doesn't exist

        Returns:
            The variable value or default
        """
        return self._input.get(key, default)

    def set_list_item(self, key: str, index: int, value: Any) -> None:
        """
        Set an item in a list variable stored in the context.

        This is used by race attacks to store per-thread results.
        Each thread stores its result at its thread_id index.

        Args:
            key: Variable name (must be a list)
            index: Index to set
            value: Value to set at the index
        """
        # Ensure the key exists and is a list
        # If it doesn't exist or isn't a list, initialize it as an empty list
        if key not in self._input or not isinstance(self._input[key], list):
            self._input[key] = []

        lst = self._input[key]

        # Dynamically grow the list if the index is beyond current size
        # This allows threads to write to their index without coordination
        # Example: Thread 15 writing to index 15 when list only has 10 items
        while len(lst) <= index:
            lst.append(None)

        # Store the value at the specified index
        lst[index] = value

    def get_list_item(self, key: str, index: int, default: Any = None) -> Any:
        """
        Retrieve an item from a list variable stored in the context.

        Args:
            key: Variable name (must be a list)
            index: Index to retrieve
            default: Default value if index doesn't exist
        """
        if key not in self._input or not isinstance(self._input[key], list):
            return default

        lst = self._input[key]

        if index < 0 or index >= len(lst):
            return default

        return lst[index]

    def get_argv(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a command-line argument.

        Args:
            key: Argument name
            default: Default value if argument doesn't exist

        Returns:
            The argument value or default
        """
        return self._argv.get(key, default)

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve an environment variable.

        Args:
            key: Environment variable name
            default: Default value if variable doesn't exist

        Returns:
            The environment variable value or default
        """
        return self._env.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update multiple variables at once.

        Args:
            data: Dictionary of key-value pairs to add to context
        """
        self._input.update(data)

    def setdefault(self, key: str, default: Any) -> Any:
        """
        Set a default value for a variable if it doesn't exist.

        Args:
            key: Variable name
            default: Default value to set

        Returns:
            The existing or default value
        """
        return self._input.setdefault(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export all variables as a dictionary.

        This is useful for template rendering where the entire context
        needs to be passed to Jinja2.

        Returns:
            Dictionary containing all stored variables
        """
        return self._input.copy()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ExecutionContext(input={len(self._input)}, argv={len(self._argv)}, env={len(self._env)})"
