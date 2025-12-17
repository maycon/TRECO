"""
Main coordinator for Treco framework.

Orchestrates the entire attack flow including race condition attacks.
"""

import threading
import time
import traceback
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)

from treco.logging import user_output
from treco.models.config import RaceConfig

from treco.models import Config, State, ExecutionContext
from treco.parser import YAMLLoader
from treco.template import TemplateEngine
from treco.http import HTTPClient, HTTPParser, extractor
from treco.state import StateMachine, StateExecutor
from treco.sync import create_sync_mechanism
from treco.connection import create_connection_strategy


class HttpxResponseAdapter:
    """
    Adapter to make httpx.Response compatible with ResponseProtocol interface.
    
    This allows existing extractors and template code to work with httpx responses
    without modification.
    
    Attributes:
        status_code: HTTP status code
        text: Response body as text
        content: Response body as bytes
        headers: Response headers (dict-like)
        cookies: Response cookies
        url: Request URL
    """
    
    def __init__(self, httpx_response):
        """
        Create adapter from httpx.Response.
        
        Args:
            httpx_response: httpx.Response object
        """
        self._response = httpx_response
        
        # Direct mappings (same interface)
        self.status_code = httpx_response.status_code
        self.text = httpx_response.text
        self.content = httpx_response.content
        self.headers = dict(httpx_response.headers)
        self.url = str(httpx_response.url)
        
        # Cookies need conversion
        self.cookies = {name: value for name, value in httpx_response.cookies.items()}
    
    def json(self) -> Any:
        """Parse response body as JSON."""
        return self._response.json()
    
    @property
    def ok(self) -> bool:
        """Check if response was successful (2xx)."""
        return 200 <= self.status_code < 300
    
    @property
    def reason(self) -> str:
        """HTTP reason phrase."""
        return self._response.reason_phrase
    
    def __repr__(self) -> str:
        return f"<HttpxResponseAdapter [{self.status_code}]>"


