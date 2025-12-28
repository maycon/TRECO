"""
Input distributor for race condition attacks.

Distributes input values across threads according to configured mode.
"""

import random
import logging
from itertools import cycle, product
from typing import Dict, List, Any, Iterator

from treco.input.config import InputMode

logger = logging.getLogger(__name__)


class InputDistributor:
    """
    Distributes input values to threads based on configured mode.
    
    Supports multiple distribution strategies:
    - SAME: All threads get the same value (backward compatible)
    - DISTRIBUTE: Round-robin distribution across threads
    - PRODUCT: Cartesian product of all inputs
    - RANDOM: Random value per thread
    
    Examples:
        # Distribute mode
        inputs = {"password": ["pass1", "pass2", "pass3"]}
        dist = InputDistributor(inputs, InputMode.DISTRIBUTE, num_threads=6)
        
        # Thread 0 gets password="pass1"
        # Thread 1 gets password="pass2"
        # Thread 2 gets password="pass3"
        # Thread 3 gets password="pass1" (cycles)
        # ...
        
        # Product mode
        inputs = {"user": ["admin", "carlos"], "pass": ["123", "456"]}
        dist = InputDistributor(inputs, InputMode.PRODUCT, num_threads=4)
        
        # Thread 0: user="admin", pass="123"
        # Thread 1: user="admin", pass="456"
        # Thread 2: user="carlos", pass="123"
        # Thread 3: user="carlos", pass="456"
    """
    
    def __init__(
        self,
        inputs: Dict[str, List[Any]],
        mode: InputMode,
        num_threads: int,
    ):
        """
        Initialize input distributor.
        
        Args:
            inputs: Dictionary mapping input names to lists of values
            mode: Distribution mode (SAME, DISTRIBUTE, PRODUCT, RANDOM)
            num_threads: Number of threads to distribute to
        """
        self.inputs = inputs
        self.mode = mode
        self.num_threads = num_threads
        self._assignments = self._compute_assignments()
        
        logger.info(
            f"Input distributor initialized: mode={mode.value}, "
            f"threads={num_threads}, inputs={list(inputs.keys())}"
        )
    
    def _compute_assignments(self) -> List[Dict[str, Any]]:
        """
        Pre-compute input assignments for all threads.
        
        Returns:
            List of dictionaries, one per thread with input assignments
        """
        if self.mode == InputMode.SAME:
            return self._assign_same()
        elif self.mode == InputMode.DISTRIBUTE:
            return self._assign_distribute()
        elif self.mode == InputMode.PRODUCT:
            return self._assign_product()
        elif self.mode == InputMode.RANDOM:
            return self._assign_random()
        else:
            logger.warning(f"Unknown input mode: {self.mode}, defaulting to SAME")
            return self._assign_same()
    
    def _assign_same(self) -> List[Dict[str, Any]]:
        """
        All threads get first value of each input (backward compatible).
        
        Returns:
            List of identical assignments for each thread
        """
        base = {k: v[0] if v else None for k, v in self.inputs.items()}
        assignments = [base.copy() for _ in range(self.num_threads)]
        
        logger.debug(f"SAME mode: All {self.num_threads} threads get {base}")
        return assignments
    
    def _assign_distribute(self) -> List[Dict[str, Any]]:
        """
        Round-robin distribution of values across threads.
        
        If there are more threads than values, cycles through values.
        If there are more values than threads, uses only first N values.
        
        Returns:
            List of assignments with round-robin distribution
        """
        assignments = []
        cycles = {k: cycle(v) for k, v in self.inputs.items()}
        
        for i in range(self.num_threads):
            assignment = {k: next(c) for k, c in cycles.items()}
            assignments.append(assignment)
        
        logger.debug(
            f"DISTRIBUTE mode: {self.num_threads} threads, "
            f"{', '.join(f'{k}={len(v) if isinstance(v, list) else 1}' for k, v in self.inputs.items())}"
        )
        return assignments
    
    def _assign_product(self) -> List[Dict[str, Any]]:
        """
        Cartesian product of all inputs.
        
        Generates all possible combinations. If there are more combinations
        than threads, uses only first N combinations. If there are more
        threads than combinations, repeats the last combination.
        
        Returns:
            List of assignments with cartesian product
        """
        keys = list(self.inputs.keys())
        values = [self.inputs[k] for k in keys]
        
        assignments = []
        for combo in product(*values):
            assignments.append(dict(zip(keys, combo)))
            if len(assignments) >= self.num_threads:
                break
        
        # Pad if needed (more threads than combinations)
        while len(assignments) < self.num_threads:
            assignments.append(assignments[-1].copy())
        
        logger.debug(
            f"PRODUCT mode: Generated {len(assignments)} combinations "
            f"for {self.num_threads} threads"
        )
        return assignments
    
    def _assign_random(self) -> List[Dict[str, Any]]:
        """
        Random selection for each thread.
        
        Each thread gets a random value from each input list.
        
        Returns:
            List of assignments with random values
        """
        assignments = []
        for i in range(self.num_threads):
            assignment = {
                k: random.choice(v) if v else None
                for k, v in self.inputs.items()
            }
            assignments.append(assignment)
        
        logger.debug(f"RANDOM mode: Generated random values for {self.num_threads} threads")
        return assignments
    
    def get_for_thread(self, thread_id: int) -> Dict[str, Any]:
        """
        Get input values for a specific thread.
        
        Args:
            thread_id: Thread identifier (0-based)
            
        Returns:
            Dictionary of input name -> value for this thread
        """
        return self._assignments[thread_id % len(self._assignments)]
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate over all thread assignments.
        
        Yields:
            Dictionary of input values for each thread
        """
        return iter(self._assignments)
    
    def __len__(self) -> int:
        """Get number of thread assignments."""
        return len(self._assignments)
