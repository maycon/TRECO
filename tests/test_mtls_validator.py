"""
Tests for mTLS validation logic in ConfigValidator.
"""

import pytest

from treco.parser.validator import ConfigValidator


class TestMTLSValidation:
    """Test cases for mTLS configuration validation."""

    @pytest.fixture
    def validator(self):
        """Create a ConfigValidator instance."""
        return ConfigValidator()

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

    def test_no_mtls_config(self, validator, valid_config):
        """Test that config without mTLS is valid."""
        validator.validate(valid_config)

    def test_mtls_cert_and_key(self, validator, valid_config):
        """Test that mTLS with cert and key is valid."""
        valid_config["target"]["tls"]["client_cert"] = "/path/to/client.crt"
        valid_config["target"]["tls"]["client_key"] = "/path/to/client.key"
        
        validator.validate(valid_config)

    def test_mtls_cert_and_key_with_password(self, validator, valid_config):
        """Test that mTLS with cert, key, and password is valid."""
        valid_config["target"]["tls"]["client_cert"] = "/path/to/client.crt"
        valid_config["target"]["tls"]["client_key"] = "/path/to/client.key"
        valid_config["target"]["tls"]["client_key_password"] = "secret123"
        
        validator.validate(valid_config)

    def test_mtls_pem_only(self, validator, valid_config):
        """Test that mTLS with PEM file is valid."""
        valid_config["target"]["tls"]["client_pem"] = "/path/to/client.pem"
        
        validator.validate(valid_config)

    def test_mtls_pfx_only(self, validator, valid_config):
        """Test that mTLS with PKCS12 file is valid."""
        valid_config["target"]["tls"]["client_pfx"] = "/path/to/client.pfx"
        
        validator.validate(valid_config)

    def test_mtls_pfx_with_password(self, validator, valid_config):
        """Test that mTLS with PKCS12 file and password is valid."""
        valid_config["target"]["tls"]["client_pfx"] = "/path/to/client.pfx"
        valid_config["target"]["tls"]["client_pfx_password"] = "pfx_password"
        
        validator.validate(valid_config)

    def test_mtls_cert_without_key(self, validator, valid_config):
        """Test that cert without key raises error."""
        valid_config["target"]["tls"]["client_cert"] = "/path/to/client.crt"
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(valid_config)
        
        assert "client_cert" in str(exc_info.value) and "client_key" in str(exc_info.value)

    def test_mtls_key_without_cert(self, validator, valid_config):
        """Test that key without cert raises error."""
        valid_config["target"]["tls"]["client_key"] = "/path/to/client.key"
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(valid_config)
        
        assert "client_cert" in str(exc_info.value) and "client_key" in str(exc_info.value)

    def test_mtls_multiple_formats(self, validator, valid_config):
        """Test that multiple mTLS formats raise error."""
        valid_config["target"]["tls"]["client_cert"] = "/path/to/client.crt"
        valid_config["target"]["tls"]["client_key"] = "/path/to/client.key"
        valid_config["target"]["tls"]["client_pem"] = "/path/to/client.pem"
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(valid_config)
        
        assert "Multiple mTLS certificate formats" in str(exc_info.value)

    def test_mtls_cert_key_and_pfx(self, validator, valid_config):
        """Test that cert+key and pfx together raise error."""
        valid_config["target"]["tls"]["client_cert"] = "/path/to/client.crt"
        valid_config["target"]["tls"]["client_key"] = "/path/to/client.key"
        valid_config["target"]["tls"]["client_pfx"] = "/path/to/client.pfx"
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(valid_config)
        
        assert "Multiple mTLS certificate formats" in str(exc_info.value)

    def test_mtls_pem_and_pfx(self, validator, valid_config):
        """Test that pem and pfx together raise error."""
        valid_config["target"]["tls"]["client_pem"] = "/path/to/client.pem"
        valid_config["target"]["tls"]["client_pfx"] = "/path/to/client.pfx"
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(valid_config)
        
        assert "Multiple mTLS certificate formats" in str(exc_info.value)

    def test_mtls_all_three_formats(self, validator, valid_config):
        """Test that all three formats together raise error."""
        valid_config["target"]["tls"]["client_cert"] = "/path/to/client.crt"
        valid_config["target"]["tls"]["client_key"] = "/path/to/client.key"
        valid_config["target"]["tls"]["client_pem"] = "/path/to/client.pem"
        valid_config["target"]["tls"]["client_pfx"] = "/path/to/client.pfx"
        
        with pytest.raises(ValueError) as exc_info:
            validator.validate(valid_config)
        
        assert "Multiple mTLS certificate formats" in str(exc_info.value)

    def test_mtls_template_support_in_paths(self, validator, valid_config):
        """Test that template expressions in paths are valid."""
        valid_config["target"]["tls"]["client_cert"] = "{{ env('CERT_PATH') }}"
        valid_config["target"]["tls"]["client_key"] = "{{ env('KEY_PATH') }}"
        valid_config["target"]["tls"]["client_key_password"] = "{{ env('KEY_PASSWORD') }}"
        
        # Should not raise validation error (templates are validated at runtime)
        validator.validate(valid_config)

    def test_mtls_password_only_without_cert(self, validator, valid_config):
        """Test that password without cert/key is still valid at validation time."""
        # Password fields alone don't cause validation errors
        valid_config["target"]["tls"]["client_key_password"] = "password"
        
        # Should not raise validation error (semantic checks done at runtime)
        validator.validate(valid_config)
