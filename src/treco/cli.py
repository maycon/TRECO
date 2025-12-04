"""
Command-line interface for Treco.

Provides a user-friendly CLI for running race condition attacks.
"""

import argparse
import sys
from pathlib import Path

import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

try:
    from colorama import init as colorama_init, Fore, Style  # type: ignore

    colorama_init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

    # Fallback for no colorama
    class Fore:
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""
        RESET = ""

    class Style:
        BRIGHT = ""
        RESET_ALL = ""


from .orchestrator import RaceCoordinator


def print_banner():
    """Print Treco banner."""
    banner = f"""
{Style.BRIGHT}{Fore.CYAN}
   /$$$$$$$$ /$$$$$$$  /$$$$$$$$  /$$$$$$   /$$$$$$ 
  |__  $$__/| $$__  $$| $$_____/ /$$__  $$ /$$__  $$
     | $$   | $$  \\ $$| $$      | $$  \\__/| $$  \\ $$
     | $$   | $$$$$$$/| $$$$$   | $$      | $$  | $$
     | $$   | $$__  $$| $$__/   | $$      | $$  | $$
     | $$   | $$  \\ $$| $$      | $$    $$| $$  | $$ 
     | $$   | $$  | $$| $$$$$$$$|  $$$$$$/|  $$$$$$/
     |__/   |__/  |__/|________/ \\______/  \\______/ 
   
  Tactical Race Exploitation & Concurrency Orchestrator
{Fore.YELLOW}
                        → it's not a bug, it's a race ←
{Style.RESET_ALL}
"""
    logger.info(banner)


def create_parser() -> argparse.ArgumentParser:
    """
    Create argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Treco - Tactical Race Exploitation & Concurrency Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python run.py configs/attack.yaml --user alice --seed JBSWY3DPEHPK3PXP
  
  # With custom thread count
  python run.py configs/attack.yaml --user alice --threads 50
  
  # Using environment variables
  export PASSWORD='alice123'
  python run.py configs/attack.yaml --user alice
  
  # Verbose output
  python run.py configs/attack.yaml --user alice --verbose

For more information, see README.md
        """,
    )

    parser.add_argument("config", type=str, help="Path to YAML configuration file")

    parser.add_argument("--user", type=str, help="Username for authentication")

    parser.add_argument(
        "--password", type=str, help="Password for authentication (prefer using env var PASSWORD)"
    )

    parser.add_argument("--seed", type=str, help="TOTP seed for 2FA generation")

    parser.add_argument("--threads", type=int, help="Number of concurrent threads for race attack")

    parser.add_argument("--host", type=str, help="Override target host")

    parser.add_argument("--port", type=int, help="Override target port")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    parser.add_argument("--version", action="version", version="Treco v1.0.0")

    return parser


def validate_config_file(config_path: str) -> Path:
    """
    Validate configuration file exists.

    Args:
        config_path: Path to config file

    Returns:
        Path object

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(config_path)

    if not path.exists():
        logger.error(
            f"{Fore.RED}Error: Configuration file not found: {config_path}{Style.RESET_ALL}"
        )
        sys.exit(1)

    if not path.is_file():
        logger.error(f"{Fore.RED}Error: Path is not a file: {config_path}{Style.RESET_ALL}")
        sys.exit(1)

    return path


def main():
    """Main CLI entry point."""
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Print banner
    if not args.verbose:
        print_banner()

    # Validate config file
    config_path = validate_config_file(args.config)

    # Build CLI arguments dictionary
    cli_args = {}
    if args.user:
        cli_args["user"] = args.user
    if args.password:
        cli_args["password"] = args.password
    if args.seed:
        cli_args["seed"] = args.seed
    if args.threads:
        cli_args["threads"] = args.threads
    if args.host:
        cli_args["host"] = args.host
    if args.port:
        cli_args["port"] = args.port

    try:
        # Create coordinator
        coordinator = RaceCoordinator(str(config_path), cli_args)

        # Execute attack
        results = coordinator.run()

        # Print success message
        logger.info(f"{Fore.GREEN}✓ Attack completed successfully{Style.RESET_ALL}")
        logger.info(f"  Total states executed: {len(results)}")

        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning(f"\n{Fore.YELLOW}⚠ Attack interrupted by user{Style.RESET_ALL}")
        sys.exit(130)

    except Exception as e:
        logger.error(f"\n{Fore.RED}✗ Attack failed: {str(e)}{Style.RESET_ALL}\n")

        if args.verbose:
            import traceback

            logger.error(f"\n{Fore.RED}Traceback:{Style.RESET_ALL}")
            traceback.print_exc()

        sys.exit(1)


if __name__ == "__main__":
    main()
