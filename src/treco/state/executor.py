"""
State executor implementation.

Executes individual states by rendering templates, making requests,
and extracting data from responses.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional
from dataclasses import dataclass

import logging

from treco.http.extractor import extract_all

from treco.models import State, ExecutionContext
from treco.template import TemplateEngine
from treco.http import HTTPClient

if TYPE_CHECKING:
    from treco.orchestrator.coordinator import RaceCoordinator

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """
    Result of executing a state.

    Attributes:
        state_name: Name of the executed state
        status: HTTP status code (0 for non-HTTP states)
        extracted: Dictionary of extracted variables
        raw_response: Raw HTTP response text
        error: Error message if execution failed
    """

    state_name: str
    status: int
    extracted: Dict[str, Any]
    raw_response: str = ""
    error: str = ""


class StateExecutor:
    """
    Executes individual states in the state machine.

    For each state, the executor:
    1. Renders the HTTP request template with current context
    2. Sends the HTTP request
    3. Extracts data from the response using regex patterns
    4. Updates the execution context with extracted data

    Race states are handled specially by delegating to the RaceCoordinator.

    Example:
        executor = StateExecutor(http_client, template_engine, extractor)
        result = executor.execute(state, context)
        logger.info(result.extracted)  # {"bearer_token": "...", "balance": 1000}
    """

    def __init__(
        self,
        http_client: HTTPClient,
        template_engine: TemplateEngine,
        # extractor: BaseExtractor
    ):
        """
        Initialize the state executor.

        Args:
            http_client: HTTP client for making requests
            template_engine: Template engine for rendering templates
            extractor: Data extractor for parsing responses
        """
        self.http_client: HTTPClient = http_client
        self.template_engine: TemplateEngine = template_engine
        self.race_coordinator: Optional[RaceCoordinator] = None  # Set by orchestrator if needed

    def execute(self, state: State, context: ExecutionContext) -> ExecutionResult:
        """
        Execute a state.

        Args:
            state: State to execute
            context: Current execution context

        Returns:
            ExecutionResult with status and extracted data
        """
        # Check if this is a race state
        result: Optional[ExecutionResult] = None
        if state.race:
            # Delegate to race coordinator
            if self.race_coordinator is None:
                raise RuntimeError("Race coordinator not configured for race state")
            result = self.race_coordinator.execute_race(state, context)
        else:
            # Normal single-threaded execution
            result = self._execute_single(state, context)

        return result

    def _execute_single(self, state: State, context: ExecutionContext) -> ExecutionResult:
        """
        Execute a single (non-race) state.

        Args:
            state: State to execute
            context: Execution context

        Returns:
            ExecutionResult
        """

        if not state.request:
            logger.info(f"[StateExecutor] Skipping state '{state.name}' with no request")
            self._last_response = None
            return ExecutionResult(
                state_name=state.name,
                status=0,
                extracted={},
                raw_response="",
            )

        try:
            # Render HTTP request template
            context_input = context.to_dict()
            context_input["target"] = self.http_client.config
            http_text = self.template_engine.render(state.request, context_input, context)

            logger.debug(f"[StateExecutor] Rendered HTTP request for state '{state.name}':\n{http_text}")
            # Send HTTP request
            response = self.http_client.send(http_text, state.should_bypass_proxy())
            
            # Store the response for when block evaluation
            self._last_response = response

            logger.info(f"[StateExecutor] Response status: {response.status_code}")
            logger.debug(f"[StateExecutor] Response headers:\n{response.headers}")
            logger.debug(f"[StateExecutor] Response received:\n{response.text}")

            # Extract data from response
            extracted = extract_all(response, state.extract, context.to_dict())

            if extracted:
                logger.info(f"[StateExecutor] Extracted variables: {list(extracted.keys())}")

            # Update context with extracted data
            context.update({state.name: extracted})

            return ExecutionResult(
                state_name=state.name,
                status=response.status_code,
                extracted=extracted,
                raw_response=response.text,
            )

        except Exception as e:
            logger.error(f"[StateExecutor] ERROR: {str(e)}")
            import traceback

            traceback.print_exc()
            
            self._last_response = None

            return ExecutionResult(state_name=state.name, status=0, extracted={}, error=str(e))