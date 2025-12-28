from typing import Optional

from .counter import MetricsCounter
from .timer import MetricsTimer

class MetricsRegistry:
    """Central registry for metrics components."""
    
    _timer: Optional['MetricsTimer'] = None
    _counter: Optional['MetricsCounter'] = None
    _enabled: bool = False
    
    @classmethod
    def initialize(cls, enabled: bool = True):
        """Initialize metrics system."""
        from .timer import MetricsTimer
        from .counter import MetricsCounter
        
        cls._enabled = enabled
        cls._timer = MetricsTimer(enabled=enabled)
        cls._counter = MetricsCounter(enabled=enabled)
    
    @classmethod
    def get_timer(cls) -> Optional['MetricsTimer']:
        """Get timer instance."""
        if cls._timer is None:
            cls.initialize(enabled=False)
        return cls._timer
    
    @classmethod
    def get_counter(cls) -> Optional['MetricsCounter']:
        """Get counter instance."""
        if cls._counter is None:
            cls.initialize(enabled=False)
        return cls._counter
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if metrics are enabled."""
        return cls._enabled