Python API Reference
====================

TRECO can be used programmatically in Python scripts.

Quick Start
-----------

.. code-block:: python

   from treco import RaceCoordinator
   
   # Create coordinator with config file
   coordinator = RaceCoordinator(
       "configs/attack.yaml",
       cli_args={"user": "alice", "threads": 20}
   )
   
   # Run attack
   results = coordinator.run()
   
   print(f"Attack completed: {len(results)} states executed")

Core Classes
------------

RaceCoordinator
~~~~~~~~~~~~~~~

The main entry point for TRECO attacks.

.. code-block:: python

   from treco import RaceCoordinator
   
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
       """
       
       def __init__(self, config_path: str, cli_args: dict = None):
           """
           Initialize the coordinator.
           
           Args:
               config_path: Path to YAML configuration file
               cli_args: Command-line arguments dictionary
           """
           pass
       
       def run(self) -> list:
           """
           Execute the complete attack flow.
           
           Returns:
               List of execution results
           """
           pass

**Example:**

.. code-block:: python

   from treco import RaceCoordinator
   
   # Basic usage
   coordinator = RaceCoordinator("attack.yaml")
   results = coordinator.run()
   
   # With CLI arguments
   coordinator = RaceCoordinator(
       "attack.yaml",
       cli_args={
           "user": "testuser",
           "password": "testpass",
           "threads": 30,
           "host": "api.staging.example.com"
       }
   )
   results = coordinator.run()

Configuration Models
--------------------

Config
~~~~~~

Root configuration object.

.. code-block:: python

   from treco.models import Config
   
   @dataclass
   class Config:
       metadata: Metadata
       target: TargetConfig
       entrypoint: Entrypoint
       states: Dict[str, State]

ServerConfig
~~~~~~~~~~~~

Server and execution settings.

.. code-block:: python

   from treco.models import ServerConfig
   
   @dataclass
   class ServerConfig:
       host: str
       port: int
       threads: int = 20
       reuse_connection: bool = False
       tls: TLSConfig = field(default_factory=TLSConfig)

State
~~~~~

State definition.

.. code-block:: python

   from treco.models import State
   
   @dataclass
   class State:
       name: str
       description: str
       request: str
       extract: Dict[str, ExtractPattern] = field(default_factory=dict)
       next: List[Transition] = field(default_factory=list)
       race: Optional[RaceConfig] = None
       logger: LoggerConfig = field(default_factory=LoggerConfig)

RaceConfig
~~~~~~~~~~

Race attack configuration.

.. code-block:: python

   from treco.models import RaceConfig
   
   @dataclass
   class RaceConfig:
       threads: int = 20
       sync_mechanism: str = "barrier"
       connection_strategy: str = "preconnect"
       reuse_connections: bool = False
       thread_propagation: str = "single"

Template Engine
---------------

TemplateEngine
~~~~~~~~~~~~~~

Jinja2-based template engine with custom filters.

.. code-block:: python

   from treco.template import TemplateEngine
   
   class TemplateEngine:
       """
       Wrapper around Jinja2 with custom filters for Treco.
       
       Custom filters available:
       - totp(seed): Generate TOTP token
       - env(var, default): Read environment variable
       - argv(var, default): Read CLI argument
       - md5(value): MD5 hash
       - sha1(value): SHA1 hash
       - sha256(value): SHA256 hash
       - average(list): Average of values
       """
       
       def render(self, template_str: str, variables: dict, context=None) -> str:
           """Render a template string with provided variables."""
           pass
       
       def render_dict(self, data: dict, variables: dict, context=None) -> dict:
           """Recursively render all string values in a dictionary."""
           pass

**Example:**

.. code-block:: python

   from treco.template import TemplateEngine
   
   engine = TemplateEngine()
   
   # Simple rendering
   result = engine.render(
       "Hello {{ name }}",
       {"name": "Alice"}
   )
   # Output: "Hello Alice"
   
   # With TOTP
   result = engine.render(
       "Code: {{ totp(seed) }}",
       {"seed": "JBSWY3DPEHPK3PXP"}
   )
   # Output: "Code: 123456"
   
   # With hashing
   result = engine.render(
       "Hash: {{ password | sha256 }}",
       {"password": "secret"}
   )

Extractors
----------

BaseExtractor
~~~~~~~~~~~~~

Base class for all extractors.

.. code-block:: python

   from treco.http.extractor import BaseExtractor
   
   class BaseExtractor:
       """Base class for data extractors."""
       
       def extract(self, response, pattern: str) -> Optional[Any]:
           """
           Extract data from HTTP response.
           
           Args:
               response: ResponseProtocol object
               pattern: Extraction pattern
           
           Returns:
               Extracted value or None
           """
           raise NotImplementedError

Available Extractors
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from treco.http.extractor import get_extractor, extract_all
   
   # Get specific extractor
   jpath = get_extractor('jpath')
   xpath = get_extractor('xpath')
   regex = get_extractor('regex')
   boundary = get_extractor('boundary')
   header = get_extractor('header')
   cookie = get_extractor('cookie')
   
   # Extract from response
   import requests
   response = requests.get("https://api.example.com/data")
   
   token = jpath.extract(response, "$.token")
   csrf = xpath.extract(response, '//input[@name="csrf"]/@value')
   session = cookie.extract(response, "session_id")

Creating Custom Extractors
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from treco.http.extractor.base import BaseExtractor, register_extractor
   
   @register_extractor('custom', aliases=['my_extractor'])
   class CustomExtractor(BaseExtractor):
       """Custom extractor implementation."""
       
       def extract(self, response, pattern: str):
           """Extract data using custom logic."""
           content = response.text
           # Your extraction logic here
           return extracted_value

Synchronization
---------------

SyncMechanism
~~~~~~~~~~~~~

Base class for synchronization mechanisms.

.. code-block:: python

   from treco.sync import create_sync_mechanism
   
   # Create sync mechanism
   barrier = create_sync_mechanism("barrier")
   latch = create_sync_mechanism("countdown_latch")
   semaphore = create_sync_mechanism("semaphore")
   
   # Prepare for N threads
   barrier.prepare(20)
   
   # Wait at sync point (called by each thread)
   barrier.wait(thread_id)

Connection Strategies
---------------------

ConnectionStrategy
~~~~~~~~~~~~~~~~~~

Base class for connection strategies.

.. code-block:: python

   from treco.connection import create_connection_strategy
   
   # Create strategy
   preconnect = create_connection_strategy("preconnect")
   lazy = create_connection_strategy("lazy")
   pooled = create_connection_strategy("pooled")
   
   # Prepare connections
   preconnect.prepare(20, http_client)
   
   # Get session for thread
   session = preconnect.get_session(thread_id)

HTTP Client
-----------

HTTPClient
~~~~~~~~~~

HTTP client with connection management.

.. code-block:: python

   from treco.http import HTTPClient
   
   class HTTPClient:
       """HTTP client for making requests."""
       
       def __init__(self, config: ServerConfig):
           """Initialize with server configuration."""
           pass
       
       @property
       def base_url(self) -> str:
           """Get base URL for requests."""
           pass
       
       def close(self):
           """Close all connections."""
           pass

HTTPParser
~~~~~~~~~~

Parse raw HTTP request strings.

.. code-block:: python

   from treco.http import HTTPParser
   
   parser = HTTPParser()
   
   http_text = """
   POST /api/login HTTP/1.1
   Host: example.com
   Content-Type: application/json
   
   {"username": "user", "password": "pass"}
   """
   
   method, path, headers, body = parser.parse(http_text)
   # method = "POST"
   # path = "/api/login"
   # headers = {"Host": "example.com", "Content-Type": "application/json"}
   # body = '{"username": "user", "password": "pass"}'

State Machine
-------------

StateMachine
~~~~~~~~~~~~

Orchestrates state execution.

.. code-block:: python

   from treco.state import StateMachine
   
   class StateMachine:
       """State machine for attack flow orchestration."""
       
       def __init__(self, config: Config, context: ExecutionContext, executor):
           """Initialize state machine."""
           pass
       
       def run(self) -> list:
           """Execute state machine from entrypoint."""
           pass

ExecutionContext
~~~~~~~~~~~~~~~~

Manages execution state and variables.

.. code-block:: python

   from treco.models import ExecutionContext
   
   class ExecutionContext:
       """Execution context for variable storage."""
       
       def __init__(self, argv: dict = None, env: dict = None):
           """Initialize context with CLI args and environment."""
           pass
       
       def set(self, key: str, value):
           """Set a variable in context."""
           pass
       
       def get(self, key: str, default=None):
           """Get a variable from context."""
           pass
       
       def to_dict(self) -> dict:
           """Convert context to dictionary."""
           pass
       
       def update(self, data: dict):
           """Update context with dictionary."""
           pass

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """Custom TRECO attack script."""
   
   import os
   from treco import RaceCoordinator
   from treco.template import TemplateEngine
   from treco.http.extractor import get_extractor
   
   def main():
       # Set up environment
       os.environ['PASSWORD'] = 'secret123'
       
       # Create coordinator
       coordinator = RaceCoordinator(
           "configs/attack.yaml",
           cli_args={
               "user": "testuser",
               "threads": 20,
           }
       )
       
       try:
           # Run attack
           results = coordinator.run()
           
           # Analyze results
           print(f"\nAttack completed!")
           print(f"States executed: {len(results)}")
           
           # Custom analysis
           for result in results:
               print(f"- {result}")
               
       except KeyboardInterrupt:
           print("\nAttack interrupted by user")
       except Exception as e:
           print(f"\nAttack failed: {e}")
           raise
   
   if __name__ == "__main__":
       main()

See Also
--------

* :doc:`configuration` - YAML configuration reference
* :doc:`extractors` - Data extraction methods
* :doc:`templates` - Template syntax and filters
* `GitHub Repository <https://github.com/maycon/TRECO>`_ - Source code
