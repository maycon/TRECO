Configuration Reference
=======================

This page provides a complete reference for TRECO's YAML configuration format.

YAML Structure Overview
-----------------------

A complete TRECO configuration file consists of four main sections:

.. code-block:: yaml

   metadata:      # Attack metadata
   target:        # Server and execution settings
   entrypoint:    # Starting point
   states:        # State definitions

Metadata Section
----------------

The ``metadata`` section provides information about the attack scenario.

.. code-block:: yaml

   metadata:
     name: "Race Condition Test"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-362"

**Fields:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``name``
     - Yes
     - Human-readable name of the attack
   * - ``version``
     - Yes
     - Version of this configuration
   * - ``author``
     - Yes
     - Author of the attack scenario
   * - ``vulnerability``
     - Yes
     - CVE or CWE identifier (e.g., CWE-362)

Target Section
--------------

The ``target`` section defines server connection and execution settings.

**Basic Configuration:**

.. code-block:: yaml

   target:
     host: "api.example.com"
     port: 443
     threads: 20
     reuse_connection: false

**Complete Configuration:**

.. code-block:: yaml

   target:
     host: "api.example.com"
     port: 443
     threads: 20
     reuse_connection: false
     
     tls:
       enabled: true
       verify_cert: true
       # mTLS options (choose one)
       client_cert: "./certs/client.crt"
       client_key: "./certs/client.key"
       client_key_password: "{{ env('KEY_PASSWORD') }}"
       # OR
       client_pem: "./certs/combined.pem"
       # OR
       client_pfx: "./certs/client.pfx"
       client_pfx_password: "{{ env('PFX_PASSWORD') }}"
     
     http:
       follow_redirects: true
       timeout: 30
     
     proxy:
       host: "proxy.example.com"
       port: 8080
       type: "http"
       auth:
         username: "{{ env('PROXY_USER') }}"
         password: "{{ env('PROXY_PASS') }}"

**Fields:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 45

   * - Field
     - Required
     - Default
     - Description
   * - ``host``
     - Yes
     - —
     - Target hostname or IP address
   * - ``port``
     - Yes
     - —
     - Target port number
   * - ``threads``
     - No
     - 20
     - Default number of concurrent threads for race attacks
   * - ``reuse_connection``
     - No
     - false
     - Whether to reuse TCP connections across requests

TLS Configuration
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 45

   * - Field
     - Required
     - Default
     - Description
   * - ``tls.enabled``
     - No
     - false
     - Use HTTPS instead of HTTP
   * - ``tls.verify_cert``
     - No
     - false
     - Verify SSL/TLS certificates
   * - ``tls.client_cert``
     - No
     - —
     - Path to client certificate for mTLS (PEM format)
   * - ``tls.client_key``
     - No
     - —
     - Path to client private key for mTLS (PEM format)
   * - ``tls.client_key_password``
     - No
     - —
     - Password for encrypted client key (supports templates)
   * - ``tls.client_pem``
     - No
     - —
     - Path to combined PEM file (cert + key)
   * - ``tls.client_pfx``
     - No
     - —
     - Path to PKCS12 file (.pfx or .p12) for mTLS
   * - ``tls.client_pfx_password``
     - No
     - —
     - Password for PKCS12 file (supports templates)

**Note:** Use only ONE of the following mTLS options:

- ``client_cert`` + ``client_key`` (separate files)
- ``client_pem`` (combined file)
- ``client_pfx`` (PKCS12 format)

HTTP Configuration
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 45

   * - Field
     - Required
     - Default
     - Description
   * - ``http.follow_redirects``
     - No
     - true
     - Follow HTTP redirects (3xx responses)
   * - ``http.timeout``
     - No
     - 30
     - Request timeout in seconds

Proxy Configuration
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 45

   * - Field
     - Required
     - Default
     - Description
   * - ``proxy.host``
     - No
     - —
     - Proxy server hostname or IP
   * - ``proxy.port``
     - No
     - —
     - Proxy server port
   * - ``proxy.type``
     - No
     - http
     - Proxy type: ``http``, ``https``, or ``socks5``
   * - ``proxy.auth.username``
     - No
     - —
     - Proxy authentication username
   * - ``proxy.auth.password``
     - No
     - —
     - Proxy authentication password (supports templates)

**Example with proxy:**

.. code-block:: yaml

   target:
     host: "api.example.com"
     port: 443
     proxy:
       host: "proxy.company.com"
       port: 8080
       type: "http"
       auth:
         username: "{{ env('PROXY_USER') }}"
         password: "{{ env('PROXY_PASS') }}"

Entrypoint Section
-------------------

The ``entrypoint`` section defines starting point for execution.

.. code-block:: yaml

   entrypoint:
     state: login
     input:
       username: "testuser"
       password: "testpass"
       api_key: "{{ env('API_KEY') }}"

**Fields:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``state``
     - Yes
     - Name of the starting state
   * - ``input``
     - No
     - Initial variables (supports templates)

States Section
--------------

The ``states`` section defines each step in the attack flow.

Basic State
~~~~~~~~~~~

.. code-block:: yaml

   states:
     login:
       description: "Authenticate and get token"
       request: |
         POST /api/login HTTP/1.1
         Host: {{ target.host }}
         Content-Type: application/json
         
         {"username": "{{ username }}", "password": "{{ password }}"}
       
       extract:
         token:
           type: jpath
           pattern: "$.access_token"
       
       next:
         - on_status: 200
           goto: next_state
         - on_status: 401
           goto: error_state

**State Fields:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``description``
     - No
     - Human-readable description of the state
   * - ``request``
     - No*
     - HTTP request template (required for non-terminal states)
   * - ``extract``
     - No
     - Variable extraction patterns (see :doc:`extractors`)
   * - ``race``
     - No
     - Race attack configuration (makes this a race state)
   * - ``logger``
     - No
     - Logging configuration for this state
   * - ``options``
     - No
     - Additional execution options (see below)
   * - ``input``
     - No
     - State-level input override (see :doc:`input-sources`)
   * - ``next``
     - No
     - State transition rules (see :doc:`when-blocks`)

State Options
~~~~~~~~~~~~~

The ``options`` block provides additional control over state execution:

.. code-block:: yaml

   states:
     bypass_proxy_state:
       description: "Direct connection bypassing proxy"
       options:
         proxy_bypass: true
       request: |
         GET /internal-api HTTP/1.1

**Available Options:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Option
     - Default
     - Description
   * - ``proxy_bypass``
     - false
     - If true, bypass proxy configuration for this state only

State-Level Input
~~~~~~~~~~~~~~~~~

States can override entrypoint input values:

.. code-block:: yaml

   entrypoint:
     state: login
     input:
       username: "global_user"
       api_key: "global_key"
   
   states:
     login:
       input:
         username: "override_user"  # Overrides entrypoint value
       request: |
         POST /login HTTP/1.1
         
         {"username": "{{ username }}"}  # Uses "override_user"

This is useful for:

- Testing different values per state
- State-specific configurations
- Dynamic value generation per state

Race Configuration
~~~~~~~~~~~~~~~~~~

Add a ``race`` block to enable concurrent execution:

.. code-block:: yaml

   states:
     race_attack:
       request: |
         POST /api/action HTTP/1.1
         Authorization: Bearer {{ token }}
       
       race:
         threads: 20
         sync_mechanism: barrier
         connection_strategy: preconnect
         thread_propagation: single
         reuse_connections: false

**Race Fields:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 45

   * - Field
     - Required
     - Default
     - Description
   * - ``threads``
     - No
     - 20
     - Number of concurrent threads
   * - ``sync_mechanism``
     - No
     - barrier
     - Synchronization method
   * - ``connection_strategy``
     - No
     - preconnect
     - How connections are established
   * - ``thread_propagation``
     - No
     - single
     - How threads continue after race
   * - ``reuse_connections``
     - No
     - false
     - Reuse connections between threads

Synchronization Mechanisms
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Value
     - Description
   * - ``barrier``
     - All threads wait until the last one arrives, then all release simultaneously. **Recommended for race conditions** (< 1μs precision).
   * - ``countdown_latch``
     - Threads count down to zero, then all proceed. Similar to barrier but with explicit countdown.
   * - ``semaphore``
     - Limits concurrent execution with permits. Good for rate limiting tests, not optimal for races.

Connection Strategies
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Value
     - Description
   * - ``preconnect``
     - Establishes TCP/TLS connections before the synchronization point. **Recommended** - eliminates connection overhead and achieves < 1μs race window.
   * - ``lazy``
     - Connects on-demand when sending requests. Higher latency, poor for race testing.
   * - ``pooled``
     - Shares a connection pool between threads. Can serialize requests, not ideal for races.

Thread Propagation
^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Value
     - Description
   * - ``single``
     - Only the first successful thread continues to the next state. Best for simple race attacks.
   * - ``parallel``
     - All successful threads continue independently with their own context. Contexts are merged at the end for aggregate analysis.

Logger Configuration
~~~~~~~~~~~~~~~~~~~~

Add logging for debugging and analysis:

.. code-block:: yaml

   states:
     race_attack:
       logger:
         on_state_enter: |
           Starting attack...
           Initial balance: {{ balance }}
         
         on_state_leave: |
           Attack complete.
           Final balance: {{ balance }}
           {% if balance > initial_balance %}
           ⚠ VULNERABLE!
           {% endif %}
         
         on_thread_enter: |
           [Thread {{ thread.id }}/{{ thread.count }}] Starting...
         
         on_thread_leave: |
           [Thread {{ thread.id }}] Status: {{ status }}

