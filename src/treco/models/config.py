"""
Configuration dataclasses for Treco framework.

These classes represent the structure of the YAML configuration file,
providing type safety and validation.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


@dataclass
class Metadata:
    """
    Metadata about the attack scenario.

    Attributes:
        name: Human-readable name of the attack
        version: Version of the configuration
        author: Author of the attack scenario
        vulnerability: CVE or CWE identifier
    """

    name: str
    version: str
    author: str
    vulnerability: str


@dataclass
class TLSConfig:
    """
    TLS/SSL configuration.

    Attributes:
        enabled: Whether to use HTTPS
        verify_cert: Whether to verify SSL certificates
    """

    enabled: bool = False
    verify_cert: bool = False

@dataclass
class HTTPConfig:
    """
    HTTP client configuration.

    Attributes:
        follow_redirects: Whether to follow redirects
    """

    follow_redirects: bool = True

@dataclass
class ProxyAuth:
    """
    Proxy authentication configuration.

    Attributes:
        username: Proxy username
        password: Proxy password
    """

    username: str
    password: str

@dataclass
class ProxyConfig:
    """
    Proxy server configuration.

    Attributes:
        host: Proxy hostname or IP address
        port: Proxy port number
        type: Proxy type (http, https, socks5)
        auth: Optional proxy authentication
    """
    host: Optional[str] = None
    port: Optional[int] = None
    type: str = "http"
    auth: Optional[ProxyAuth] = None

    def to_client_proxy(self) -> Optional[str]:
        """Convert proxy configuration to dictionary format for HTTP clients."""
        if not self.host or not self.port:
            return None
        
        if self.auth:
            proxy_url = f"{self.type}://{self.auth.username}:{self.auth.password}@{self.host}:{self.port}"
        else:
            proxy_url = f"{self.type}://{self.host}:{self.port}"
            
        return proxy_url

@dataclass
class ServerConfig:
    """
    Target server configuration.

    Attributes:
        host: Server hostname or IP address
        port: Server port number
        threads: Default number of concurrent threads
        reuse_connection: Whether to reuse TCP connections
        tls: TLS/SSL configuration
        http: HTTP client configuration
    """

    host: str
    port: int
    threads: int = 20
    reuse_connection: bool = False
    tls: TLSConfig = field(default_factory=TLSConfig)
    http: HTTPConfig = field(default_factory=HTTPConfig)
    proxy: Optional[ProxyConfig] = None


@dataclass
class Entrypoint:
    """
    Defines the initial state and variables for execution.

    Attributes:
        state: Name of the starting state
        input: Initial variable definitions with template support
    """

    state: str
    input: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Transition:
    """
    State transition rule based on HTTP response.

    Attributes:
        on_status: HTTP status code(s) that triggers this transition
        goto: Name of the next state to transition to
        delay_ms: Optional delay in milliseconds before transition
    """

    on_status: List[int]
    goto: str
    delay_ms: int = 0


@dataclass
class RaceConfig:
    """
    Configuration for race condition attacks within a state.

    Attributes:
        threads: Number of concurrent threads for the race
        sync_mechanism: Synchronization strategy (barrier, countdown_latch, semaphore)
        connection_strategy: Connection establishment strategy (preconnect, lazy, pooled)
        reuse_connections: Whether threads reuse connections
        thread_propagation: How to propagate threads after race (single, parallel)
    """

    threads: int = 20
    sync_mechanism: str = "barrier"
    connection_strategy: str = "preconnect"
    reuse_connections: bool = False
    thread_propagation: str = "single"


@dataclass
class LoggerConfig:
    """
    Logging configuration for state execution.

    Attributes:
        on_enter: Template string to log when entering the state
        on_leave: Template string to log when leaving the state
    """

    on_state_enter: str = ""
    on_state_leave: str = ""
    on_thread_enter: str = ""
    on_thread_leave: str = ""


@dataclass
class ExtractPattern:
    """
    Represents a single extraction pattern for a variable.

    Patterns can be of different types:
    - regex: Regular expression pattern to extract data
    - jpath: JSONPath expression to extract data from JSON responses
    - xpath: XPath expression to extract data from XML/HTML responses
    - jinja2: Jinja2 template to extract data

    Attributes:
        pattern_type: Type of extraction (e.g., regex)
        pattern_data: The actual pattern string
    """

    pattern_type: str
    pattern_data: str


@dataclass
class State:
    """
    Represents a single state in the attack flow.

    A state can be either:
    - A normal sequential state (single request)
    - A race state (multiple concurrent requests)

    Attributes:
        name: Unique identifier for this state
        description: Human-readable description
        request: HTTP request template (raw HTTP format)
        extract: Dictionary of variable_name -> regex_pattern for data extraction
        next: List of possible transitions to other states
        race: Optional race configuration (makes this a race state)
        logger: Logger configuration for state entry/exit
    """

    name: str
    description: str
    request: str
    extract: Dict[str, ExtractPattern] = field(default_factory=dict)
    next: List[Transition] = field(default_factory=list)
    race: Optional[RaceConfig] = None
    logger: LoggerConfig = field(default_factory=LoggerConfig)


@dataclass
class Config:
    """
    Root configuration object representing the entire YAML file.

    This is the top-level structure that contains all attack configuration,
    including metadata, server settings, states, and entrypoints.

    Attributes:
        metadata: Attack metadata (name, version, author, vulnerability)
        config: Server and execution configuration
        entrypoints: List of possible entry points (usually just one)
        states: Dictionary mapping state names to State objects
    """

    metadata: Metadata
    config: ServerConfig
    entrypoints: List[Entrypoint]
    states: Dict[str, State]
