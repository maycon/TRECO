"""
MD5 Filter.

Gives the MD5 hash of the input value.
"""

import hashlib
from typing import Any


def md5_filter(value: Any) -> str:
    """
    Compute the MD5 hash of the input value.

    Args:
        value: Input value to hash (will be converted to string)

    Returns:
        MD5 hash as a hexadecimal string
    """
    # Convert value to string and encode to bytes
    value_str = str(value).encode("utf-8")

    # Compute MD5 hash
    md5_hash = hashlib.md5(value_str).hexdigest()

    return md5_hash
