"""
YAML configuration loader.

Loads YAML files and converts them into typed Config objects.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

import logging

from treco.models.config import ExtractPattern, HTTPConfig, ProxyAuth, ProxyConfig, StateOptions
from treco.template.engine import TemplateEngine

from treco.models import (
    Config,
    Metadata,
    TargetConfig,
    TLSConfig,
    Entrypoint,
    State,
    Transition,
    RaceConfig,
    LoggerConfig,
)
from treco.parser.validator import ConfigValidator
from treco.parser.schema_validator import SchemaValidator

logger = logging.getLogger(__name__)


class YAMLLoader:
    """
    Loads and parses YAML configuration files into Config objects.

    The loader performs layered validation:
    1. Reads the YAML file
    2. Schema validation (structure, types, patterns)
    3. Semantic validation (state references, extractor patterns)
    4. Converts dictionaries into dataclasses
    5. Returns a fully-typed Config object

    Example:
        loader = YAMLLoader()
        config = loader.load("configs/attack.yaml")
        logger.info(config.metadata.name)  # "Race Condition PoC - Fund Redemption"
    """

    def __init__(self, enable_schema_validation: bool = True):
        """
        Initialize the YAML loader with validators.
        
        Args:
            enable_schema_validation: Whether to enable JSON Schema validation (default: True)
        """
        self.enable_schema_validation = enable_schema_validation
        self.schema_validator = SchemaValidator() if enable_schema_validation else None
        self.semantic_validator = ConfigValidator()
        self.engine = TemplateEngine()

    def load(self, filepath: str) -> Config:
        """
        Load and parse a YAML configuration file.

        Args:
            filepath: Path to the YAML file

        Returns:
            Parsed Config object

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is malformed
            SchemaValidationError: If schema validation fails
            ValueError: If semantic validation fails
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        # Load raw YAML
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        # Layer 1: Schema validation (structure, types, patterns)
        if self.enable_schema_validation:
            logger.debug("Running schema validation...")
            self.schema_validator.validate(raw_data)
            logger.debug("Schema validation passed")

        # Layer 2: Semantic validation (state references, extractor patterns)
        logger.debug("Running semantic validation...")
        self.semantic_validator.validate(raw_data)
        logger.debug("Semantic validation passed")

        # Convert to typed objects
        return self._build_config(raw_data)

    def _build_config(self, data: Dict[str, Any]) -> Config:
        """
        Convert raw YAML dictionary into Config object.

        Args:
            data: Raw YAML data as dictionary

        Returns:
            Typed Config object
        """

        return Config(
            metadata=self._build_metadata(data["metadata"]),
            target=self._build_target_config(data["target"]),
            entrypoint=self._build_entrypoint(data["entrypoint"]),
            states=self._build_states(data["states"]),
        )

    def _build_metadata(self, data: Dict[str, Any]) -> Metadata:
        """Build Metadata object from dictionary."""
        return Metadata(
            name=data["name"],
            version=data["version"],
            author=data["author"],
            vulnerability=data["vulnerability"],
        )

    def _build_target_config(self, data: Dict[str, Any]) -> TargetConfig:
        """Build ServerConfig object from dictionary."""
        tls_data = data.get("tls", {})
        tls_config = TLSConfig(
            enabled=tls_data.get("enabled", False),
            verify_cert=tls_data.get("verify_cert", False),
            # mTLS fields with template support
            client_cert=self.engine.render(tls_data["client_cert"], {}) if "client_cert" in tls_data else None,
            client_key=self.engine.render(tls_data["client_key"], {}) if "client_key" in tls_data else None,
            client_key_password=self.engine.render(tls_data["client_key_password"], {}) if "client_key_password" in tls_data else None,
            client_pem=self.engine.render(tls_data["client_pem"], {}) if "client_pem" in tls_data else None,
            client_pfx=self.engine.render(tls_data["client_pfx"], {}) if "client_pfx" in tls_data else None,
            client_pfx_password=self.engine.render(tls_data["client_pfx_password"], {}) if "client_pfx_password" in tls_data else None,
        )

        http_data = data.get("http", {})
        http_config = HTTPConfig(
            follow_redirects=http_data.get("follow_redirects", True)
        )

        proxy_data = data.get("proxy", None)
        proxy_config: Optional[ProxyConfig] = None
        if proxy_data:
            proxy_config = ProxyConfig(
                host = proxy_data.get("host", None),
                port = proxy_data.get("port", None),
                type = proxy_data.get("type", "http"),
 
                auth=ProxyAuth(
                    username=self.engine.render(proxy_data["auth"]["username"], {}),
                    password=self.engine.render(proxy_data["auth"]["password"], {}),
                ) if "auth" in proxy_data else None
            )

        return TargetConfig(
            host=self.engine.render(data["host"], {}),
            port=data["port"],
            threads=data.get("threads", 20),
            reuse_connection=data.get("reuse_connection", False),
            tls=tls_config,
            http=http_config,
            proxy=proxy_config,
        )

    def _build_entrypoint_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build input dictionary for Entrypoint."""
        if not data:
            return {}
        
        result: Dict[str, Any] = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.engine.render(value, {})
            elif isinstance(value, dict):
                result[key] = self._build_entrypoint_input(value)
            else:
                result[key] = value  # Keep as is for non-str/dict types

        return result

    def _build_entrypoint(self, entry: dict) -> Entrypoint:
        """Build list of Entrypoint objects from list."""
        return Entrypoint(
                state=entry["state"],
                input=self._build_entrypoint_input(entry.get("input", {})),
            )

    def _build_states(self, data: Dict[str, Any]) -> Dict[str, State]:
        """Build dictionary of State objects."""
        states = {}
        for state_name, state_data in data.items():
            states[state_name] = self._build_state(state_name, state_data)
        return states

    def _build_logger(self, data: Dict[str, Any]):
        """Build Logger object from dictionary."""
        return LoggerConfig(
            on_state_enter=data.get("on_state_enter", ""),
            on_state_leave=data.get("on_state_leave", ""),
            on_thread_enter=data.get("on_thread_enter", ""),
            on_thread_leave=data.get("on_thread_leave", ""),
        )

    def _build_single_extract_pattern(self, data: Any) -> ExtractPattern:
        """Build a single ExtractPattern object from dictionary or string."""
        # Handle both string and dict formats.
        if isinstance(data, str):
            # The default is regex if string.
            return ExtractPattern(pattern_type="regex", pattern_data=data)
        elif isinstance(data, dict):
            # Get the extractor type
            pattern_type = data.get("type", "")
            
            # For JWT and other complex extractors, pass the entire dict as pattern_data
            # For simple extractors, just use the 'pattern' field
            if pattern_type == "jwt":
                # JWT extractor uses the entire config dict
                return ExtractPattern(
                    pattern_type=pattern_type, 
                    pattern_data=data
                )
            else:
                # Simple extractors use just the pattern field
                return ExtractPattern(
                    pattern_type=pattern_type, 
                    pattern_data=data.get("pattern", "")
                )
        else:
            raise ValueError(f"Invalid extract pattern format: {data}")

    def _build_extract_pattern(self, data: Any) -> Any:
        """Build ExtractPattern object from dictionary or string."""

        for variable_name, pattern_data in data.items():
            data[variable_name] = self._build_single_extract_pattern(pattern_data)

        return data

    def _build_state_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build state-level input configuration.
        
        Handles both simple values and complex input configurations with
        source specifications (file, generator, range).
        
        Args:
            data: Raw input configuration from YAML
            
        Returns:
            Processed input configuration dictionary
        """
        if not data:
            return {}
        
        # Keep the raw structure - resolution will happen at runtime
        # This allows for both simple values and complex InputConfig specs
        return data

    def _build_state(self, name: str, data: Dict[str, Any]) -> State:
        """Build a single State object."""
        # Build transitions
        transitions = []
        for trans in data.get("next", []):
            # Check if this is a when block transition
            if "when" in trans:
                transitions.append(
                    Transition(
                        when=trans["when"],
                        goto=trans["goto"],
                        delay_ms=trans.get("delay_ms", 0),
                    )
                )
            # Check if this is an otherwise transition
            elif "otherwise" in trans:
                transitions.append(
                    Transition(
                        otherwise=True,
                        goto=trans["goto"],
                        delay_ms=trans.get("delay_ms", 0),
                    )
                )
            # Legacy on_status transition
            else:
                status = trans.get("on_status", 0)
                status = [status] if isinstance(status, int) else status

                transitions.append(
                    Transition(
                        on_status=status,
                        goto=trans["goto"],
                        delay_ms=trans.get("delay_ms", 0),
                    )
                )

        if "logger" in data:
            logger_config = self._build_logger(data["logger"])
        else:
            logger_config = LoggerConfig()

        state_options: StateOptions = StateOptions()
        if "options" in data:
            options_data = data["options"]
            state_options.proxy_bypass = options_data.get("proxy_bypass", False)

        # Build race config if present
        race_config: Optional[RaceConfig] = None
        if "race" in data:
            race_data = data["race"]
            race_config = RaceConfig(
                threads=race_data.get("threads", 20),
                sync_mechanism=race_data.get("sync_mechanism", "barrier"),
                connection_strategy=race_data.get("connection_strategy", "preconnect"),
                reuse_connections=race_data.get("reuse_connections", False),
                thread_propagation=race_data.get("thread_propagation", "single"),
                input_mode=race_data.get("input_mode", "same"),
            )

        # Build extract patterns
        extracts = self._build_extract_pattern(data.get("extract", {}))
        
        # Build state-level input configuration (if present)
        state_input = self._build_state_input(data.get("input", {}))

        return State(
            name=name,
            description=data.get("description", ""),
            request=data.get("request", ""),
            options=state_options,
            extract=extracts,
            next=transitions,
            logger=logger_config,
            race=race_config,
            input=state_input,
        )
