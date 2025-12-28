"""
Parallel flow executor for thread propagation.

Handles execution of remaining states in parallel after a race attack
when thread_propagation is set to "parallel".
"""

import threading
import traceback
import logging
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from treco.models import Config, State, ExecutionContext
    from treco.http import HTTPClient
    from treco.template import TemplateEngine
    from treco.orchestrator.race_executor import RaceResult


logger = logging.getLogger(__name__)


class ParallelExecutor:
    """
    Executes remaining flow in parallel for each successful race thread.

    After a race attack with thread_propagation="parallel", each successful
    thread continues executing subsequent states independently.

    Example:
        executor = ParallelExecutor(config, http_client, template_engine)
        executor.execute_parallel_flows(
            successful_results,
            next_state_name,
            context,
        )
    """

    def __init__(
        self,
        config: "Config",
        http_client: "HTTPClient",
        template_engine: "TemplateEngine",
    ):
        """
        Initialize parallel executor.

        Args:
            config: Attack configuration
            http_client: HTTP client
            template_engine: Template engine
        """
        self.config = config
        self.http_client = http_client
        self.template_engine = template_engine

    def execute_parallel_flows(
        self,
        successful_results: List["RaceResult"],
        next_state_name: str,
        context: "ExecutionContext",
    ) -> None:
        """
        Execute remaining flow in parallel for all successful threads.

        Args:
            successful_results: List of successful race results
            next_state_name: Starting state for parallel execution
            context: Base execution context
        """
        if not successful_results:
            logger.info("No successful race results for parallel propagation")
            return

        if not next_state_name or next_state_name in ["end", "error"]:
            logger.info("No next state for parallel propagation")
            return

        logger.info(f"\n{'='*70}")
        logger.info("PARALLEL PROPAGATION")
        logger.info(f"{'='*70}")
        logger.info(f"Starting {len(successful_results)} parallel flows from: {next_state_name}")
        logger.info(f"{'='*70}\n")

        # Create parallel threads
        parallel_threads: List[threading.Thread] = []

        for result in successful_results:
            # Create independent context for each thread
            thread_context = context.copy()
            thread_context.update(result.extracted)

            thread = threading.Thread(
                target=self._execute_flow,
                args=(next_state_name, thread_context, result.thread_id),
                name=f"ParallelFlow-{result.thread_id}",
            )
            parallel_threads.append(thread)
            thread.start()

        # Wait for completion
        logger.info(f"Waiting for {len(parallel_threads)} parallel threads to complete...")

        for thread in parallel_threads:
            thread.join()

        logger.info("All parallel threads completed\n")

    def _execute_flow(
        self,
        start_state_name: str,
        thread_context: "ExecutionContext",
        thread_id: int,
    ) -> None:
        """
        Execute remaining flow for a single parallel thread.

        Args:
            start_state_name: Starting state name
            thread_context: Independent context for this thread
            thread_id: Thread identifier for logging
        """
        from treco.state import StateExecutor

        logger.info(f"[ParallelThread-{thread_id}] Starting flow from: {start_state_name}")

        current_state_name = start_state_name

        try:
            while current_state_name and current_state_name not in ["end", "error"]:
                if current_state_name not in self.config.states:
                    logger.error(f"[ParallelThread-{thread_id}] State not found: {current_state_name}")
                    return

                state = self.config.states[current_state_name]

                # Skip nested race states
                if state.race:
                    logger.warning(f"[ParallelThread-{thread_id}] Skipping nested race: {state.name}")
                    break

                logger.info(f"[ParallelThread-{thread_id}] Executing: {state.name}")

                # Execute state
                executor = StateExecutor(self.http_client, self.template_engine)
                result = executor.execute(state, thread_context)

                if not result or result.status != 200:
                    logger.error(
                        f"[ParallelThread-{thread_id}] State {state.name} failed "
                        f"with status {result.status if result else 'None'}"
                    )
                    return

                # Update context
                thread_context.update(result.extracted)

                # Get next state
                current_state_name = self._get_next_state(state)

            logger.info(f"[ParallelThread-{thread_id}] Flow completed successfully")

        except Exception as e:
            logger.error(f"[ParallelThread-{thread_id}] Error: {str(e)}")
            traceback.print_exc()

    def _get_next_state(self, state: "State") -> str:
        """
        Get next state name from transitions.

        Args:
            state: Current state

        Returns:
            Next state name or empty string
        """
        if not state.next:
            return ""

        # Simple: take first transition
        return state.next[0].goto