@dataclass
class RaceResult:
    """Result from a single thread in a race attack."""

    thread_id: int
    status: int
    extracted: Dict[str, Any]
    timing_ns: int  # Time in nanoseconds from barrier release to response
    error: str = ""


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

    def __init__(self, config_path: str, cli_args: Optional[Dict[str, Any]] = None):
        """
        Initialize the coordinator.

        Args:
            config_path: Path to YAML configuration file
            cli_args: Command-line arguments dictionary
        """
        # Load configuration
        loader = YAMLLoader()
        self.config: Config = loader.load(config_path)

        # Initialize execution context
        import os

        self.context = ExecutionContext(argv=cli_args or {}, env=dict(os.environ))

        # Initialize components
        self.template_engine = TemplateEngine()
        self.http_client = HTTPClient(self.config.config)
        self.http_parser = HTTPParser()
        # self.extractors = extractor.JsonExtractor()
        self.engine = TemplateEngine()

        # Initialize state executor
        self.executor = StateExecutor(
            self.http_client,
            self.template_engine,
            # self.extractor
        )

        # Set self as race coordinator in executor
        self.executor.race_coordinator = self  # type: ignore

        # Initialize state machine
        self.machine = StateMachine(self.config, self.context, self.executor)

        logger.info(f"\n{'='*70}")
        logger.info(f"Treco - Race Condition PoC Framework")
        logger.info(f"{'='*70}")
        logger.info(f"Attack: {self.config.metadata.name}")
        logger.info(f"Version: {self.config.metadata.version}")
        logger.info(f"Vulnerability: {self.config.metadata.vulnerability}")
        logger.info(f"Target: {self.http_client.base_url}")
        logger.info(f"{'='*70}\n")

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

    def execute_race(self, state: State, context: ExecutionContext):
        """
        Execute a race condition attack for a given state.

        This is the core race attack logic:
        1. Create sync mechanism (barrier/latch/semaphore)
        2. Create connection strategy (preconnect/lazy/pooled)
        3. Spawn N threads
        4. Each thread:
           a. Gets its session (connection strategy)
           b. Waits at sync point
           c. Sends request simultaneously
           d. Records result and timing
        5. Collect all results
        6. Propagate context based on configuration

        Args:
            state: Race state to execute
            context: Current execution context

        Returns:
            ExecutionResult with aggregated race results
        """
        from treco.state.executor import ExecutionResult

        if not state.race:
            raise ValueError("State is not configured for race condition attack")

        race_config: RaceConfig = state.race
        num_threads = race_config.threads

        logger.info(f"\n{'='*70}")
        logger.info(f"RACE ATTACK: {state.name}")
        logger.info(f"{'='*70}")
        logger.info(f"Threads: {num_threads}")
        logger.info(f"Sync Mechanism: {race_config.sync_mechanism}")
        logger.info(f"Connection Strategy: {race_config.connection_strategy}")
        logger.info(f"Thread Propagation: {race_config.thread_propagation}")
        logger.info(f"{'='*70}\n")

        # Create sync mechanisms:
        # 1. conn_sync: Ensures all threads have established connections before proceeding
        # 2. race_sync: Synchronizes the actual race (all threads send simultaneously)
        conn_sync = create_sync_mechanism("barrier")
        race_sync = create_sync_mechanism(race_config.sync_mechanism)

        # Create connection strategy with connection sync
        conn_strategy = create_connection_strategy(
            race_config.connection_strategy,
            sync=conn_sync
        )
        
        # Prepare strategies
        conn_strategy.prepare(num_threads, self.http_client)
        race_sync.prepare(num_threads)

        # Shared results list (thread-safe with lock)
        race_results: List[RaceResult] = []
        results_lock = threading.Lock()

        # Worker function for each thread
        def race_worker(thread_id: int):

            thread_info = {"id": thread_id, "count": num_threads}

            try:
                # ════════════════════════════════════════════════════════════
                # PHASE 1: LOG THREAD ENTRY (optional)
                # ════════════════════════════════════════════════════════════
                if state.logger.on_thread_enter:

                    context_input = self.context.to_dict()
                    context_input["config"] = self.http_client.config
                    context_input["thread"] = thread_info

                    logger_output = self.engine.render(
                        state.logger.on_thread_enter,
                        context_input,
                        self.context,
                    )

                    for line in logger_output.splitlines():
                        user_output(f">> {state.name} T:{thread_id:02} {line}")

                # ════════════════════════════════════════════════════════════
                # PHASE 2: PREPARE REQUEST (before connect, can be serialized)
                # Render template and parse HTTP - this can be slow due to GIL
                # but it doesn't matter because we haven't connected yet
                # ════════════════════════════════════════════════════════════
                context_input = context.to_dict()
                context_input["config"] = self.http_client.config
                context_input["thread"] = {"id": thread_id, "count": num_threads}

                http_text = self.template_engine.render(state.request, context_input, context)
                method, path, headers, body = self.http_parser.parse(http_text)

                # ════════════════════════════════════════════════════════════
                # PHASE 3: CONNECT (parallel with internal barrier)
                # All threads establish connections simultaneously, then wait
                # at conn_sync barrier until everyone is connected
                # ════════════════════════════════════════════════════════════
                conn_strategy.connect(thread_id)
                client = conn_strategy.get_session(thread_id)

                # Build the prepared request (doesn't send yet)
                # This prepares all headers, encodes body, resolves URL
                request = client.build_request(
                    method=method,
                    url=path,  # base_url is already set in the client
                    headers=headers,
                    content=body if body else None,
                )

                # ════════════════════════════════════════════════════════════
                # PHASE 4: RACE SYNC (all threads ready, minimal gap)
                # At this point: connection established, request prepared
                # Only thing left is to send bytes over the wire
                # ════════════════════════════════════════════════════════════
                logger.debug(f"[Thread {thread_id}] Ready, waiting at race sync point...")
                race_sync.wait(thread_id)

                # ════════════════════════════════════════════════════════════
                # PHASE 5: RACE WINDOW - SEND ONLY
                # This is the critical section - only network I/O happens here
                # All preparation is done, just send the prepared request
                # ════════════════════════════════════════════════════════════
                start_time_ns = time.perf_counter_ns()

                response = client.send(request)

                end_time_ns = time.perf_counter_ns()
                # === RACE WINDOW ENDS HERE ===

                timing_ns = end_time_ns - start_time_ns

                # Extract data
                extracted = extractor.extract_all(response, state.extract)

                # Update context with extracted data
                context.set_list_item(
                    state.name,
                    thread_id,
                    {
                        "thread": thread_info,
                        "status": response.status_code,
                        "timing_ms": timing_ns / 1_000_000,
                        **extracted
                    },
                )

                # Store result
                result = RaceResult(
                    thread_id=thread_id,
                    status=response.status_code,
                    extracted=extracted,
                    timing_ns=timing_ns,
                )

                with results_lock:
                    race_results.append(result)

                logger.info(
                    f"[Thread {thread_id}] Status: {response.status_code}, "
                    f"Time: {timing_ns/1_000_000:.2f}ms"
                )

                # Log thread leave
                if state.logger.on_thread_leave:
                    context_input = self.context.to_dict()
                    context_input.update({
                        "config": self.http_client.config,
                        "thread": thread_info,
                        "response": response,
                        "timing_ms": timing_ns / 1_000_000
                    })

                    logger_output = self.engine.render(
                        state.logger.on_thread_leave,
                        context_input,
                        self.context,
                    )

                    for line in logger_output.splitlines():
                        user_output(f"<< {state.name} T:{thread_id:02} {line}")

            except Exception as e:
                # Store error result
                result = RaceResult(
                    thread_id=thread_id, status=0, extracted={}, timing_ns=0, error=str(e)
                )

                with results_lock:
                    race_results.append(result)

                logger.info(f"[Thread {thread_id}] ERROR: {str(e)}")

        # Create and start threads
        threads = []
        logger.info(f"\nStarting {num_threads} threads...\n")

        # Initialize context list for this state
        context.setdefault(state.name, [] * num_threads)

        for i in range(num_threads):
            thread = threading.Thread(target=race_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        logger.info(f"\n⚡ ALL THREADS RELEASED ⚡\n")

        # Cleanup connections
        conn_strategy.cleanup()

        # Analyze results
        self._analyze_race_results(race_results)

        # Propagate context based on configuration
        if race_config.thread_propagation == "single":
            # Use first successful result
            # TODO: make this configurable (first/last/best)
            for result in race_results:
                if result.status == 200 and result.extracted:
                    context.update(result.extracted)
                    break

        # Return aggregated result
        successful_count = sum(1 for r in race_results if r.status == 200)

        return ExecutionResult(
            state_name=state.name,
            status=200 if successful_count > 0 else 0,
            extracted={
                "race_thread_count": num_threads,
                "race_successful_count": successful_count,
                "race_results": [
                    {
                        "thread_": {"id": r.thread_id, "count": num_threads},
                        "status": r.status,
                        "timing_ms": r.timing_ns / 1_000_000,
                    }
                    for r in race_results
                ],
            },
        )

    def _handle_single_propagation(
        self, state: State, race_results: List[RaceResult], context: ExecutionContext
    ) -> None:
        """
        Handle single thread propagation (default behavior).

        Only one thread continues after the race. We pick the first
        successful result and merge its context into the main flow.

        Args:
            state: The race state that was executed
            race_results: List of results from all race threads
            context: Main execution context to update
        """
        logger.info(f"\n{'='*70}")
        logger.info("THREAD PROPAGATION: SINGLE")
        logger.info(f"{'='*70}\n")

        # Filter successful results
        successful = [r for r in race_results if r.status == 200 and not r.error]

        if not successful:
            logger.warning("No successful threads - nothing to propagate")
            return

        # Use first successful result (could be configurable: first/last/best)
        winning_result = successful[0]

        logger.info(f"Selected thread {winning_result.thread_id} for propagation")
        logger.info(
            f"Merging {len(winning_result.extracted)} extracted variables into main context"
        )

        # Update main context with extracted variables
        context.update(winning_result.extracted)

        logger.info(f"Context propagation complete\n")

    def _handle_parallel_propagation(
        self, state: State, race_results: List[RaceResult], context: ExecutionContext
    ) -> None:
        """
        Handle parallel thread propagation.

        All successful threads continue executing subsequent states
        independently. Each thread maintains its own context and
        executes the remaining flow in parallel.

        This is useful for:
        - Exploiting sequential race conditions
        - Testing concurrent state transitions
        - Amplifying attack impact

        Args:
            state: The race state that was executed
            race_results: List of results from all race threads
            context: Main execution context (used as template for thread contexts)
        """
        logger.info(f"\n{'='*70}")
        logger.info("THREAD PROPAGATION: PARALLEL")
        logger.info(f"{'='*70}\n")

        # Filter successful results
        successful = [r for r in race_results if r.status == 200 and not r.error]

        if not successful:
            logger.warning("No successful threads - nothing to propagate")
            return

        logger.info(f"Propagating {len(successful)} successful threads")

        # Get next state from transitions
        next_state_name = self._get_next_state(state)

        if not next_state_name:
            logger.info("No next state - race was the final state")
            # Still merge contexts for final reporting
            self._merge_parallel_contexts(successful, context)
            return

        logger.info(f"Next state: {next_state_name}")
        logger.info(f"Spawning {len(successful)} parallel threads...\n")

        # Create parallel execution threads
        parallel_threads = []
        parallel_contexts = []

        for result in successful:
            # Create independent context for this thread
            # Start with main context and add thread-specific extracted vars
            thread_context = ExecutionContext(argv=context._argv.copy(), env=context._env.copy())
            thread_context.update(context.to_dict())  # Copy main context
            thread_context.update(result.extracted)  # Add thread-specific vars

            parallel_contexts.append(thread_context)

            # Spawn thread to continue execution
            thread = threading.Thread(
                target=self._execute_parallel_flow,
                args=(next_state_name, thread_context, result.thread_id),
                name=f"ParallelFlow-{result.thread_id}",
            )
            parallel_threads.append(thread)
            thread.start()

        # Wait for all parallel threads to complete
        logger.info(f"Waiting for {len(parallel_threads)} parallel threads to complete...")

        for thread in parallel_threads:
            thread.join()

        logger.info(f"All parallel threads completed\n")

        # Merge contexts from all threads for final analysis
        self._merge_parallel_contexts(successful, context)

    def _execute_parallel_flow(
        self, start_state_name: str, thread_context: ExecutionContext, thread_id: int
    ) -> None:
        """
        Execute the remaining flow for a single parallel thread.

        This runs in its own thread and executes all subsequent states
        independently with its own context.

        Args:
            start_state_name: Name of the state to start from
            thread_context: Independent context for this thread
            thread_id: ID of this thread (for logging)
        """
        logger.info(f"[ParallelThread-{thread_id}] Starting flow from state: {start_state_name}")

        current_state_name = start_state_name

        try:
            while current_state_name:
                # Get state from config
                if current_state_name not in self.config.states:
                    logger.error(
                        f"[ParallelThread-{thread_id}] State not found: {current_state_name}"
                    )
                    return

                state = self.config.states[current_state_name]

                # Skip nested race states (not supported in parallel propagation)
                if state.race:
                    logger.warning(
                        f"[ParallelThread-{thread_id}] Skipping nested race state: {state.name}"
                    )
                    logger.warning(
                        f"[ParallelThread-{thread_id}] Nested races not supported in parallel propagation"
                    )
                    break

                logger.info(f"[ParallelThread-{thread_id}] Executing state: {state.name}")

                # Execute state using a dedicated executor with thread context
                thread_executor = StateExecutor(
                    self.http_client,
                    self.template_engine,
                )

                # Execute the state
                result = thread_executor.execute(state, thread_context)

                if not result or result.status != 200:
                    logger.error(
                        f"[ParallelThread-{thread_id}] State {state.name} failed "
                        f"with status {result.status if result else 'None'}"
                    )
                    return

                # Update thread context with extracted variables
                thread_context.update(result.extracted)

                # Get next state
                current_state_name = self._get_next_state(state)

            logger.info(f"[ParallelThread-{thread_id}] Flow completed successfully")

        except Exception as e:
            logger.error(f"[ParallelThread-{thread_id}] Error: {str(e)}")
            traceback.print_exc()

    def _get_next_state(self, state: State) -> Optional[str]:
        """
        Determine the next state to execute based on transitions.

        Currently uses simple logic (first transition), but could be
        enhanced to check status codes, conditions, etc.

        Args:
            state: Current state

        Returns:
            Name of next state, or None if no transitions
        """
        if not state.next or len(state.next) == 0:
            return None

        # Simple: take first transition
        # TODO: Could match against last_status_code with on_status
        return state.next[0].goto

    def _merge_parallel_contexts(
        self, results: List[RaceResult], main_context: ExecutionContext
    ) -> None:
        """
        Merge contexts from all parallel threads into the main context.

        This aggregates results for final reporting. Creates aggregate
        variables like:
        - variable_all: List of all values from all threads
        - variable_count: Count of values
        - variable_sum: Sum (if numeric)
        - variable_avg: Average (if numeric)

        Args:
            results: Results from all successful threads
            main_context: Main execution context to update with aggregated data
        """
        logger.info(f"\n{'='*70}")
        logger.info("MERGING PARALLEL CONTEXTS")
        logger.info(f"{'='*70}\n")

        aggregated: Dict[str, List[Any]] = {}

        # Collect all extracted variables from all threads
        for result in results:
            for key, value in result.extracted.items():
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append(value)

        # Create aggregated variables in main context
        for key, values in aggregated.items():
            # Store all values as a list
            main_context.set(f"{key}_all", values)
            main_context.set(f"{key}_count", len(values))

            logger.info(f"Aggregated '{key}': {len(values)} values")

            # Try to compute sum/average if numeric
            try:
                numeric_values = [float(v) for v in values]
                total = sum(numeric_values)
                average = total / len(numeric_values)

                main_context.set(f"{key}_sum", total)
                main_context.set(f"{key}_avg", average)

                logger.info(f"  → Sum: {total}, Average: {average:.2f}")

            except (ValueError, TypeError):
                # Not numeric, skip aggregation
                logger.info(f"  → Non-numeric values, skipping sum/avg")

        logger.info(f"\nContext merge complete\n")

    def _analyze_race_results(self, results: List[RaceResult]) -> None:
        """
        Analyze and print race attack results.

        Args:
            results: List of race results from all threads
        """
        logger.info(f"\n{'='*70}")
        logger.info("RACE ATTACK RESULTS")
        logger.info(f"{'='*70}\n")

        # Count successes and failures
        # TODO: make success/failure criteria configurable
        successful = [r for r in results if r.status == 200]
        failed = [r for r in results if r.status != 200 or r.error]

        logger.info(f"Total threads: {len(results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")

        # Timing analysis
        if successful:
            timings_ms = [r.timing_ns / 1_000_000 for r in successful]
            avg_timing = sum(timings_ms) / len(timings_ms)
            min_timing = min(timings_ms)
            max_timing = max(timings_ms)

            # Calculate race window (time between first and last request)
            race_window_ms = max_timing - min_timing

            logger.info(f"\nTiming Analysis:")
            logger.info(f"  Average response time: {avg_timing:.2f}ms")
            logger.info(f"  Fastest response: {min_timing:.2f}ms")
            logger.info(f"  Slowest response: {max_timing:.2f}ms")
            logger.info(f"  Race window: {race_window_ms:.2f}ms")

            # Evaluate race quality
            if race_window_ms < 1.0:
                logger.info(f"  ✓ EXCELLENT race window (< 1ms)")
            elif race_window_ms < 100.0:
                logger.info(f"  ⚠ GOOD race window (< 100ms)")
            else:
                logger.info(f"  ✗ POOR race window (> 100ms)")

        # Vulnerability analysis
        logger.info(f"\nVulnerability Assessment:")
        if len(successful) > 1:
            logger.info(f"  ⚠ VULNERABLE: Multiple requests succeeded ({len(successful)})")
            logger.info(f"  ⚠ Potential race condition detected!")
        elif len(successful) == 1:
            logger.info(f"  ✓ PROTECTED: Only 1 request succeeded")
            logger.info(f"  ✓ Server appears to have proper synchronization")
        else:
            logger.info(f"  ? INCONCLUSIVE: No successful requests")

        logger.info(f"\n{'='*70}\n")