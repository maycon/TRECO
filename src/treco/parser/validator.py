"""
Configuration validator.

Validates YAML structure, required fields, and references.
"""

from typing import Dict, Any, Set

from treco.http.extractor import get_extractor, ExtractorRegistry
from treco.models.config import Entrypoint


class ConfigValidator:
    """
    Validates YAML configuration structure and semantics.

    Performs checks for:
    - Required fields presence
    - Correct data types
    - Valid state references
    - Valid sync mechanisms and connection strategies
    - Proper transition definitions

    Example:
        validator = ConfigValidator()
        validator.validate(yaml_data)  # Raises ValueError if invalid
    """

    VALID_SYNC_MECHANISMS = {"barrier", "countdown_latch", "semaphore"}
    VALID_CONNECTION_STRATEGIES = {"preconnect", "lazy", "pooled", "multiplexed"}
    VALID_THREAD_PROPAGATIONS = {"single", "parallel"}

    def validate(self, data: Dict[str, Any]) -> None:
        """
        Validate the entire configuration.

        Args:
            data: Raw YAML data as dictionary

        Raises:
            ValueError: If validation fails
        """
        self._check_required_sections(data)
        self._validate_metadata(data["metadata"])
        self._validate_target(data["target"])
        self._validate_entrypoint(data["entrypoint"], data["states"])
        self._validate_states(data["states"])

    def _check_required_sections(self, data: Dict[str, Any]) -> None:
        """Check that all required top-level sections exist."""
        required = ["metadata", "target", "entrypoint", "states"]
        for section in required:
            if section not in data:
                raise ValueError(f"Missing required section: {section}")

    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate metadata section."""
        required_fields = ["name", "version", "author", "vulnerability"]
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")

    def _validate_target(self, config: Dict[str, Any]) -> None:
        """Validate config section."""
        # Required fields
        if "host" not in config:
            raise ValueError("Missing required config field: host")
        if "port" not in config:
            raise ValueError("Missing required config field: port")

        # Validate port is numeric
        if not isinstance(config["port"], int):
            raise ValueError(f"Port must be an integer, got: {type(config['port'])}")

        # Validate threads if present
        if "threads" in config and not isinstance(config["threads"], int):
            raise ValueError(f"Threads must be an integer, got: {type(config['threads'])}")

        # Validate TLS config if present
        if "tls" in config:
            tls = config["tls"]
            if "enabled" in tls and not isinstance(tls["enabled"], bool):
                raise ValueError(f"TLS enabled must be boolean, got: {type(tls['enabled'])}")

    def _validate_entrypoint(self, entrypoint: dict, states: Dict[str, Any]) -> None:
        """Validate entrypoint section."""
        if not entrypoint:
            raise ValueError("At least one entrypoint is required")

        if not "state" in entrypoint:
            raise ValueError(f"Entrypoint missing 'state' field")

        # Check that referenced state exists
        if entrypoint["state"] not in states:
            raise ValueError(f"Entrypoint references non-existent state: {entrypoint["state"]}")

    def _validate_states(self, states: Dict[str, Any]) -> None:
        """Validate states section."""
        if not states:
            raise ValueError("At least one state is required")

        # Collect all state names for reference checking
        state_names: Set[str] = set(states.keys())

        # Validate each state
        for state_name, state_data in states.items():
            self._validate_state(state_name, state_data, state_names)

    def _validate_state(self, name: str, data: Dict[str, Any], all_states: Set[str]) -> None:
        """
        Validate a single state.

        Args:
            name: State name
            data: State data dictionary
            all_states: Set of all valid state names for reference checking
        """
        # Description is optional but recommended
        if "description" not in data:
            # Not an error, just a warning we could log
            pass

        # Request is required for non-terminal states
        # if name not in ["end", "error"] and "request" not in data:
        #     raise ValueError(f"State '{name}' missing required field: request")

        if "options" in data:
            self._validate_state_options(name, data["options"])

        # Validate transitions
        if "next" in data:
            for idx, transition in enumerate(data["next"]):
                self._validate_transition(name, idx, transition, all_states)

        # Validate race config if present
        if "race" in data:
            self._validate_race_config(name, data["race"])

        # Validate extractor patterns if present
        if "extract" in data:
            self._validate_extractor_patterns(name, data["extract"])

    def _validate_state_options(self, state_name: str, options: Dict[str, Any]) -> None:
        """Validate state options."""
        if "proxy_bypass" in options:
            proxy_bypass = options["proxy_bypass"]
            if not isinstance(proxy_bypass, bool):
                raise ValueError(
                    f"State '{state_name}' option 'proxy_bypass' must be boolean, got: {type(proxy_bypass)}"
                )

    def _validate_transition(
        self, state_name: str, idx: int, transition: Dict[str, Any], all_states: Set[str]
    ) -> None:
        """Validate a state transition."""
        if "goto" not in transition:
            raise ValueError(f"State '{state_name}' transition {idx} missing 'goto' field")

        target_state = transition["goto"]
        if target_state not in all_states:
            raise ValueError(
                f"State '{state_name}' transition {idx} references non-existent state: {target_state}"
            )
        
        # Check if this is a when block transition
        if "when" in transition:
            self._validate_when_block(state_name, idx, transition["when"])
        # Check if this is an otherwise transition
        elif "otherwise" in transition:
            # Allow None, True, or boolean values (YAML "- otherwise:" parses as None)
            if transition["otherwise"] is not None and not isinstance(transition["otherwise"], bool):
                raise ValueError(
                    f"State '{state_name}' transition {idx} has invalid otherwise value: must be boolean or null"
                )
        # Legacy on_status transition
        elif "on_status" in transition:
            status = transition["on_status"]
            if isinstance(status, int):
                status = [status]

            for s in status:
                if not isinstance(s, int) or s < 0:
                    raise ValueError(
                        f"State '{state_name}' transition {idx} has invalid on_status: {s}"
                    )
        # No condition specified - this is valid for backward compatibility (matches any status)
    
    def _validate_when_block(self, state_name: str, transition_idx: int, when_conditions: list) -> None:
        """
        Validate when block conditions.
        
        Args:
            state_name: Name of the state
            transition_idx: Index of the transition
            when_conditions: List of condition dictionaries
        """
        if not isinstance(when_conditions, list):
            raise ValueError(
                f"State '{state_name}' transition {transition_idx} 'when' must be a list"
            )
        
        if len(when_conditions) == 0:
            raise ValueError(
                f"State '{state_name}' transition {transition_idx} 'when' block cannot be empty"
            )
        
        # Validate each condition in the when block
        for cond_idx, condition in enumerate(when_conditions):
            if not isinstance(condition, dict):
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {cond_idx} must be a dictionary"
                )
            
            self._validate_single_condition(state_name, transition_idx, cond_idx, condition)
    
    def _validate_single_condition(
        self, state_name: str, transition_idx: int, condition_idx: int, condition: Dict[str, Any]
    ) -> None:
        """Validate a single condition within a when block."""
        valid_condition_keys = {
            "status", "status_in", "status_range",
            "condition",
            "body_contains", "body_not_contains", "body_matches", "body_equals",
            "header_exists", "header_not_exists", "header_equals", 
            "header_contains", "header_matches", "header_compare",
            "response_time_ms"
        }
        
        # Check that at least one valid condition key is present
        condition_keys = set(condition.keys())
        matching_keys = condition_keys & valid_condition_keys
        
        if not matching_keys:
            raise ValueError(
                f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                f"has no valid condition type. Valid types: {valid_condition_keys}"
            )
        
        # Validate specific condition types
        if "status" in condition:
            if not isinstance(condition["status"], int) or condition["status"] < 0:
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"has invalid status: must be non-negative integer"
                )
        
        if "status_in" in condition:
            if not isinstance(condition["status_in"], list):
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"status_in must be a list"
                )
            for s in condition["status_in"]:
                if not isinstance(s, int) or s < 0:
                    raise ValueError(
                        f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                        f"has invalid status in status_in: {s}"
                    )
        
        if "status_range" in condition:
            if not isinstance(condition["status_range"], list) or len(condition["status_range"]) != 2:
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"status_range must be a list of exactly 2 integers [low, high]"
                )
            low, high = condition["status_range"]
            if not isinstance(low, int) or not isinstance(high, int) or low < 0 or high < 0:
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"status_range values must be non-negative integers"
                )
            if low > high:
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"status_range low value must be <= high value"
                )
        
        if "condition" in condition:
            if not isinstance(condition["condition"], str):
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"'condition' must be a string (Jinja2 expression)"
                )
        
        # Validate header-based conditions that require dict structure
        for key in ["header_equals", "header_contains", "header_matches"]:
            if key in condition:
                if not isinstance(condition[key], dict):
                    raise ValueError(
                        f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                        f"'{key}' must be a dictionary with 'name' and 'value'/'pattern' keys"
                    )
                if "name" not in condition[key]:
                    raise ValueError(
                        f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                        f"'{key}' must have 'name' key"
                    )
        
        if "header_compare" in condition:
            if not isinstance(condition["header_compare"], dict):
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"'header_compare' must be a dictionary"
                )
            required_keys = ["name", "operator", "value"]
            for key in required_keys:
                if key not in condition["header_compare"]:
                    raise ValueError(
                        f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                        f"'header_compare' missing required key: {key}"
                    )
            
            valid_operators = ["<", "<=", ">", ">=", "==", "!="]
            if condition["header_compare"]["operator"] not in valid_operators:
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"'header_compare' has invalid operator. Valid: {valid_operators}"
                )
        
        if "response_time_ms" in condition:
            if not isinstance(condition["response_time_ms"], dict):
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"'response_time_ms' must be a dictionary with 'operator' and 'value'"
                )
            if "operator" not in condition["response_time_ms"] or "value" not in condition["response_time_ms"]:
                raise ValueError(
                    f"State '{state_name}' transition {transition_idx} condition {condition_idx} "
                    f"'response_time_ms' must have 'operator' and 'value' keys"
                )



    def _validate_race_config(self, state_name: str, race: Dict[str, Any]) -> None:
        """
        Validate race configuration.

        Args:
            state_name: Name of the state
            race: Race configuration dictionary
        """
        # Validate sync mechanism
        if "sync_mechanism" in race:
            mechanism = race["sync_mechanism"]
            if mechanism not in self.VALID_SYNC_MECHANISMS:
                raise ValueError(
                    f"State '{state_name}' has invalid sync_mechanism: {mechanism}. "
                    f"Valid options: {self.VALID_SYNC_MECHANISMS}"
                )

        # Validate connection strategy
        if "connection_strategy" in race:
            strategy = race["connection_strategy"]
            if strategy not in self.VALID_CONNECTION_STRATEGIES:
                raise ValueError(
                    f"State '{state_name}' has invalid connection_strategy: {strategy}. "
                    f"Valid options: {self.VALID_CONNECTION_STRATEGIES}"
                )

        # Validate thread propagation
        if "thread_propagation" in race:
            propagation = race["thread_propagation"]
            if propagation not in self.VALID_THREAD_PROPAGATIONS:
                raise ValueError(
                    f"State '{state_name}' has invalid thread_propagation: {propagation}. "
                    f"Valid options: {self.VALID_THREAD_PROPAGATIONS}"
                )

        # Validate threads count
        if "threads" in race:
            threads = race["threads"]
            if not isinstance(threads, int) or threads < 1:
                raise ValueError(
                    f"State '{state_name}' has invalid threads count: {threads}. "
                    "Must be positive integer."
                )

    def _validate_extractor_patterns(self, state_name: str, extracts: Dict[str, Any]) -> None:
        """
        Validate extractor patterns in a state.

        Args:
            state_name: Name of the state
            extracts: Dictionary of variable_name -> extract pattern

        Raises:
            ValueError: If any extractor pattern is invalid

        Returns:
            None
        """
        for var_name, pattern in extracts.items():
            if isinstance(pattern, str):
                # Simple string pattern is allowed (defaults to regex)
                continue

            if not isinstance(pattern, dict):
                raise ValueError(
                    f"State '{state_name}' extractor for variable '{var_name}' "
                    "must be a string or a dictionary."
                )

            if "pattern" not in pattern:
                raise ValueError(
                    f"State '{state_name}' extractor for variable '{var_name}' "
                    "must have 'pattern' fields."
                )

            # Validate pattern_type
            pattern_type = pattern.get("type", "regex")

            if not get_extractor(pattern_type):
                raise ValueError(
                    f"State '{state_name}' extractor for variable '{var_name}' "
                    f"has invalid pattern type: {pattern_type}. Valid types: {", ".join(list(ExtractorRegistry.get_registered_types()))}"
                )
