from contextlib import contextmanager
from functools import wraps
import time
from typing import Optional, Callable

class MetricsTimer:
    """Track execution time of operations."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.timings = {}
    
    @contextmanager
    def measure(self, name: str, metadata: Optional[dict] = None):
        """Context manager for timing operations."""
        if not self.enabled:
            yield
            return
        
        start = time.perf_counter()
        error = None
        
        try:
            yield
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration = time.perf_counter() - start
            self._record(name, duration, metadata, error)
    
    def _record(self, name: str, duration: float, metadata: Optional[dict] = None, error: Optional[str] = None):
        """Record timing data."""
        if name not in self.timings:
            self.timings[name] = []
        
        self.timings[name].append({
            'duration_ms': duration * 1000,
            'timestamp': time.time(),
            'metadata': metadata or {},
            'error': error,
        })


def timed(name: Optional[str] = None, metadata: Optional[Callable] = None):
    """Decorator to automatically time function execution."""
    def decorator(func):
        operation_name = name or f"{func.__module__}.{func.__qualname__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            from .registry import MetricsRegistry
            timer = MetricsRegistry.get_timer()
            
            if not timer.enabled:
                return func(*args, **kwargs)
            
            # Extract metadata if callable provided
            meta = metadata(*args, **kwargs) if metadata else None
            
            with timer.measure(operation_name, meta):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator