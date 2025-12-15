from functools import wraps
from typing import Callable, Optional

class MetricsCounter:
    """Track call counts and frequencies."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.counts = {}
    
    def increment(self, name: str, value: int = 1, labels: Optional[dict] = None):
        """Increment a counter."""
        if not self.enabled:
            return
        
        key = (name, frozenset(labels.items()) if labels else frozenset())
        self.counts[key] = self.counts.get(key, 0) + value


def count_calls(name: Optional[str] = None, labels: Optional[Callable] = None):
    """Decorator to count function calls."""
    def decorator(func):
        counter_name = name or f"{func.__module__}.{func.__qualname__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            from .registry import MetricsRegistry
            counter = MetricsRegistry.get_counter()
            
            if counter.enabled:
                label_dict = labels(*args, **kwargs) if labels else None
                counter.increment(counter_name, labels=label_dict)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator