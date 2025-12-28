"""
Race condition attack executor.

Handles the execution of race condition attacks with multi-threaded
coordination, input distribution, and result collection.
"""

import threading
import time
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import httpx
import logging

from treco.http import extractor
from treco.input import InputDistributor, InputMode
from treco.logging import user_output
from treco.models import ExecutionContext, State, build_template_context
from treco.models.config import RaceConfig
from treco.sync import create_sync_mechanism
from treco.connection import create_connection_strategy

if TYPE_CHECKING:
    from treco.http import HTTPClient, HTTPParser
    from treco.template import TemplateEngine


logger = logging.getLogger(__name__)


@dataclass
class RaceResult:
    """Result from a single thread in a race attack."""

    thread_id: int
    status: int
    extracted: Dict[str, Any]
    timing_ns: int
    error: str = ""


class RaceExecutor:
    """
    Executes race condition attacks for a given state.

    The executor handles:
    1. Sync mechanism creation (barrier/latch/semaphore)
    2. Connection strategy setup (preconnect/multiplexed/lazy/pooled)
    3. Input distribution across threads
    4. Multi-threaded request execution
    5. Result collection and timing measurement

    Example:
        executor = RaceExecutor(
            http_client=http_client,
            http_parser=http_parser,
            template_engine=template_engine,
            config=config,
        )
        
        result = executor.execute(state, context)
    """

    def __init__(
        self,
        http_client: "HTTPClient",
        http_parser: "HTTPParser",
        template_engine: "TemplateEngine",
        entrypoint_input: Dict[str, Any],
    ):
        """
        Initialize the race executor.

        Args:
            http_client: HTTP client for making requests
            http_parser: Parser for raw HTTP text
            template_engine: Template engine for rendering
            entrypoint_input: Input configuration from entrypoint
        """
        self.http_client = http_client
        self.http_parser = http_parser
        self.template_engine = template_engine
        self.entrypoint_input = entrypoint_input

    def execute(
        self,
        state: State,
        context: ExecutionContext,
    ) -> List[RaceResult]:
        """
        Execute a race condition attack for a given state.

        Args:
            state: Race state to execute
            context: Current execution context

        Returns:
            List of RaceResult from all threads

        Raises:
            ValueError: If state is not configured for race attack
        """
        if not state.race:
            raise ValueError("State is not configured for race condition attack")

        race_config: RaceConfig = state.race
        num_threads = race_config.threads

        self._log_race_start(state, race_config)

        # Create sync mechanisms
        conn_sync = create_sync_mechanism("barrier")
        race_sync = create_sync_mechanism(race_config.sync_mechanism)

        # Check proxy bypass
        bypass_proxy = state.should_bypass_proxy()
        if bypass_proxy:
            logger.info(f"Proxy bypass enabled for state: {state.name}")

        # Create connection strategy
        conn_strategy = create_connection_strategy(
            race_config.connection_strategy,
            sync=conn_sync,
            bypass_proxy=bypass_proxy,
        )

        # Prepare strategies
        conn_strategy.prepare(num_threads, self.http_client)
        race_sync.prepare(num_threads)

        # Setup input distribution
        input_distributor = self._setup_input_distributor(
            state, context, race_config, num_threads
        )

        # Execute race attack
        race_results = self._execute_threads(
            state=state,
            context=context,
            num_threads=num_threads,
            conn_strategy=conn_strategy,
            race_sync=race_sync,
            input_distributor=input_distributor,
        )

        # Cleanup
        conn_strategy.cleanup()

        return race_results

    def _log_race_start(self, state: State, race_config: RaceConfig) -> None:
        """Log race attack configuration."""
        logger.info(f"\n{'='*70}")
        logger.info(f"RACE ATTACK: {state.name}")
        logger.info(f"{'='*70}")
        logger.info(f"Threads: {race_config.threads}")
        logger.info(f"Sync Mechanism: {race_config.sync_mechanism}")
        logger.info(f"Connection Strategy: {race_config.connection_strategy}")
        logger.info(f"Thread Propagation: {race_config.thread_propagation}")
        logger.info(f"{'='*70}\n")

    def _setup_input_distributor(
        self,
        state: State,
        context: ExecutionContext,
        race_config: RaceConfig,
        num_threads: int,
    ) -> Optional[InputDistributor]:
        """
        Setup input distribution for race threads.

        Args:
            state: Race state
            context: Execution context
            race_config: Race configuration
            num_threads: Number of threads

        Returns:
            InputDistributor if inputs are configured, None otherwise
        """
        # Merge entrypoint input with state-level input
        merged_input: Dict[str, Any] = {}
        if self.entrypoint_input:
            merged_input.update(self.entrypoint_input)
        if state.input:
            merged_input.update(state.input)

        if not merged_input:
            return None

        # Resolve input configurations
        context_input = build_template_context(
            context=context,
            target=self.http_client.config,
        )

        resolved_inputs = self.template_engine.render_dict(
            merged_input,
            context_input,
            context,
        )

        # Normalize inputs: ensure all values are lists
        normalized_inputs = self._normalize_inputs(resolved_inputs)

        # Get input mode
        try:
            input_mode = InputMode[race_config.input_mode.upper()]
        except (KeyError, AttributeError):
            input_mode = InputMode.SAME

        distributor = InputDistributor(
            inputs=normalized_inputs,
            mode=input_mode,
            num_threads=num_threads,
        )

        logger.info(f"Input Mode: {input_mode.value}")
        logger.info(f"Input Variables: {list(resolved_inputs.keys())}")

        return distributor
    
    def _normalize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, List[Any]]:
        """
        Normalize input values to lists.
        
        InputDistributor expects all values to be lists. This method
        wraps scalar values in a list.
        
        Args:
            inputs: Dictionary with mixed scalar/list values
            
        Returns:
            Dictionary with all values as lists
        """
        normalized: Dict[str, List[Any]] = {}
        
        for key, value in inputs.items():
            if isinstance(value, list):
                normalized[key] = value
            else:
                # Wrap scalar in list
                normalized[key] = [value]
        
        return normalized

    def _execute_threads(
        self,
        state: State,
        context: ExecutionContext,
        num_threads: int,
        conn_strategy,
        race_sync,
        input_distributor: Optional[InputDistributor],
    ) -> List[RaceResult]:
        """
        Execute all race threads and collect results.

        Args:
            state: Race state
            context: Execution context
            num_threads: Number of threads
            conn_strategy: Connection strategy
            race_sync: Race synchronization mechanism
            input_distributor: Optional input distributor

        Returns:
            List of RaceResult from all threads
        """
        race_results: List[RaceResult] = []
        results_lock = threading.Lock()

        def worker(thread_id: int) -> None:
            result = self._race_worker(
                thread_id=thread_id,
                state=state,
                context=context,
                num_threads=num_threads,
                conn_strategy=conn_strategy,
                race_sync=race_sync,
                input_distributor=input_distributor,
            )
            with results_lock:
                race_results.append(result)

        # Create and start threads
        threads: List[threading.Thread] = []
        logger.info(f"\nStarting {num_threads} threads...\n")

        # Initialize context list for this state
        context.setdefault(state.name, [None] * num_threads)

        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        logger.info("\n⚡ ALL THREADS RELEASED ⚡\n")

        return race_results

    def _race_worker(
        self,
        thread_id: int,
        state: State,
        context: ExecutionContext,
        num_threads: int,
        conn_strategy,
        race_sync,
        input_distributor: Optional[InputDistributor],
    ) -> RaceResult:
        """
        Worker function for a single race thread.

        Args:
            thread_id: Thread identifier
            state: Race state
            context: Execution context
            num_threads: Total number of threads
            conn_strategy: Connection strategy
            race_sync: Race synchronization mechanism
            input_distributor: Optional input distributor

        Returns:
            RaceResult for this thread
        """
        thread_info: Dict[str, Any] = {"id": thread_id, "count": num_threads}
        thread_input = None
        
        if input_distributor:
            thread_input = input_distributor.get_for_thread(thread_id)
            thread_info["input"] = thread_input

        try:
            # Phase 1: Log thread entry
            self._log_thread_enter(state, context, thread_info, thread_input)

            # Phase 2: Prepare request
            context_input = build_template_context(
                context=context,
                target=self.http_client.config,
                thread=thread_info,
            )

            http_text = self.template_engine.render(
                state.request, context_input, context
            )
            method, path, headers, body = self.http_parser.parse(http_text)

            # Phase 3: Connect
            conn_strategy.connect(thread_id)
            client = conn_strategy.get_session(thread_id)

            # Build prepared request
            request = client.build_request(
                method=method,
                url=path,
                headers=headers,
                content=body if body else None,
            )

            # Phase 4: Race sync
            logger.debug(f"[Thread {thread_id}] Ready, waiting at race sync point...")
            race_sync.wait(thread_id)

            # Phase 5: Send request (RACE WINDOW)
            start_time_ns = time.perf_counter_ns()
            response = client.send(request)
            end_time_ns = time.perf_counter_ns()

            timing_ns = end_time_ns - start_time_ns

            # Extract data
            extracted = extractor.extract_all(response, state.extract)

            # Update context
            context.set_list_item(
                state.name,
                thread_id,
                {
                    "thread": thread_info,
                    "status": response.status_code,
                    "timing_ms": timing_ns / 1_000_000,
                    **extracted,
                },
            )

            logger.info(
                f"[Thread {thread_id}] Status: {response.status_code}, "
                f"Time: {timing_ns/1_000_000:.2f}ms"
            )

            # Log thread leave
            self._log_thread_leave(
                state, context, thread_info, thread_input, response, timing_ns
            )

            return RaceResult(
                thread_id=thread_id,
                status=response.status_code,
                extracted=extracted,
                timing_ns=timing_ns,
            )

        except Exception as e:
            logger.error(f"\n{'='*70}")
            logger.error(f"[Thread {thread_id}] ERROR: {str(e)}")
            logger.error(f"{'='*70}\n")
            traceback.print_exc()

            return RaceResult(
                thread_id=thread_id,
                status=0,
                extracted={},
                timing_ns=0,
                error=str(e),
            )

    def _log_thread_enter(
        self,
        state: State,
        context: ExecutionContext,
        thread_info: Dict[str, Any],
        thread_input: Optional[Dict[str, Any]],
    ) -> None:
        """Log thread entry if configured."""
        if not state.logger.on_thread_enter:
            return

        context_input = build_template_context(
            context=context,
            target=self.http_client.config,
            thread=thread_info,
            input_data=thread_input,
        )

        logger_output = self.template_engine.render(
            state.logger.on_thread_enter,
            context_input,
            context,
        )

        thread_id = thread_info["id"]
        for line in logger_output.splitlines():
            user_output(f">> {state.name} T:{thread_id:02} {line}")

    def _log_thread_leave(
        self,
        state: State,
        context: ExecutionContext,
        thread_info: Dict[str, Any],
        thread_input: Optional[Dict[str, Any]],
        response: httpx.Response,
        timing_ns: int,
    ) -> None:
        """Log thread leave if configured."""
        if not state.logger.on_thread_leave:
            return

        context_input = build_template_context(
            context=context,
            target=self.http_client.config,
            thread=thread_info,
            input_data=thread_input,
            response=response,
            timing_ms=timing_ns / 1_000_000,
        )

        logger_output = self.template_engine.render(
            state.logger.on_thread_leave,
            context_input,
            context,
        )

        thread_id = thread_info["id"]
        for line in logger_output.splitlines():
            user_output(f"<< {state.name} T:{thread_id:02} {line}")