"""
Race attack result analysis and context merging.

Provides analysis of race condition attack results including
timing analysis, vulnerability assessment, and context aggregation.
"""

import logging
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from treco.models import ExecutionContext
    from treco.orchestrator.race_executor import RaceResult


logger = logging.getLogger(__name__)


class ResultAnalyzer:
    """
    Analyzes race attack results and manages context propagation.

    Provides:
    - Timing analysis (average, min, max, race window)
    - Success/failure counting
    - Vulnerability assessment
    - Context aggregation for parallel propagation

    Example:
        analyzer = ResultAnalyzer()
        analyzer.analyze(race_results)
        analyzer.propagate_context(race_results, context, propagation_mode)
    """

    def analyze(self, results: List["RaceResult"]) -> None:
        """
        Analyze and log race attack results.

        Args:
            results: List of race results from all threads
        """
        logger.info(f"\n{'='*70}")
        logger.info("RACE ATTACK RESULTS")
        logger.info(f"{'='*70}\n")

        # Count successes and failures
        successful = [r for r in results if r.status == 200]
        failed = [r for r in results if r.status != 200 or r.error]

        logger.info(f"Total threads: {len(results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")

        # Timing analysis
        if successful:
            self._analyze_timing(successful)

        # Vulnerability analysis
        self._analyze_vulnerability(successful)

        logger.info(f"\n{'='*70}\n")

    def _analyze_timing(self, successful: List["RaceResult"]) -> None:
        """Analyze timing of successful requests."""
        timings_ms = [r.timing_ns / 1_000_000 for r in successful]
        avg_timing = sum(timings_ms) / len(timings_ms)
        min_timing = min(timings_ms)
        max_timing = max(timings_ms)
        race_window_ms = max_timing - min_timing

        logger.info("\nTiming Analysis:")
        logger.info(f"  Average response time: {avg_timing:.2f}ms")
        logger.info(f"  Fastest response: {min_timing:.2f}ms")
        logger.info(f"  Slowest response: {max_timing:.2f}ms")
        logger.info(f"  Race window: {race_window_ms:.2f}ms")

        # Evaluate race quality
        if race_window_ms < 1.0:
            logger.info("  ✓ EXCELLENT race window (< 1ms)")
        elif race_window_ms < 100.0:
            logger.info("  ⚠ GOOD race window (< 100ms)")
        else:
            logger.info("  ✗ POOR race window (> 100ms)")

    def _analyze_vulnerability(self, successful: List["RaceResult"]) -> None:
        """Analyze potential vulnerability based on results."""
        logger.info("\nVulnerability Assessment:")

        if len(successful) > 1:
            logger.info(f"  ⚠ VULNERABLE: Multiple requests succeeded ({len(successful)})")
            logger.info("  ⚠ Potential race condition detected!")
        elif len(successful) == 1:
            logger.info("  ✓ PROTECTED: Only 1 request succeeded")
            logger.info("  ✓ Server appears to have proper synchronization")
        else:
            logger.info("  ? INCONCLUSIVE: No successful requests")

    def propagate_context(
        self,
        results: List["RaceResult"],
        context: "ExecutionContext",
        propagation_mode: str,
    ) -> List["RaceResult"]:
        """
        Propagate race results to context based on configuration.

        Args:
            results: Race results from all threads
            context: Execution context to update
            propagation_mode: "single" or "parallel"

        Returns:
            List of successful results (for parallel propagation)
        """
        successful = [r for r in results if r.status == 200 and not r.error]

        if propagation_mode == "single":
            # Use first successful result
            for result in results:
                if result.status == 200 and result.extracted:
                    context.update(result.extracted)
                    break
        elif propagation_mode == "parallel":
            # Return successful results for parallel execution
            pass

        return successful

    def merge_parallel_contexts(
        self,
        results: List["RaceResult"],
        context: "ExecutionContext",
    ) -> None:
        """
        Merge contexts from all parallel threads into main context.

        Creates aggregate variables like:
        - variable_all: List of all values from all threads
        - variable_count: Count of values
        - variable_sum: Sum (if numeric)
        - variable_avg: Average (if numeric)

        Args:
            results: Results from all successful threads
            context: Main execution context to update
        """
        logger.info(f"\n{'='*70}")
        logger.info("MERGING PARALLEL CONTEXTS")
        logger.info(f"{'='*70}\n")

        aggregated: Dict[str, List[Any]] = {}

        # Collect all extracted variables
        for result in results:
            for key, value in result.extracted.items():
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append(value)

        # Create aggregated variables
        for key, values in aggregated.items():
            context.set(f"{key}_all", values)
            context.set(f"{key}_count", len(values))

            logger.info(f"Aggregated '{key}': {len(values)} values")

            # Try numeric aggregation
            try:
                numeric_values = [float(v) for v in values]
                total = sum(numeric_values)
                average = total / len(numeric_values)

                context.set(f"{key}_sum", total)
                context.set(f"{key}_avg", average)

                logger.info(f"  → Sum: {total}, Average: {average:.2f}")
            except (ValueError, TypeError):
                logger.info("  → Non-numeric values, skipping sum/avg")

        logger.info("\nContext merge complete\n")