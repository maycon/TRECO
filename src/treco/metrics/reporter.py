import json
from typing import Dict, Any
from pathlib import Path

from treco.metrics.registry import MetricsCounter, MetricsTimer

class MetricsReporter:
    """Generate metrics reports."""
    
    @staticmethod
    def generate_report(timer: 'MetricsTimer', counter: 'MetricsCounter') -> Dict[str, Any]:
        """Generate comprehensive metrics report."""
        return {
            'timings': MetricsReporter._analyze_timings(timer.timings),
            'counters': dict(counter.counts),
            'summary': MetricsReporter._generate_summary(timer, counter),
        }
    
    @staticmethod
    def _analyze_timings(timings: Dict) -> Dict[str, Any]:
        """Analyze timing data."""
        analysis = {}
        
        for name, measurements in timings.items():
            if not measurements:
                continue
            
            durations = [m['duration_ms'] for m in measurements if m['error'] is None]
            errors = sum(1 for m in measurements if m['error'] is not None)
            
            if durations:
                analysis[name] = {
                    'count': len(measurements),
                    'errors': errors,
                    'total_ms': sum(durations),
                    'mean_ms': sum(durations) / len(durations),
                    'min_ms': min(durations),
                    'max_ms': max(durations),
                    'p50_ms': sorted(durations)[len(durations) // 2],
                    'p95_ms': sorted(durations)[int(len(durations) * 0.95)],
                    'p99_ms': sorted(durations)[int(len(durations) * 0.99)],
                }
        
        return analysis
    
    @staticmethod
    def _generate_summary(timer: 'MetricsTimer', counter: 'MetricsCounter') -> Dict[str, Any]:
        """Generate summary statistics."""
        total_operations = sum(len(v) for v in timer.timings.values())
        total_time = sum(
            sum(m['duration_ms'] for m in measurements)
            for measurements in timer.timings.values()
        )
        
        return {
            'total_operations': total_operations,
            'total_time_ms': total_time,
            'total_counters': sum(counter.counts.values()),
        }
    
    @staticmethod
    def save_report(report: Dict[str, Any], filepath: Path):
        """Save report to file."""
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
    
    @staticmethod
    def print_report(report: Dict[str, Any]):
        """Print formatted report to console."""
        print("\n" + "="*80)
        print("TRECO PERFORMANCE METRICS REPORT")
        print("="*80 + "\n")
        
        # Summary
        summary = report['summary']
        print(f"Total Operations: {summary['total_operations']}")
        print(f"Total Time: {summary['total_time_ms']:.2f}ms")
        print(f"Total Counters: {summary['total_counters']}\n")
        
        # Top slowest operations
        print("Top 10 Slowest Operations:")
        print("-" * 80)
        
        timings = report['timings']
        sorted_ops = sorted(
            timings.items(),
            key=lambda x: x[1]['mean_ms'],
            reverse=True
        )[:10]
        
        for name, stats in sorted_ops:
            print(f"{name:60} {stats['mean_ms']:>8.2f}ms (±{stats['max_ms']-stats['min_ms']:.2f}ms)")
        
        print()