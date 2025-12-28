"""
Main coordinator for Treco framework.

Orchestrates the entire attack flow including race condition attacks.
"""

import os
import traceback
from typing import Any, Dict, List, Optional, Union

import logging

from treco.models import Config, State, ExecutionContext
from treco.models.config import BaseConfig, RaceConfig
from treco.parser import YAMLLoader
from treco.template import TemplateEngine
from treco.http import HTTPClient, HTTPParser
from treco.state import StateMachine, StateExecutor
from treco.state.executor import ExecutionResult

from .race_executor import RaceExecutor, RaceResult
from .result_analyzer import ResultAnalyzer
from .parallel_executor import ParallelExecutor


logger = logging.getLogger(__name__)


class RaceCoordinator:
    """
    Main coordinator that orchestrates the entire Treco attack flow.

    The coordinator:
    1. Loads and validates YAML configuration
    2. Initializes all components (HTTP client, template engine, etc.)
    3. Executes normal states via StateMachine
    4. Detects and handles race states specially
    5. Coordinates multi-threaded race attacks
    6. Collects and aggregates results

    Example:
        coordinator = RaceCoordinator("configs/attack.yaml", cli_args)
        results = coordinator.run()
        logger.info(f"Attack completed: {len(results)} states executed")
    """

    def __init__(
        self,
        config_path: str,
        cli_inputs: Optional[Dict[str, Any]] = None,
        log_level: str = "info",
    ):
        """
        Initialize the coordinator.

        Args:
            config_path: Path to YAML configuration file
            cli_inputs: Command-line input variables to override config
            log_level: Logging level (debug, info, warning, error)
        """
        self.config_path = config_path
        self.cli_inputs = cli_inputs or {}
        self.log_level = log_level

        # Load configuration
        loader = YAMLLoader()
        self.config: Config = loader.load(config_path)

        # Apply CLI config overrides
        self._apply_config_overrides()

        # Initialize context
        self.context = ExecutionContext(argv=cli_inputs or {}, env=dict(os.environ))

        # Initialize components
        self.engine = TemplateEngine()
        self.http_client = HTTPClient(self.config.target)
        self.http_parser = HTTPParser()

        # Initialize executors
        self.race_executor = RaceExecutor(
            http_client=self.http_client,
            http_parser=self.http_parser,
            template_engine=self.engine,
            entrypoint_input=self.config.entrypoint.input,
        )
        self.result_analyzer = ResultAnalyzer()
        self.parallel_executor = ParallelExecutor(
            config=self.config,
            http_client=self.http_client,
            template_engine=self.engine,
        )

        # Initialize state executor
        self.state_executor = StateExecutor(self.http_client, self.engine)
        self.state_executor.race_coordinator = self

        # Initialize state machine
        self.machine = StateMachine(self.config, self.context, self.state_executor)

        self._log_startup()

    def _log_startup(self) -> None:
        """Log startup information."""
        logger.info(f"\n{'='*70}")
        logger.info("Treco - Race Condition PoC Framework")
        logger.info(f"{'='*70}")
        logger.info(f"Attack: {self.config.metadata.name}")
        logger.info(f"Version: {self.config.metadata.version}")
        logger.info(f"Vulnerability: {self.config.metadata.vulnerability}")
        logger.info(f"Target: {self.http_client.base_url}")
        logger.info(f"{'='*70}\n")

    def _apply_config_overrides(self) -> None:
        """Apply command-line config overrides to loaded configuration."""
        logger.debug(f"Applying CLI config overrides: {self.cli_inputs}")

        if "input" in self.cli_inputs:
            self._merge_config(self.config.entrypoint.input, self.cli_inputs["input"])

        if "target" in self.cli_inputs:
            self._merge_config(self.config.target, self.cli_inputs["target"])

    def _merge_config(
        self,
        config: Union[BaseConfig, Dict[Any, Any]],
        cli_config: Dict[str, Any],
    ) -> None:
        """
        Merge CLI config overrides into existing configuration.

        Args:
            config: Existing configuration object or dictionary
            cli_config: CLI config overrides as dictionary
        """
        logger.debug(f"Merging CLI config overrides: {cli_config}")

        for key, value in cli_config.items():
            if isinstance(config, dict):
                if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                    self._merge_config(config[key], value)
                else:
                    config[key] = value
            else:
                if hasattr(config, key):
                    current_value = getattr(config, key)
                    if isinstance(current_value, BaseConfig) and isinstance(value, dict):
                        self._merge_config(current_value, value)
                    elif isinstance(current_value, dict) and isinstance(value, dict):
                        self._merge_config(current_value, value)
                    else:
                        setattr(config, key, value)

    def run(self) -> List:
        """
        Execute the complete attack flow.

        Returns:
            List of execution results
        """
        try:
            results = self.machine.run()

            logger.info(f"\n{'='*70}")
            logger.info("Attack Completed Successfully")
            logger.info(f"{'='*70}\n")

            return results

        except Exception as e:
            logger.error(f"\n{'='*70}")
            logger.error(f"Attack Failed: {str(e)}")
            logger.error(f"{'='*70}\n")
            traceback.print_exc()
            raise
        finally:
            self.http_client.close()

    def execute_race(self, state: State, context: ExecutionContext) -> ExecutionResult:
        """
        Execute a race condition attack for a given state.

        This method is called by StateExecutor when it encounters a race state.

        Args:
            state: Race state to execute
            context: Current execution context

        Returns:
            ExecutionResult with aggregated race results
        """
        # Execute race attack
        race_results = self.race_executor.execute(state, context)

        # Analyze results
        self.result_analyzer.analyze(race_results)

        # Get race config
        race_config: RaceConfig = state.race  # type: ignore

        # Propagate context
        successful = self.result_analyzer.propagate_context(
            race_results, context, race_config.thread_propagation
        )

        # Handle parallel propagation
        if race_config.thread_propagation == "parallel" and successful:
            next_state = self._get_next_state(state)
            if next_state:
                self.parallel_executor.execute_parallel_flows(
                    successful, next_state, context
                )
                self.result_analyzer.merge_parallel_contexts(successful, context)

        # Return aggregated result
        return self._create_race_result(state, race_results)

    def _get_next_state(self, state: State) -> Optional[str]:
        """Get next state name from transitions."""
        if not state.next:
            return None
        return state.next[0].goto

    def _create_race_result(
        self,
        state: State,
        race_results: List[RaceResult],
    ) -> ExecutionResult:
        """
        Create an ExecutionResult from race results.

        Args:
            state: Race state
            race_results: List of race results

        Returns:
            Aggregated ExecutionResult
        """
        # Find first successful result
        for result in race_results:
            if result.status == 200:
                return ExecutionResult(
                    state_name=state.name,
                    status=result.status,
                    extracted=result.extracted,
                    raw_response="",
                )

        # No success, return first result
        if race_results:
            first = race_results[0]
            return ExecutionResult(
                state_name=state.name,
                status=first.status,
                extracted=first.extracted,
                error=first.error,
            )

        # No results at all
        return ExecutionResult(
            state_name=state.name,
            status=0,
            extracted={},
            error="No race results",
        )