import click
import os
import json
from typing import Dict, Any, List, Tuple

from treco import RaceCoordinator
from treco.logging import get_logger, setup_logging
from treco.console import Colors, error, print_banner, success, warning

def parse_set_value(value: str) -> Any:
    """Parse a --set value, handling special prefixes."""
    
    # File reference: @filename
    if value.startswith('@'):
        filepath = value[1:]
        with open(filepath, 'r') as f:
            # Return list of lines for wordlist-style files
            lines = [line.strip() for line in f if line.strip()]
            return lines if len(lines) > 1 else lines[0] if lines else ""
    
    # Environment variable: $VAR or ${VAR}
    if value.startswith('$'):
        var_name = value[1:].strip('{}')
        return os.environ.get(var_name, '')
    
    # JSON: starts with { or [
    if value.startswith(('{', '[')):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    
    # # Comma-separated list
    # if ',' in value and not value.startswith('"'):
    #     return [v.strip() for v in value.split(',')]
    
    # Boolean
    if value.lower() in ('true', 'yes', '1'):
        return True
    if value.lower() in ('false', 'no', '0'):
        return False
    
    # Integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Float
    try:
        return float(value)
    except ValueError:
        pass
    
    # String (default)
    return value


def parse_set_option(ctx, param, values: Tuple[str, ...]) -> Dict[str, Any]:
    """Parse multiple --set key=value options."""
    result = {}
    
    for item in values:
        if '=' not in item:
            raise click.BadParameter(f"Invalid format: '{item}'. Use key=value")
        
        key, value = item.split('=', 1)
        key = key.strip()
        
        # Handle type hints: key:type=value
        type_hint = None
        if ':' in key:
            key, type_hint = key.rsplit(':', 1)
        
        parsed_value = parse_set_value(value)
        
        # Apply type hint if specified
        if type_hint:
            parsed_value = apply_type_hint(parsed_value, type_hint)
        
        # Handle nested keys: config.host -> {"config": {"host": value}}
        if '.' in key:
            parts = key.split('.')
            current = result
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = parsed_value
        else:
            result[key] = parsed_value
    
    return result


def apply_type_hint(value: Any, type_hint: str) -> Any:
    """Apply type hint to value."""
    type_map = {
        'int': int,
        'float': float,
        'bool': lambda v: str(v).lower() in ('true', 'yes', '1'),
        'str': str,
        'list': lambda v: v if isinstance(v, list) else [v],
        'json': json.loads if isinstance(value, str) else lambda v: v,
    }
    
    converter = type_map.get(type_hint.lower())
    if converter:
        return converter(value)
    return value


@click.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option(
    '--set', '-s',
    'variables',
    multiple=True,
    callback=parse_set_option,
    help='Set input variable (key=value). Can be used multiple times.'
)
@click.option(
    '--log-level', '-l',
    type=click.Choice(['quiet', 'error', 'warning', 'info', 'debug']),
    default='warning',
    help='Log level'
)
@click.option(
    '--no-banner',
    is_flag=True,
    help='Disable banner output'
)
def main(config_file: str, variables: Dict[str, Any], log_level: str, 
         no_banner: bool):
    """
    TRECO - Tactical Race Exploitation & Concurrency Orchestrator
    
    Execute race condition attacks defined in CONFIG_FILE.
    
    \b
    Examples:
        treco attack.yaml
        treco attack.yaml --set username=carlos --set password=secret
        treco attack.yaml -s threads=50 -s host=target.com
        treco attack.yaml --set passwords=@wordlist.txt
    """
    
    # Setup logging with configured level
    setup_logging(log_level)
    logger = get_logger()

    # Print banner (unless suppressed)
    if not no_banner:
        print_banner()
    
    results = run_attack(config_file, variables)
    return results

def print_banner():
    """Print TRECO banner."""
    click.echo("""
╔═══════════════════════════════════════════════════════════╗
║  🦎 TRECO - Tactical Race Exploitation & Concurrency      ║
║                    Orchestrator                           ║
╚═══════════════════════════════════════════════════════════╝
    """)


def run_attack(config_path: str, variables: Dict[str, Any]) -> int:
    """
    Execute the race condition attack.

    Args:
        config_path: Path to configuration file
        variables: Input variables for the attack

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = get_logger()

    try:
        # Create and run coordinator
        coordinator = RaceCoordinator(config_path, variables)
        results = coordinator.run()

        # Success output
        print(success("Attack completed successfully"))
        print(f"  Total states executed: {len(results)}")

        return 0

    except KeyboardInterrupt:
        print(f"\n{warning('Attack interrupted by user')}")
        return 130

    except Exception as e:
        import sys, traceback
        print(f"\n{error(f'Attack failed: {e}')}", file=sys.stderr)
        logger.debug(traceback.format_exc())
        return 1

if __name__ == '__main__':
    main()