"""
State machine implementation.

Manages the execution flow through states with automatic transitions.
"""

from dataclasses import asdict
import time
from typing import Any, Dict, Optional

import logging

from treco.models.context import build_template_context

from treco.logging import user_output

from treco.models import Config, State, ExecutionContext
from treco.template import TemplateEngine
from treco.state.executor import StateExecutor, ExecutionResult
from treco.state.conditions import ConditionEvaluator

logger = logging.getLogger(__name__)



class StateMachine:
    """
    State machine that orchestrates the attack flow.

    The machine:
    1. Starts at the configured entrypoint state
    2. Executes each state via StateExecutor
    3. Evaluates transitions based on HTTP status or when blocks
    4. Navigates to the next state
    5. Continues until reaching a terminal state (end, error)

    Example:
        config = YAMLLoader().load("config.yaml")
        context = ExecutionContext()
        machine = StateMachine(config, context, executor)

        results = machine.run()  # Execute the entire flow
    """

    def __init__(self, config: Config, context: ExecutionContext, executor: StateExecutor):
        """
        Initialize the state machine.

        Args:
            config: Parsed configuration
            context: Execution context for variable storage
            executor: State executor for running individual states
        """
        self.config = config
        self.context = context
        self.executor = executor
        self.engine = TemplateEngine()
        self.condition_evaluator = ConditionEvaluator(self.engine)
        self.current_state: Optional[str] = None
        self.history: list = []  # Track visited states for debugging

    def run(self) -> list:
        """
        Execute the state machine from entrypoint to completion.

        Returns:
            List of execution results from all states

        Raises:
            ValueError: If state not found or invalid transition
        """
        # Initialize entrypoint variables
        entrypoint = self.config.entrypoint
        self._initialize_variables(entrypoint.input)

        # Start from entrypoint state
        state_name = entrypoint.state
        results = []

        logger.info(f"[StateMachine] Starting from state: {state_name}")

        # Execute until terminal state
        while state_name not in ["end", "error"]:
            # Get state definition
            if state_name not in self.config.states:
                raise ValueError(f"State not found: {state_name}")

            state = self.config.states[state_name]
            self.current_state = state_name
            self.history.append(state_name)

            state_description: str = self.engine.render(
                state.description,
                self._get_render_context(),
                self.context,
            )

            logger.info(f"\n[StateMachine] Executing state: {state_name}")
            logger.info(f"[StateMachine] Description: {state_description}")
            
            if state.logger.on_state_enter:
                logger_output = self.engine.render(
                    state.logger.on_state_enter,
                    self._get_render_context(race=state.race),
                    self.context,
                )

                user_output(f">> {state_name}")
                for line in logger_output.splitlines():
                    user_output(f"  {line}")
                user_output("")

            # Execute state
            result = self.executor.execute(state, self.context)
            results.append(result)

            if state.logger.on_state_leave:
                logger_output = self.engine.render(
                    state.logger.on_state_leave,
                    self._get_render_context(response=asdict(result), race=state.race),
                    self.context,
                )
                user_output(f"<< {state_name}")
                for line in logger_output.splitlines():
                    user_output(f"  {line}")
                user_output("")

            # Determine next state based on result
            next_state = self._get_next_state(state, result)

            # Apply transition delay if specified
            transition = self._find_transition(state, result)
            if transition and transition.delay_ms > 0:
                delay_seconds = transition.delay_ms / 1000.0
                logger.info(f"[StateMachine] Delaying {delay_seconds}s before next transition")
                time.sleep(delay_seconds)

            state_name = next_state

        logger.info(f"\n[StateMachine] Reached terminal state: {state_name}")
        logger.info(f"[StateMachine] Execution path: {' → '.join(self.history)}")

        return results
    
    def _get_render_context(self, **extra: Any) -> Dict[str, Any]:
        """Get base context for template rendering."""
        return build_template_context(
            context=self.context,
            target=self.config.target,
            **extra,
        )

    def _initialize_str_variable(self, template_str: str) -> str:
        """
        Render and initialize a string variable from template.

        Args:
            template_str: Template string to render
        Returns:
            Rendered string value
        """
        ctx = self._get_render_context()
        return self.engine.render(template_str, ctx, self.context)

    def _initialize_list_variable(self, template_list: list) -> list:
        """
        Render and initialize a list variable from templates.

        Args:
            template_list: List of template strings to render
        Returns:
            List of rendered string values
        """
        rendered_list = []

        ctx = self._get_render_context()
        for item in template_list:
            if isinstance(item, str):
                rendered_item = self.engine.render(item, ctx, self.context)
                rendered_list.append(rendered_item)
            else:
                rendered_list.append(item)
        return rendered_list

    def _initialize_dict_variable(self, input_dict) -> dict:
        return_dict = {}

        ctx = self._get_render_context()
        for key, value_template in input_dict.items():
            if not isinstance(value_template, str):
                rendered_value = self._initialize_variables(value_template)
            else:
                rendered_value = self.engine.render(value_template, ctx, self.context)
            return_dict.update({key: rendered_value if rendered_value else value_template})
        return return_dict

    def _initialize_variables(self, input_dict: dict) -> None:
        """
        Initialize entrypoint variables in context.

        Variables may contain templates that need to be resolved
        before storing in context.

        Args:
            input_dict: Dictionary of variable definitions from entrypoint
        """

        # Render each variable template and store in context
        renders = {
            "str": self._initialize_str_variable,
            "list": self._initialize_list_variable,
            "dict": self._initialize_dict_variable,
        }

        for key, value_template in input_dict.items():
            tp: str = type(value_template).__name__
            rendered_value = renders[tp](value_template) if tp in renders else None
            self.context.set(key, rendered_value if rendered_value else value_template)

    def _get_next_state(self, state: State, result: ExecutionResult) -> str:
        """
        Determine the next state based on execution result.

        Args:
            state: Current state
            result: Execution result with status code and response

        Returns:
            Name of next state to execute
        """
        # Find matching transition
        transition = self._find_transition(state, result)

        if transition:
            return transition.goto

        # No transition available, go to error state
        logger.warning(
            f"[StateMachine] WARNING: No transition for status {result.status}, going to error"
        )
        return "error"

    def _find_transition(self, state: State, result: ExecutionResult):
        """
        Find a matching transition for the given execution result.

        Supports both legacy on_status transitions and new when block transitions.

        Args:
            state: Current state
            result: Execution result with status code, response, etc.

        Returns:
            Matching Transition object or None
        """
        # Try to get the response object from the executor's last response
        # This is needed for when block evaluation
        response = getattr(self.executor, '_last_response', None)
        
        for transition in state.next:
            # Check when block conditions
            if transition.when is not None:
                if response is None:
                    logger.warning("[StateMachine] No response available for when block evaluation")
                    continue
                
                # Evaluate all conditions in the when block (AND logic)
                if self.condition_evaluator.evaluate_when_block(
                    transition.when, 
                    response, 
                    self.context,
                    response_time_ms=getattr(result, 'response_time_ms', None)
                ):
                    return transition
            
            # Check otherwise (catch-all)
            elif transition.otherwise:
                return transition
            
            # Legacy on_status check
            elif transition.on_status is not None and result.status in transition.on_status:
                return transition
        
        return None
