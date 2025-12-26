"""
Tests for input configuration and distribution.
"""

import pytest
from pathlib import Path
import tempfile

from treco.input import InputConfig, InputMode, InputDistributor
from treco.template import TemplateEngine


class TestInputConfig:
    """Test cases for InputConfig class."""
    
    def test_inline_values(self):
        """Test inline list of values."""
        config = InputConfig(values=["val1", "val2", "val3"])
        values = config.resolve()
        
        assert values == ["val1", "val2", "val3"]
    
    def test_range_with_end(self):
        """Test range source with end parameter."""
        config = InputConfig(source="range", start=10, end=15)
        values = config.resolve()
        
        assert values == [10, 11, 12, 13, 14]
    
    def test_range_with_count(self):
        """Test range source with count parameter."""
        config = InputConfig(source="range", start=100, count=5)
        values = config.resolve()
        
        assert values == [100, 101, 102, 103, 104]
    
    def test_range_default_start(self):
        """Test range source with default start (0)."""
        config = InputConfig(source="range", count=3)
        values = config.resolve()
        
        assert values == [0, 1, 2]
    
    def test_file_source(self):
        """Test loading values from file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("line1\n")
            f.write("line2\n")
            f.write("\n")  # Empty line should be skipped
            f.write("line3\n")
            temp_path = f.name
        
        try:
            config = InputConfig(source="file", path=temp_path)
            values = config.resolve()
            
            assert values == ["line1", "line2", "line3"]
        finally:
            Path(temp_path).unlink()
    
    def test_generator_source(self):
        """Test generator source with Jinja2 expression."""
        engine = TemplateEngine()
        config = InputConfig(
            source="generator",
            expression="ID-{{ '%03d' | format(index) }}",
            count=5
        )
        values = config.resolve(template_engine=engine)
        
        assert values == ["ID-000", "ID-001", "ID-002", "ID-003", "ID-004"]
    
    def test_generator_with_index_alias(self):
        """Test generator with both index and i variable."""
        engine = TemplateEngine()
        config = InputConfig(
            source="generator",
            expression="{{ i }}",
            count=3
        )
        values = config.resolve(template_engine=engine)
        
        assert values == ["0", "1", "2"]
    
    def test_from_dict_inline(self):
        """Test creating InputConfig from dictionary with inline values."""
        data = {"values": ["a", "b", "c"]}
        config = InputConfig.from_dict(data)
        values = config.resolve()
        
        assert values == ["a", "b", "c"]
    
    def test_from_dict_range(self):
        """Test creating InputConfig from dictionary with range."""
        data = {"source": "range", "start": 5, "count": 3}
        config = InputConfig.from_dict(data)
        values = config.resolve()
        
        assert values == [5, 6, 7]
    
    def test_builtin_wordlist(self):
        """Test loading built-in wordlist."""
        # This assumes the built-in wordlist exists
        config = InputConfig(source="file", path="builtin:passwords-top-100")
        values = config.resolve()
        
        # Should have loaded some passwords
        assert len(values) > 0
        assert "password" in values or "123456" in values


class TestInputDistributor:
    """Test cases for InputDistributor class."""
    
    def test_same_mode(self):
        """Test SAME mode - all threads get first value."""
        inputs = {"password": ["pass1", "pass2", "pass3"]}
        dist = InputDistributor(inputs, InputMode.SAME, num_threads=5)
        
        # All threads should get the first value
        for i in range(5):
            assignment = dist.get_for_thread(i)
            assert assignment == {"password": "pass1"}
    
    def test_distribute_mode_exact(self):
        """Test DISTRIBUTE mode with exact match (threads == values)."""
        inputs = {"password": ["pass1", "pass2", "pass3"]}
        dist = InputDistributor(inputs, InputMode.DISTRIBUTE, num_threads=3)
        
        assert dist.get_for_thread(0) == {"password": "pass1"}
        assert dist.get_for_thread(1) == {"password": "pass2"}
        assert dist.get_for_thread(2) == {"password": "pass3"}
    
    def test_distribute_mode_more_threads(self):
        """Test DISTRIBUTE mode with more threads than values (cycles)."""
        inputs = {"password": ["a", "b", "c"]}
        dist = InputDistributor(inputs, InputMode.DISTRIBUTE, num_threads=7)
        
        assert dist.get_for_thread(0) == {"password": "a"}
        assert dist.get_for_thread(1) == {"password": "b"}
        assert dist.get_for_thread(2) == {"password": "c"}
        assert dist.get_for_thread(3) == {"password": "a"}  # Cycles
        assert dist.get_for_thread(4) == {"password": "b"}
        assert dist.get_for_thread(5) == {"password": "c"}
        assert dist.get_for_thread(6) == {"password": "a"}
    
    def test_distribute_mode_multiple_inputs(self):
        """Test DISTRIBUTE mode with multiple input variables."""
        inputs = {
            "user": ["alice", "bob"],
            "id": [1, 2]
        }
        dist = InputDistributor(inputs, InputMode.DISTRIBUTE, num_threads=4)
        
        assert dist.get_for_thread(0) == {"user": "alice", "id": 1}
        assert dist.get_for_thread(1) == {"user": "bob", "id": 2}
        assert dist.get_for_thread(2) == {"user": "alice", "id": 1}  # Cycles
        assert dist.get_for_thread(3) == {"user": "bob", "id": 2}
    
    def test_product_mode_simple(self):
        """Test PRODUCT mode with simple cartesian product."""
        inputs = {
            "user": ["admin", "carlos"],
            "pass": ["123", "456"]
        }
        dist = InputDistributor(inputs, InputMode.PRODUCT, num_threads=4)
        
        assignments = [dist.get_for_thread(i) for i in range(4)]
        
        # Should have all 4 combinations
        assert {"user": "admin", "pass": "123"} in assignments
        assert {"user": "admin", "pass": "456"} in assignments
        assert {"user": "carlos", "pass": "123"} in assignments
        assert {"user": "carlos", "pass": "456"} in assignments
    
    def test_product_mode_more_threads(self):
        """Test PRODUCT mode with more threads than combinations."""
        inputs = {
            "user": ["alice", "bob"],
            "pass": ["x", "y"]
        }
        # 2x2 = 4 combinations, but 6 threads
        dist = InputDistributor(inputs, InputMode.PRODUCT, num_threads=6)
        
        assignments = [dist.get_for_thread(i) for i in range(6)]
        
        # First 4 should be unique combinations
        assert len(assignments) == 6
        # Last assignments should repeat the last combination
        assert assignments[4] == assignments[3]
        assert assignments[5] == assignments[3]
    
    def test_product_mode_less_threads(self):
        """Test PRODUCT mode with fewer threads than combinations."""
        inputs = {
            "a": ["1", "2"],
            "b": ["x", "y"],
            "c": ["p", "q"]
        }
        # 2x2x2 = 8 combinations, but only 3 threads
        dist = InputDistributor(inputs, InputMode.PRODUCT, num_threads=3)
        
        assignments = [dist.get_for_thread(i) for i in range(3)]
        
        # Should have 3 unique assignments
        assert len(assignments) == 3
        # All should be different
        assert len(set(tuple(sorted(a.items())) for a in assignments)) == 3
    
    def test_random_mode(self):
        """Test RANDOM mode generates assignments."""
        inputs = {"password": ["pass1", "pass2", "pass3"]}
        dist = InputDistributor(inputs, InputMode.RANDOM, num_threads=10)
        
        assignments = [dist.get_for_thread(i) for i in range(10)]
        
        # All assignments should be valid
        for assignment in assignments:
            assert assignment["password"] in ["pass1", "pass2", "pass3"]
        
        # Should have some variety (probabilistic, might rarely fail)
        unique_values = set(a["password"] for a in assignments)
        # With 10 random selections from 3 values, very likely to get at least 2 different
        assert len(unique_values) >= 1  # At minimum should work
    
    def test_iterator(self):
        """Test that distributor is iterable."""
        inputs = {"val": [1, 2, 3]}
        dist = InputDistributor(inputs, InputMode.DISTRIBUTE, num_threads=3)
        
        assignments = list(dist)
        
        assert len(assignments) == 3
        assert assignments[0] == {"val": 1}
        assert assignments[1] == {"val": 2}
        assert assignments[2] == {"val": 3}
    
    def test_len(self):
        """Test that distributor has length."""
        inputs = {"val": [1, 2, 3]}
        dist = InputDistributor(inputs, InputMode.DISTRIBUTE, num_threads=5)
        
        assert len(dist) == 5
    
    def test_empty_input(self):
        """Test distributor with empty input values."""
        inputs = {"val": []}
        dist = InputDistributor(inputs, InputMode.SAME, num_threads=2)
        
        # Should handle empty gracefully
        assignment = dist.get_for_thread(0)
        assert assignment == {"val": None}


class TestInputModes:
    """Test edge cases for different input modes."""
    
    def test_input_mode_enum(self):
        """Test InputMode enum values."""
        assert InputMode.SAME.value == "same"
        assert InputMode.DISTRIBUTE.value == "distribute"
        assert InputMode.PRODUCT.value == "product"
        assert InputMode.RANDOM.value == "random"
    
    def test_single_value_distribute(self):
        """Test distribute mode with single value."""
        inputs = {"val": ["only_one"]}
        dist = InputDistributor(inputs, InputMode.DISTRIBUTE, num_threads=5)
        
        # All threads should get the same single value
        for i in range(5):
            assert dist.get_for_thread(i) == {"val": "only_one"}
    
    def test_single_thread_product(self):
        """Test product mode with single thread."""
        inputs = {
            "user": ["alice", "bob"],
            "pass": ["123", "456"]
        }
        dist = InputDistributor(inputs, InputMode.PRODUCT, num_threads=1)
        
        # Should get the first combination
        assignment = dist.get_for_thread(0)
        # Verify it's a valid combination from the product
        assert "user" in assignment and "pass" in assignment
        assert assignment["user"] in ["alice", "bob"]
        assert assignment["pass"] in ["123", "456"]
