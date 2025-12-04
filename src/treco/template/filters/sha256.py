"""
SHA256 Filter.

Gives the SHA256 hash of the input value.
"""

import hashlib
from typing import Any


def sha256_filter(value: Any) -> str:
    """
    Compute the SHA256 hash of the input value.

    Args:
        value: Input value to hash (will be converted to string)

    Returns:
        SHA256 hash as a hexadecimal string
    """
    # Convert value to string and encode to bytes
    value_str = str(value).encode("utf-8")

    # Compute SHA256 hash
    sha256_hash = hashlib.sha256(value_str).hexdigest()

    return sha256_hash
