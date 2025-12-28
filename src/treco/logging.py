"""
Logging configuration for TRECO.

Provides configurable log levels with special handling for YAML logger output.
"""

import logging
import sys
from enum import IntEnum


class LogLevel(IntEnum):
    """Log levels for TRECO."""
    
    QUIET = logging.CRITICAL + 10  # Above all standard levels
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG


# Custom log level for YAML logger output (always shown)
YAML_OUTPUT = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(YAML_OUTPUT, "OUTPUT")


# Log level name mapping
LOG_LEVEL_NAMES = {
    "quiet": LogLevel.QUIET,
    "critical": LogLevel.CRITICAL,
    "error": LogLevel.ERROR,
    "warning": LogLevel.WARNING,
    "info": LogLevel.INFO,
    "debug": LogLevel.DEBUG,
}


class TrecoFormatter(logging.Formatter):
    """Custom formatter with level-specific prefixes."""

    FORMATS = {
        logging.DEBUG: "[DEBUG] %(message)s",
        logging.INFO: "[+] %(message)s",
        logging.WARNING: "[!] %(message)s",
        logging.ERROR: "[ERROR] %(message)s",
        logging.CRITICAL: "[CRITICAL] %(message)s",
        YAML_OUTPUT: "%(message)s",  # Clean output for YAML logger
    }

    def format(self, record: logging.LogRecord) -> str:
        fmt = self.FORMATS.get(record.levelno, "%(message)s")
        formatter = logging.Formatter(fmt)
        return formatter.format(record)


class YamlOutputFilter(logging.Filter):
    """Filter that always allows YAML_OUTPUT level messages."""

    def __init__(self, base_level: int):
        super().__init__()
        self.base_level = base_level

    def filter(self, record: logging.LogRecord) -> bool:
        # Always allow YAML logger output
        if record.levelno == YAML_OUTPUT:
            return True
        # Apply normal level filtering
        return record.levelno >= self.base_level


def setup_logging(level_name: str = "quiet") -> logging.Logger:
    """
    Configure logging based on verbosity level.

    Args:
        level_name: One of 'quiet', 'critical', 'error', 'warning', 'info', 'debug'

    Returns:
        Configured logger instance
    """
    level = LOG_LEVEL_NAMES.get(level_name, LogLevel.QUIET)

    # Get TRECO logger
    logger = logging.getLogger("treco")
    logger.setLevel(logging.DEBUG)  # Capture all, filter on handler
    logger.handlers.clear()
    logger.propagate = False

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(TrecoFormatter())
    handler.addFilter(YamlOutputFilter(level))
    logger.addHandler(handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the TRECO logger instance."""
    return logging.getLogger("treco")


def user_output(message: str) -> None:
    """
    Output from YAML logger blocks.
    
    This is always shown regardless of log level setting.

    Args:
        message: Message to output
    """
    logger = get_logger()
    logger.log(YAML_OUTPUT, message)