"""
Tests for thread groups in race conditions.
"""

import pytest
from treco.models.config import RaceConfig, ThreadGroup
from treco.parser.loaders.yaml import YAMLLoader
import tempfile
import os


class TestThreadGroupModel:
    """Test cases for ThreadGroup dataclass."""
    
    def test_thread_group_creation(self):
        """Test creating a ThreadGroup with all parameters."""
        group = ThreadGroup(
            name="test_group",
            threads=10,
            delay_ms=50,
            request="GET /test HTTP/1.1\nHost: example.com",
            variables={"var1": "value1"}
        )
        
        assert group.name == "test_group"
        assert group.threads == 10
        assert group.delay_ms == 50
        assert "GET /test" in group.request
        assert group.variables["var1"] == "value1"
    
    def test_thread_group_defaults(self):
        """Test ThreadGroup default values."""
        group = ThreadGroup(
            name="minimal",
            threads=5
        )
        
        assert group.name == "minimal"
        assert group.threads == 5
        assert group.delay_ms == 0
        assert group.request == ""
        assert group.variables == {}


class TestRaceConfigWithThreadGroups:
    """Test cases for RaceConfig with thread_groups."""
    
    def test_race_config_with_thread_groups(self):
        """Test RaceConfig with thread_groups field."""
        groups = [
            ThreadGroup(name="group1", threads=5, delay_ms=0, request="GET /1 HTTP/1.1"),
            ThreadGroup(name="group2", threads=10, delay_ms=20, request="GET /2 HTTP/1.1")
        ]
        
        config = RaceConfig(
            threads=20,  # Legacy field still exists
            sync_mechanism="barrier",
            connection_strategy="multiplexed",
            thread_groups=groups
        )
        
        assert config.thread_groups is not None
        assert len(config.thread_groups) == 2
        assert config.thread_groups[0].name == "group1"
        assert config.thread_groups[1].threads == 10
    
    def test_race_config_backward_compatibility(self):
        """Test RaceConfig works without thread_groups (legacy mode)."""
        config = RaceConfig(
            threads=30,
            sync_mechanism="barrier",
            connection_strategy="preconnect"
        )
        
        assert config.threads == 30
        assert config.thread_groups is None


class TestYAMLParserThreadGroups:
    """Test cases for YAML parser with thread groups."""
    
    def test_parse_thread_groups_yaml(self):
        """Test parsing YAML with thread_groups configuration."""
        yaml_content = """
metadata:
  name: "Test"
  version: "1.0"
  author: "Test"
  vulnerability: "CWE-362"

target:
  host: "example.com"
  port: 443

entrypoint:
  state: test_state

states:
  test_state:
    description: "Test state"
    request: ""
    race:
      sync_mechanism: barrier
      connection_strategy: multiplexed
      thread_groups:
        - name: group1
          threads: 5
          delay_ms: 0
          request: |
            GET /test1 HTTP/1.1
            Host: example.com
          variables:
            key1: value1
        
        - name: group2
          threads: 10
          delay_ms: 100
          request: |
            POST /test2 HTTP/1.1
            Host: example.com
          variables:
            key2: value2
    next:
      - goto: end
  
  end:
    description: "End"
"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            loader = YAMLLoader()
            config = loader.load(temp_path)
            
            # Check that config loaded
            assert config.metadata.name == "Test"
            
            # Check thread groups
            state = config.states["test_state"]
            assert state.race is not None
            assert state.race.thread_groups is not None
            assert len(state.race.thread_groups) == 2
            
            # Check group 1
            group1 = state.race.thread_groups[0]
            assert group1.name == "group1"
            assert group1.threads == 5
            assert group1.delay_ms == 0
            assert "GET /test1" in group1.request
            assert group1.variables["key1"] == "value1"
            
            # Check group 2
            group2 = state.race.thread_groups[1]
            assert group2.name == "group2"
            assert group2.threads == 10
            assert group2.delay_ms == 100
            assert "POST /test2" in group2.request
            assert group2.variables["key2"] == "value2"
            
        finally:
            os.unlink(temp_path)
    
    def test_parse_legacy_race_yaml(self):
        """Test parsing legacy YAML without thread_groups."""
        yaml_content = """
metadata:
  name: "Legacy Test"
  version: "1.0"
  author: "Test"
  vulnerability: "CWE-362"

target:
  host: "example.com"
  port: 443

entrypoint:
  state: test_state

states:
  test_state:
    description: "Test state"
    request: |
      GET /test HTTP/1.1
      Host: example.com
    race:
      threads: 20
      sync_mechanism: barrier
      connection_strategy: preconnect
    next:
      - goto: end
  
  end:
    description: "End"
"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            loader = YAMLLoader()
            config = loader.load(temp_path)
            
            # Check that config loaded
            assert config.metadata.name == "Legacy Test"
            
            # Check legacy race config
            state = config.states["test_state"]
            assert state.race is not None
            assert state.race.threads == 20
            assert state.race.sync_mechanism == "barrier"
            assert state.race.thread_groups is None  # Should be None for legacy
            
        finally:
            os.unlink(temp_path)
    
    def test_thread_groups_total_threads_calculation(self):
        """Test that we can calculate total threads from groups."""
        yaml_content = """
metadata:
  name: "Test"
  version: "1.0"
  author: "Test"
  vulnerability: "CWE-362"

target:
  host: "example.com"
  port: 443

entrypoint:
  state: test_state

states:
  test_state:
    description: "Test"
    request: ""
    race:
      thread_groups:
        - name: g1
          threads: 3
          request: "GET /1 HTTP/1.1"
        - name: g2
          threads: 7
          request: "GET /2 HTTP/1.1"
        - name: g3
          threads: 10
          request: "GET /3 HTTP/1.1"
    next:
      - goto: end
  
  end:
    description: "End"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            loader = YAMLLoader()
            config = loader.load(temp_path)
            
            state = config.states["test_state"]
            groups = state.race.thread_groups
            
            # Calculate total threads
            total = sum(g.threads for g in groups)
            assert total == 20  # 3 + 7 + 10
            
        finally:
            os.unlink(temp_path)


class TestThreadGroupContext:
    """Test cases for thread group context variables."""
    
    def test_group_variables(self):
        """Test that group variables can be accessed."""
        group = ThreadGroup(
            name="test",
            threads=5,
            request="GET /test HTTP/1.1",
            variables={
                "api_key": "secret123",
                "endpoint": "/api/v1"
            }
        )
        
        assert "api_key" in group.variables
        assert group.variables["api_key"] == "secret123"
        assert group.variables["endpoint"] == "/api/v1"
