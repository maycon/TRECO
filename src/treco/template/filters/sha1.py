"""
SHA1 Filter.

Gives the SHA1 hash of the input value.
"""

import hashlib
from typing import Any


def sha1_filter(value: Any) -> str:
    """
    Compute the SHA1 hash of the input value.

    Args:
        value: Input value to hash (will be converted to string)

    Returns:
        SHA1 hash as a hexadecimal string
    """
    # Convert value to string and encode to bytes
    value_str = str(value).encode("utf-8")

    # Compute SHA1 hash
    sha1_hash = hashlib.sha1(value_str).hexdigest()

    return sha1_hash
