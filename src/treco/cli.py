"""
Command-line interface for TRECO.

Provides a user-friendly CLI for running race condition attacks.
"""

import argparse
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .console import Colors, error, print_banner, success, warning
from .logging import LOG_LEVEL_NAMES, get_logger, setup_logging
from .orchestrator import RaceCoordinator

__version__ = "1.0.0"


@dataclass
class CLIConfig:
    """Parsed CLI configuration."""

    config_path: Path
    log_level: str
    show_banner: bool
    cli_args: Dict[str, Any]


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="treco",
        description="TRECO - Tactical Race Exploitation & Concurrency Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  treco attack.yaml --user alice --seed JBSWY3DPEHPK3PXP
  
  # With custom thread count
  treco attack.yaml --user alice --threads 50
  
  # Using environment variables for sensitive data
  export PASSWORD='secret'
  treco attack.yaml --user alice
  
  # Verbose output (debug level)
  treco attack.yaml --user alice -v
  
  # Custom log level
  treco attack.yaml --user alice --log-level info

Documentation: https://treco.readthedocs.io
        """,
    )

    # Positional arguments
    parser.add_argument(
        "config",
        type=str,
        metavar="CONFIG_FILE",
        help="Path to YAML configuration file",
    )

    # Authentication options
    auth_group = parser.add_argument_group("Authentication")
    auth_group.add_argument(
        "--user", "-u",
        type=str,
        metavar="USERNAME",
        help="Username for authentication",
    )
    auth_group.add_argument(
        "--password", "-p",
        type=str,
        metavar="PASSWORD",
        help="Password (prefer env var PASSWORD for security)",
    )
    auth_group.add_argument(
        "--seed", "-s",
        type=str,
        metavar="TOTP_SEED",
        help="TOTP seed for 2FA generation",
    )

    # Target options
    target_group = parser.add_argument_group("Target")
    target_group.add_argument(
        "--host", "-H",
        type=str,
        metavar="HOSTNAME",
        help="Override target hostname",
    )
    target_group.add_argument(
        "--port", "-P",
        type=int,
        metavar="PORT",
        help="Override target port",
    )

    # Execution options
    exec_group = parser.add_argument_group("Execution")
    exec_group.add_argument(
        "--threads", "-t",
        type=int,
        metavar="COUNT",
        help="Number of concurrent threads for race attack",
    )

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "--log-level", "-l",
        type=str,
        choices=list(LOG_LEVEL_NAMES.keys()),
        default="quiet",
        metavar="LEVEL",
        help="Log verbosity: quiet, critical, error, warning, info, debug (default: quiet)",
    )
    output_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (shortcut for --log-level debug)",
    )
    output_group.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress banner output",
    )

    # Info options
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def validate_config_path(config_path: str) -> Path:
    """
    Validate that configuration file exists and is readable.

    Args:
        config_path: Path to configuration file

    Returns:
        Validated Path object

    Raises:
        SystemExit: If validation fails
    """
    path = Path(config_path)

    if not path.exists():
        print(error(f"Configuration file not found: {config_path}"), file=sys.stderr)
        sys.exit(1)

    if not path.is_file():
        print(error(f"Path is not a file: {config_path}"), file=sys.stderr)
        sys.exit(1)

    if path.suffix.lower() not in (".yaml", ".yml"):
        print(warning(f"File does not have .yaml/.yml extension: {config_path}"), file=sys.stderr)

    return path


def build_cli_args(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Build CLI arguments dictionary from parsed arguments.

    Args:
        args: Parsed argument namespace

    Returns:
        Dictionary of non-None CLI arguments
    """
    arg_mapping = {
        "user": args.user,
        "password": args.password,
        "seed": args.seed,
        "threads": args.threads,
        "host": args.host,
        "port": args.port,
    }

    return {k: v for k, v in arg_mapping.items() if v is not None}


def parse_args(argv: Optional[List[str]] = None) -> CLIConfig:
    """
    Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv)

    Returns:
        Parsed CLI configuration
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Validate config file
    config_path = validate_config_path(args.config)

    # Resolve log level (--verbose overrides --log-level)
    log_level = "debug" if args.verbose else args.log_level

    # Determine if banner should be shown
    show_banner = not args.no_banner and log_level != "debug"

    # Build CLI args dict
    cli_args = build_cli_args(args)

    return CLIConfig(
        config_path=config_path,
        log_level=log_level,
        show_banner=show_banner,
        cli_args=cli_args,
    )


def run_attack(config: CLIConfig) -> int:
    """
    Execute the race condition attack.

    Args:
        config: CLI configuration

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = get_logger()

    try:
        # Create and run coordinator
        coordinator = RaceCoordinator(str(config.config_path), config.cli_args)
        results = coordinator.run()

        # Success output
        print(success("Attack completed successfully"))
        print(f"  Total states executed: {len(results)}")

        return 0

    except KeyboardInterrupt:
        print(f"\n{warning('Attack interrupted by user')}")
        return 130

    except Exception as e:
        print(f"\n{error(f'Attack failed: {e}')}", file=sys.stderr)
        logger.debug(traceback.format_exc())
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point.

    Args:
        argv: Argument list (defaults to sys.argv)

    Returns:
        Exit code
    """
    # Parse arguments first (before setting up logging)
    try:
        config = parse_args(argv)
    except SystemExit as e:
        return e.code if e.code is not None else 1

    # Setup logging with configured level
    setup_logging(config.log_level)
    logger = get_logger()

    # Print banner (unless suppressed)
    if config.show_banner:
        print_banner()

    # Log startup info
    logger.info(f"Loading configuration: {config.config_path}")
    if config.cli_args:
        safe_args = {k: "***" if k == "password" else v for k, v in config.cli_args.items()}
        logger.debug(f"CLI overrides: {safe_args}")

    # Run attack
    return run_attack(config)


def cli() -> None:
    """Entry point for setuptools console script."""
    sys.exit(main())


if __name__ == "__main__":
    cli()