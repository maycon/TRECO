"""
Tests for JSON Schema validation.
"""

import pytest

from treco.parser.schema_validator import SchemaValidator, SchemaValidationError


class TestSchemaValidator:
    """Test cases for SchemaValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a SchemaValidator instance."""
        return SchemaValidator()

    @pytest.fixture
    def valid_config(self):
        """Return a valid configuration dictionary."""
        return {
            "metadata": {
                "name": "Test Attack",
                "version": "1.0",
                "author": "Test Author",
                "vulnerability": "CWE-362"
            },
            "target": {
                "host": "example.com",
                "port": 443,
                "threads": 20,
                "tls": {
                    "enabled": True,
                    "verify_cert": True
                }
            },
            "entrypoint": {
                "state": "start",
                "input": {}
            },
            "states": {
                "start": {
                    "description": "Start state",
                    "request": "GET / HTTP/1.1\nHost: example.com\n",
                    "next": [
                        {
                            "on_status": 200,
                            "goto": "end"
                        }
                    ]
                },
                "end": {
                    "description": "End state"
                }
            }
        }

    def test_valid_config_passes(self, validator, valid_config):
        """Test that a valid configuration passes validation."""
        # Should not raise any exception
        validator.validate(valid_config)

    def test_missing_required_field_metadata_name(self, validator, valid_config):
        """Test that missing required field raises error."""
        del valid_config["metadata"]["name"]
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "name" in str(exc_info.value).lower()
        assert "required" in str(exc_info.value).lower()

    def test_missing_required_section(self, validator, valid_config):
        """Test that missing required section raises error."""
        del valid_config["metadata"]
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "metadata" in str(exc_info.value).lower()

    def test_invalid_vulnerability_pattern(self, validator, valid_config):
        """Test that invalid CVE/CWE pattern raises error."""
        valid_config["metadata"]["vulnerability"] = "INVALID-123"
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "vulnerability" in str(exc_info.value).lower()
        assert "does not match" in str(exc_info.value).lower()

    def test_invalid_port_number(self, validator, valid_config):
        """Test that invalid port number raises error."""
        valid_config["target"]["port"] = 70000
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "port" in str(exc_info.value).lower()

    def test_invalid_sync_mechanism(self, validator, valid_config):
        """Test that invalid sync mechanism raises error."""
        valid_config["states"]["start"]["race"] = {
            "threads": 10,
            "sync_mechanism": "invalid_mechanism"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "sync_mechanism" in str(exc_info.value).lower() or "not one of" in str(exc_info.value).lower()

    def test_invalid_connection_strategy(self, validator, valid_config):
        """Test that invalid connection strategy raises error."""
        valid_config["states"]["start"]["race"] = {
            "threads": 10,
            "connection_strategy": "invalid_strategy"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "connection_strategy" in str(exc_info.value).lower() or "not one of" in str(exc_info.value).lower()

    def test_invalid_extractor_type(self, validator, valid_config):
        """Test that invalid extractor type raises error."""
        valid_config["states"]["start"]["extract"] = {
            "token": {
                "type": "invalid_type",
                "pattern": ".*"
            }
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "type" in str(exc_info.value).lower() or "not one of" in str(exc_info.value).lower()

    def test_valid_extractor_shorthand(self, validator, valid_config):
        """Test that extractor shorthand (string) is valid."""
        valid_config["states"]["start"]["extract"] = {
            "token": "regex_pattern"
        }
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_valid_race_config(self, validator, valid_config):
        """Test that valid race configuration passes."""
        valid_config["states"]["start"]["race"] = {
            "threads": 20,
            "sync_mechanism": "barrier",
            "connection_strategy": "preconnect",
            "reuse_connections": False,
            "thread_propagation": "single"
        }
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_validate_with_warnings(self, validator, valid_config):
        """Test that validate_with_warnings returns empty list for valid config."""
        warnings = validator.validate_with_warnings(valid_config)
        assert warnings == []

    def test_validate_with_warnings_returns_errors(self, validator, valid_config):
        """Test that validate_with_warnings returns errors for invalid config."""
        del valid_config["metadata"]["name"]
        
        warnings = validator.validate_with_warnings(valid_config)
        assert len(warnings) > 0
        assert any("name" in w.lower() for w in warnings)

    def test_version_pattern(self, validator, valid_config):
        """Test that version pattern is validated correctly."""
        # Valid versions
        for version in ["1.0", "2.1.0", "10.5.3"]:
            valid_config["metadata"]["version"] = version
            validator.validate(valid_config)
        
        # Invalid version (missing number)
        valid_config["metadata"]["version"] = "invalid"
        with pytest.raises(SchemaValidationError):
            validator.validate(valid_config)

    def test_http_status_code_range(self, validator, valid_config):
        """Test that HTTP status codes are validated."""
        # Valid status code
        valid_config["states"]["start"]["next"][0]["on_status"] = 404
        validator.validate(valid_config)
        
        # Invalid status code
        valid_config["states"]["start"]["next"][0]["on_status"] = 999
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "on_status" in str(exc_info.value).lower() or "maximum" in str(exc_info.value).lower()

    def test_threads_minimum_value(self, validator, valid_config):
        """Test that threads minimum value is enforced."""
        valid_config["target"]["threads"] = 0
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "threads" in str(exc_info.value).lower() or "minimum" in str(exc_info.value).lower()

    def test_race_threads_minimum(self, validator, valid_config):
        """Test that race threads must be at least 2."""
        valid_config["states"]["start"]["race"] = {
            "threads": 1
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "threads" in str(exc_info.value).lower() or "minimum" in str(exc_info.value).lower()

    def test_proxy_configuration(self, validator, valid_config):
        """Test that proxy configuration is validated."""
        valid_config["target"]["proxy"] = {
            "host": "proxy.example.com",
            "port": 8080,
            "type": "http",
            "auth": {
                "username": "user",
                "password": "pass"
            }
        }
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_invalid_proxy_type(self, validator, valid_config):
        """Test that invalid proxy type raises error."""
        valid_config["target"]["proxy"] = {
            "host": "proxy.example.com",
            "port": 8080,
            "type": "invalid_type"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "type" in str(exc_info.value).lower() or "not one of" in str(exc_info.value).lower()

    def test_logger_configuration(self, validator, valid_config):
        """Test that logger configuration is validated."""
        valid_config["states"]["start"]["logger"] = {
            "on_state_enter": "Entering state",
            "on_state_leave": "Leaving state",
            "on_thread_enter": "Thread entering",
            "on_thread_leave": "Thread leaving"
        }
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_state_options(self, validator, valid_config):
        """Test that state options are validated."""
        valid_config["states"]["start"]["options"] = {
            "proxy_bypass": True
        }
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_http_config(self, validator, valid_config):
        """Test that HTTP config is validated."""
        valid_config["target"]["http"] = {
            "follow_redirects": False,
            "timeout": 30
        }
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_invalid_timeout(self, validator, valid_config):
        """Test that invalid timeout raises error."""
        valid_config["target"]["http"] = {
            "timeout": 0
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(valid_config)
        
        assert "timeout" in str(exc_info.value).lower() or "minimum" in str(exc_info.value).lower()

    def test_mtls_client_cert_and_key(self, validator, valid_config):
        """Test that mTLS with separate cert and key is valid."""
        valid_config["target"]["tls"]["client_cert"] = "/path/to/client.crt"
        valid_config["target"]["tls"]["client_key"] = "/path/to/client.key"
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_mtls_client_cert_key_with_password(self, validator, valid_config):
        """Test that mTLS with cert, key, and password is valid."""
        valid_config["target"]["tls"]["client_cert"] = "/path/to/client.crt"
        valid_config["target"]["tls"]["client_key"] = "/path/to/client.key"
        valid_config["target"]["tls"]["client_key_password"] = "{{ env('CLIENT_KEY_PASSWORD') }}"
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_mtls_client_pem(self, validator, valid_config):
        """Test that mTLS with combined PEM file is valid."""
        valid_config["target"]["tls"]["client_pem"] = "/path/to/client.pem"
        
        # Should not raise any exception
        validator.validate(valid_config)

    def test_mtls_client_pfx(self, validator, valid_config):
        """Test that mTLS with PKCS12 file is valid."""
        valid_config["target"]["tls"]["client_pfx"] = "/path/to/client.pfx"
        valid_config["target"]["tls"]["client_pfx_password"] = "{{ env('PFX_PASSWORD') }}"
        
        # Should not raise any exception
        validator.validate(valid_config)