**Logger Fields:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - ``on_state_enter``
     - Template logged when entering the state
   * - ``on_state_leave``
     - Template logged when leaving the state
   * - ``on_thread_enter``
     - Template logged when a thread starts (race states only)
   * - ``on_thread_leave``
     - Template logged when a thread completes (race states only)

Transitions
~~~~~~~~~~~

Define state transitions in the ``next`` block:

.. code-block:: yaml

   next:
     - on_status: 200
       goto: success_state
       delay_ms: 100
     - on_status: 401
       goto: retry_auth
     - on_status: 0
       goto: default_state

**Transition Fields:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``on_status``
     - No
     - HTTP status code that triggers this transition (0 = always)
   * - ``goto``
     - Yes
     - Name of the next state
   * - ``delay_ms``
     - No
     - Delay in milliseconds before transition

Complete Example
----------------

Here's a complete configuration example:

.. code-block:: yaml

   metadata:
     name: "E-commerce Race Condition Test"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-362"

   target:
     host: "shop.example.com"
     port: 443
     threads: 20
     tls:
       enabled: true
       verify_cert: true

   entrypoint:
     state: login
     input:
       username: "{{ argv('user', 'testuser') }}"
       password: "{{ env('PASSWORD', 'testpass') }}"

   states:
     login:
       description: "Authenticate user"
       request: |
         POST /api/auth/login HTTP/1.1
         Host: {{ target.host }}
         Content-Type: application/json
         
         {"username": "{{ username }}", "password": "{{ password }}"}
       
       extract:
         auth_token:
           type: jpath
           pattern: "$.token"
         initial_balance:
           type: jpath
           pattern: "$.user.balance"
       
       logger:
         on_state_leave: |
           Logged in successfully.
           Initial balance: {{ initial_balance }}
       
       next:
         - on_status: 200
           goto: race_redeem

     race_redeem:
       description: "Race condition attack on coupon redemption"
       request: |
         POST /api/coupons/redeem HTTP/1.1
         Host: {{ target.host }}
         Authorization: Bearer {{ login.auth_token }}
         Content-Type: application/json
         
         {"coupon_code": "DISCOUNT50"}
       
       race:
         threads: 10
         sync_mechanism: barrier
         connection_strategy: preconnect
         thread_propagation: single
       
       extract:
         new_balance:
           type: jpath
           pattern: "$.balance"
       
       logger:
         on_thread_enter: |
           [Thread {{ thread.id }}] Attempting redemption...
         on_thread_leave: |
           [Thread {{ thread.id }}] Status: {{ status }}, Balance: {{ new_balance }}
       
       next:
         - on_status: 200
           goto: verify
         - on_status: 400
           goto: end

     verify:
       description: "Verify final balance"
       request: |
         GET /api/user/balance HTTP/1.1
         Host: {{ target.host }}
         Authorization: Bearer {{ login.auth_token }}
       
       extract:
         final_balance:
           type: jpath
           pattern: "$.balance"
       
       logger:
         on_state_leave: |
           Initial balance: {{ login.initial_balance }}
           Final balance: {{ final_balance }}
           {% if final_balance > login.initial_balance %}
           ⚠ VULNERABLE: Balance increased unexpectedly!
           {% endif %}
       
       next:
         - on_status: 200
           goto: end

     end:
       description: "Test complete"

Best Practices
--------------

Configuration Tips
~~~~~~~~~~~~~~~~~~

1. **Use descriptive names**: Clear state names make debugging easier
2. **Add descriptions**: Document what each state does
3. **Use environment variables**: Never hardcode sensitive data
4. **Start with fewer threads**: Begin with 5-10, increase gradually
5. **Use preconnect + barrier**: Best combination for race conditions

Security Tips
~~~~~~~~~~~~~

1. **Store credentials safely**: Use ``env()`` filter for passwords and keys
2. **Disable cert verification carefully**: Only for testing environments
3. **Clean up test data**: Remove test accounts and transactions after testing

Performance Tips
~~~~~~~~~~~~~~~~

1. **Optimize thread count**: Usually 10-30 threads is optimal
2. **Use preconnect strategy**: Eliminates connection overhead
3. **Monitor race window**: Keep it under 1ms for reliable results
4. **Test network latency**: Lower latency = better precision

See Also
--------

* :doc:`extractors` - Data extraction methods
* :doc:`templates` - Template syntax and filters
* :doc:`examples` - Real-world attack examples
* :doc:`cli` - Command-line interface reference