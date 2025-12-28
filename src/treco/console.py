"""
Console utilities for TRECO.

Provides colored output and banner display.
"""

# Try to import colorama for colored output
try:
    from colorama import init as colorama_init, Fore, Style # type: ignore

    colorama_init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

    class Fore:
        """Fallback for missing colorama."""
        
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""
        RESET = ""

    class Style:
        """Fallback for missing colorama."""
        
        BRIGHT = ""
        DIM = ""
        RESET_ALL = ""


# Export color constants for convenience
class Colors:
    """Color constants for console output."""
    
    # Foreground colors
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Fore.RESET

    # Styles
    BRIGHT = Style.BRIGHT
    DIM = Style.DIM
    RESET_ALL = Style.RESET_ALL

    # Semantic colors
    ERROR = Fore.RED
    SUCCESS = Fore.GREEN
    WARNING = Fore.YELLOW
    INFO = Fore.CYAN
    HIGHLIGHT = Fore.MAGENTA


BANNER = f"""
{Colors.BRIGHT}{Colors.CYAN}
   /$$$$$$$$ /$$$$$$$  /$$$$$$$$  /$$$$$$   /$$$$$$ 
  |__  $$__/| $$__  $$| $$_____/ /$$__  $$ /$$__  $$
     | $$   | $$  \\ $$| $$      | $$  \\__/| $$  \\ $$
     | $$   | $$$$$$$/| $$$$$   | $$      | $$  | $$
     | $$   | $$__  $$| $$__/   | $$      | $$  | $$
     | $$   | $$  \\ $$| $$      | $$    $$| $$  | $$ 
     | $$   | $$  | $$| $$$$$$$$|  $$$$$$/|  $$$$$$/
     |__/   |__/  |__/|________/ \\______/  \\______/ 
   
  Tactical Race Exploitation & Concurrency Orchestrator
{Colors.YELLOW}
                        → it's not a bug, it's a race ←
{Colors.RESET_ALL}
"""


def print_banner() -> None:
    """Print the TRECO banner to stdout."""
    print(BANNER)


def success(message: str) -> str:
    """Format a success message."""
    return f"{Colors.SUCCESS}✓ {message}{Colors.RESET_ALL}"


def error(message: str) -> str:
    """Format an error message."""
    return f"{Colors.ERROR}✗ {message}{Colors.RESET_ALL}"


def warning(message: str) -> str:
    """Format a warning message."""
    return f"{Colors.WARNING}⚠ {message}{Colors.RESET_ALL}"


def info(message: str) -> str:
    """Format an info message."""
    return f"{Colors.INFO}→ {message}{Colors.RESET_ALL}"


def highlight(message: str) -> str:
    """Format a highlighted message."""
    return f"{Colors.BRIGHT}{message}{Colors.RESET_ALL}"