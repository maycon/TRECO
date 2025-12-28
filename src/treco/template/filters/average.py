"""
Average Filter

Computes the average of a list of numeric values.
"""

def average_filter(iterable, attribute=None) -> float:
    """
    Compute the average of a list of numeric values.

    Args:
        value: List of numeric values

    Returns:
        Average as a float. Returns 0.0 for empty lists.

    Raises:
        ValueError: If input is not a list or contains non-numeric values.
    """
    if attribute:
        values = [
            getattr(item, attribute, None) or item.get(attribute)
            for item in iterable
        ]
    else:
        values = iterable

    if not values:
        return 0.0

    return sum(values) / len(values)
