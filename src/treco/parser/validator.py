"""
Configuration validator.

Validates YAML structure, required fields, and references.
"""

from typing import Dict, Any, Set

from treco.http.extractor import get_extractor, ExtractorRegistry


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
        self._validate_config(data["config"])
        self._validate_entrypoints(data["entrypoints"], data["states"])
        self._validate_states(data["states"])

    def _check_required_sections(self, data: Dict[str, Any]) -> None:
        """Check that all required top-level sections exist."""
        required = ["metadata", "config", "entrypoints", "states"]
        for section in required:
            if section not in data:
                raise ValueError(f"Missing required section: {section}")

    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate metadata section."""
        required_fields = ["name", "version", "author", "vulnerability"]
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")

    def _validate_config(self, config: Dict[str, Any]) -> None:
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

    def _validate_entrypoints(self, entrypoints: list, states: Dict[str, Any]) -> None:
        """Validate entrypoints section."""
        if not entrypoints:
            raise ValueError("At least one entrypoint is required")

        for idx, entry in enumerate(entrypoints):
            if "state" not in entry:
                raise ValueError(f"Entrypoint {idx} missing 'state' field")

            # Check that referenced state exists
            state_name = entry["state"]
            if state_name not in states:
                raise ValueError(f"Entrypoint references non-existent state: {state_name}")

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
        
        # on_status is optional (default 0 = always transition)
        if "on_status" in transition:
            status = transition["on_status"]
            if isinstance(status, int):
                status = [status]

            for s in status:
                if not isinstance(s, int) or s < 0:
                    raise ValueError(
                        f"State '{state_name}' transition {idx} has invalid on_status: {s}"
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
