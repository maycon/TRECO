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
     description: "Testing payment processing for race conditions"

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
     - No
     - Author of the attack scenario
   * - ``vulnerability``
     - No
     - CVE or CWE identifier (e.g., CWE-362)
   * - ``description``
     - No
     - Detailed description of the test

Config Section
--------------

The ``config`` section defines server and execution settings.

Basic Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   target:
     host: "api.example.com"
     port: 443
     threads: 20
     timeout: 30
     reuse_connection: false

**Basic Fields:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

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
     - Default number of concurrent threads
   * - ``timeout``
     - No
     - 30
     - Request timeout in seconds
   * - ``reuse_connection``
     - No
     - false
     - Whether to reuse TCP connections globally

TLS/SSL Configuration
~~~~~~~~~~~~~~~~~~~~~

Configure HTTPS and certificate validation:

.. code-block:: yaml

   target:
     tls:
       enabled: true
       verify_cert: true
       cert_path: "/path/to/ca-bundle.crt"  # Optional

**TLS Fields:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

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
     - true
     - Verify SSL/TLS certificates
   * - ``tls.cert_path``
     - No
     - None
     - Path to custom CA certificate bundle

**Example: Self-Signed Certificates**

.. code-block:: yaml

   target:
     host: "internal-api.company.com"
     port: 443
     tls:
       enabled: true
       verify_cert: false  # Only for testing!

.. warning::
   Disabling certificate verification (``verify_cert: false``) should only be done in testing environments. Never use this in production testing without explicit authorization.

HTTP Configuration
~~~~~~~~~~~~~~~~~~

Control HTTP client behavior:

.. code-block:: yaml

   target:
     http:
       follow_redirects: true

**HTTP Fields:**

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
     - Automatically follow HTTP 3xx redirects

**Example: Testing Redirect Logic**

.. code-block:: yaml

   target:
     http:
       follow_redirects: false  # Don't auto-follow

   states:
     test_redirect:
       request: |
         GET /redirect-endpoint HTTP/1.1
         Host: {{ config.host }}
       
       extract:
         redirect_location:
           type: header
           pattern: "Location"
       
       next:
         - on_status: 302
           goto: analyze_redirect

Proxy Configuration
~~~~~~~~~~~~~~~~~~~

Route requests through HTTP, HTTPS, or SOCKS5 proxies.

**Basic Proxy**

.. code-block:: yaml

   target:
     proxy:
       host: "proxy.example.com"
       port: 8080
       type: "http"  # Options: http, https, socks5

**Proxy with Authentication**

.. code-block:: yaml

   target:
     proxy:
       host: "proxy.example.com"
       port: 8080
       type: "http"
       auth:
         username: "{{ env('PROXY_USER') }}"
         password: "{{ env('PROXY_PASS') }}"

**Proxy Fields:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 45

   * - Field
     - Required
     - Default
     - Description
   * - ``proxy.host``
     - Yes*
     - None
     - Proxy server hostname or IP
   * - ``proxy.port``
     - Yes*
     - None
     - Proxy server port
   * - ``proxy.type``
     - No
     - http
     - Proxy type: ``http``, ``https``, or ``socks5``
   * - ``proxy.auth.username``
     - No
     - None
     - Username for proxy authentication
   * - ``proxy.auth.password``
     - No
     - None
     - Password for proxy authentication

\* Required if proxy configuration is present

**Proxy Types**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Type
     - Description
   * - ``http``
     - Standard HTTP proxy. Most common for corporate networks.
   * - ``https``
     - HTTPS proxy with encrypted connection to proxy server.
   * - ``socks5``
     - SOCKS5 proxy for protocol-agnostic proxying (e.g., Tor).

**Example: Corporate Proxy**

.. code-block:: yaml

   target:
     host: "internal-api.company.com"
     port: 443
     tls:
       enabled: true
     proxy:
       host: "proxy.company.com"
       port: 8080
       type: "http"
       auth:
         username: "{{ env('CORP_USER') }}"
         password: "{{ env('CORP_PASS') }}"

Run with:

.. code-block:: bash

   export CORP_USER="your-username"
   export CORP_PASS="your-password"
   treco corporate-test.yaml

**Example: Tor/SOCKS5 Proxy**

.. code-block:: yaml

   target:
     host: "target-api.example.com"
     port: 443
     tls:
       enabled: true
     proxy:
       host: "127.0.0.1"
       port: 9050  # Tor default port
       type: "socks5"

.. note::
   **Proxy Performance Impact**
   
   Using proxies adds latency that affects race window timing:
   
   * Direct connection: < 1μs race window
   * HTTP proxy: +10-50ms latency
   * HTTPS proxy: +20-80ms latency
   * SOCKS5/Tor: +200-1000ms latency
   
   For best race condition timing, avoid proxies or use local proxies when possible.

Complete Config Example
~~~~~~~~~~~~~~~~~~~~~~~

Here's a complete configuration with all options:

.. code-block:: yaml

   target:
     # Basic settings
     host: "api.example.com"
     port: 443
     threads: 20
     timeout: 60
     reuse_connection: false
     
     # TLS/SSL
     tls:
       enabled: true
       verify_cert: true
       cert_path: "/path/to/ca-bundle.crt"
     
     # HTTP behavior
     http:
       follow_redirects: true
     
     # Proxy configuration
     proxy:
       host: "proxy.example.com"
       port: 8080
       type: "http"
       auth:
         username: "{{ env('PROXY_USER') }}"
         password: "{{ env('PROXY_PASS') }}"

Entrypoint Section
-------------------

The ``entrypoint`` section defines starting points for execution.

.. code-block:: yaml

   entrypoint:
     state: login
     input:
       username: "{{ argv('user', 'testuser') }}"
       password: "{{ env('PASSWORD') }}"
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
         Host: {{ config.host }}
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
     - Human-readable description
   * - ``request``
     - No*
     - HTTP request template (required for non-terminal states)
   * - ``extract``
     - No
     - Variable extraction patterns
   * - ``race``
     - No
     - Race attack configuration
   * - ``logger``
     - No
     - Logging configuration
   * - ``next``
     - No
     - State transitions

\* Required unless state is terminal (end state)

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
   * - ``permits``
     - No
     - None
     - Number of permits (semaphore only)

Synchronization Mechanisms
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Value
     - Description
   * - ``barrier``
     - All threads wait until the last one arrives, then all release simultaneously. **Recommended for race conditions** (< 1μs precision with Python 3.14t).
   * - ``countdown_latch``
     - Threads count down to zero, then all proceed. Similar to barrier but with explicit countdown. Good for multi-stage attacks.
   * - ``semaphore``
     - Limits concurrent execution with permits. Good for rate limiting tests, not optimal for races.

**Example: Barrier (Recommended)**

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: barrier
     connection_strategy: preconnect

**Example: Semaphore (Rate Limiting)**

.. code-block:: yaml

   race:
     threads: 100
     sync_mechanism: semaphore
     permits: 10  # Max 10 concurrent

For detailed information, see :doc:`synchronization`.

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
     - Connects on-demand when sending requests. Higher latency, poor for race testing. Use only when testing connection timing.
   * - ``pooled``
     - Shares a connection pool between threads. Can serialize requests, not ideal for races. Use for sequential testing.
   * - ``multiplexed``
     - Single HTTP/2 connection shared by all threads. Use for HTTP/2-specific testing only.

**Recommendation:**

Always use ``preconnect`` for race condition testing. Other strategies are for specific scenarios only.

For detailed information, see :doc:`connection-strategies`.

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
     - All successful threads continue independently with their own context. Use for multi-stage race attacks.

**Example: Single Propagation (Default)**

.. code-block:: yaml

   race:
     threads: 20
     thread_propagation: single  # Only one continues

**Example: Parallel Propagation**

.. code-block:: yaml

   race:
     threads: 20
     thread_propagation: parallel  # All continue

Data Extraction
~~~~~~~~~~~~~~~

Extract data from responses using various methods:

.. code-block:: yaml

   extract:
     # JSONPath
     token:
       type: jpath
       pattern: "$.access_token"
     
     # XPath
     csrf_token:
       type: xpath
       pattern: '//input[@name="csrf"]/@value'
     
     # Regular Expression
     session_id:
       type: regex
       pattern: "SESSION=([A-Z0-9]+)"
     
     # HTTP Header
     rate_limit:
       type: header
       pattern: "X-RateLimit-Remaining"
     
     # Cookie
     auth_cookie:
       type: cookie
       pattern: "session"
     
     # With default value
     optional_field:
       type: jpath
       pattern: "$.optional.field"
       default: "not_found"

**Extractor Types:**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Type
     - Description
   * - ``jpath``
     - JSONPath expressions for JSON responses
   * - ``xpath``
     - XPath expressions for XML/HTML responses
   * - ``regex``
     - Regular expressions for pattern matching
   * - ``boundary``
     - Extract text between delimiters
   * - ``header``
     - Extract HTTP response headers
   * - ``cookie``
     - Extract cookie values from Set-Cookie headers

For detailed information and examples, see :doc:`extractors`.

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
           [Thread {{ thread.id }}] Status: {{ status }}, Time: {{ response_time }}ms

**Logger Fields:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - ``on_state_enter``
     - Template logged when entering the state (once per state)
   * - ``on_state_leave``
     - Template logged when leaving the state (once per state)
   * - ``on_thread_enter``
     - Template logged when a thread starts (race states only, per thread)
   * - ``on_thread_leave``
     - Template logged when a thread completes (race states only, per thread)

**Available Variables in Logger:**

* ``thread.id`` - Thread number (0-based)
* ``thread.count`` - Total thread count
* ``status`` - HTTP status code
* ``response_time`` - Response time in milliseconds
* All extracted variables
* All context variables from previous states

Transitions
~~~~~~~~~~~

Define state transitions in the ``next`` block:

.. code-block:: yaml

   next:
     - on_status: 200
       goto: success_state
       delay_ms: 100
     
     - on_status: [401, 403]
       goto: auth_error
     
     - on_status: [500, 502, 503]
       goto: server_error
     
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
     - HTTP status code(s) that trigger this transition. Can be single integer or list. Use 0 for default/catch-all.
   * - ``goto``
     - Yes
     - Name of the next state
   * - ``delay_ms``
     - No
     - Delay in milliseconds before transition

**Transition Matching:**

1. Transitions are evaluated in order
2. First matching status code wins
3. ``on_status: 0`` matches any status (use as catch-all at end)
4. Status can be single value or list: ``[200, 201, 202]``

Complete Example
----------------

Here's a complete configuration example with all features:

.. code-block:: yaml

   metadata:
     name: "Advanced E-commerce Race Test"
     version: "2.0"
     author: "Security Team"
     vulnerability: "CWE-362"
     description: "Testing coupon redemption for race conditions"

   target:
     # Basic settings
     host: "shop.example.com"
     port: 443
     threads: 20
     timeout: 60
     reuse_connection: false
     
     # TLS configuration
     tls:
       enabled: true
       verify_cert: true
     
     # HTTP behavior
     http:
       follow_redirects: true
     
     # Proxy configuration (optional)
     proxy:
       host: "proxy.company.com"
       port: 8080
       type: "http"
       auth:
         username: "{{ env('PROXY_USER') }}"
         password: "{{ env('PROXY_PASS') }}"

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
         Host: {{ config.host }}
         Content-Type: application/json
         
         {"username": "{{ username }}", "password": "{{ password }}"}
       
       extract:
         auth_token:
           type: jpath
           pattern: "$.token"
         initial_balance:
           type: jpath
           pattern: "$.user.balance"
         rate_limit:
           type: header
           pattern: "X-RateLimit-Remaining"
       
       logger:
         on_state_leave: |
           ✓ Logged in successfully
           Initial balance: ${{ initial_balance }}
           Rate limit: {{ rate_limit }}
       
       next:
         - on_status: 200
           goto: race_redeem
         - on_status: 401
           goto: auth_failed

     race_redeem:
       description: "Race condition attack on coupon redemption"
       request: |
         POST /api/coupons/redeem HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.auth_token }}
         Content-Type: application/json
         
         {"coupon_code": "DISCOUNT50"}
       
       race:
         threads: 20
         sync_mechanism: barrier
         connection_strategy: preconnect
         thread_propagation: single
         reuse_connections: false
       
       extract:
         new_balance:
           type: jpath
           pattern: "$.balance"
           default: 0
       
       logger:
         on_thread_enter: |
           [Thread {{ thread.id }}] Attempting redemption...
         
         on_thread_leave: |
           [Thread {{ thread.id }}] Status: {{ status }}, Balance: ${{ new_balance }}
         
         on_state_leave: |
           Race attack completed
           Successful threads: {{ successful_threads }}
           Race window: {{ race_window }}ms
       
       next:
         - on_status: 200
           goto: verify
         - on_status: 400
           goto: end

     verify:
       description: "Verify final balance"
       request: |
         GET /api/user/balance HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.auth_token }}
       
       extract:
         final_balance:
           type: jpath
           pattern: "$.balance"
       
       logger:
         on_state_leave: |
           ═══════════════════════════════════════
           VULNERABILITY ASSESSMENT
           ═══════════════════════════════════════
           Initial balance: ${{ login.initial_balance }}
           Final balance: ${{ final_balance }}
           Difference: ${{ final_balance - login.initial_balance }}
           
           {% if final_balance > login.initial_balance %}
           🚨 VULNERABLE: Race condition detected!
           🚨 Balance increased unexpectedly!
           {% else %}
           ✓ No vulnerability detected
           {% endif %}
       
       next:
         - on_status: 200
           goto: end

     auth_failed:
       description: "Authentication failed"
       logger:
         on_state_enter: |
           ❌ Authentication failed
       next:
         - on_status: 0
           goto: end

     end:
       description: "Test complete"

Best Practices
--------------

Configuration Tips
~~~~~~~~~~~~~~~~~~

1. **Use descriptive names**: Clear state names make debugging easier

   .. code-block:: yaml
   
      # Good
      states:
        authenticate_user:
        validate_coupon:
        race_redemption:
      
      # Bad
      states:
        state1:
        state2:
        state3:

2. **Add descriptions**: Document what each state does

   .. code-block:: yaml
   
      states:
        login:
          description: "Authenticate user and obtain JWT token"

3. **Use environment variables**: Never hardcode sensitive data

   .. code-block:: yaml
   
      # Good
      input:
        password: "{{ env('PASSWORD') }}"
        api_key: "{{ env('API_KEY') }}"
      
      # Bad
      input:
        password: "MyPassword123"
        api_key: "sk-1234567890"

4. **Start with fewer threads**: Begin with 5-10, increase gradually

   .. code-block:: yaml
   
      race:
        threads: 10  # Start here, increase if needed

5. **Use preconnect + barrier**: Best combination for race conditions

   .. code-block:: yaml
   
      race:
        sync_mechanism: barrier
        connection_strategy: preconnect

Security Tips
~~~~~~~~~~~~~

1. **Store credentials safely**: Use ``env()`` filter for passwords and keys

2. **Disable cert verification carefully**: Only for testing environments

   .. code-block:: yaml
   
      tls:
        verify_cert: false  # Only in test environments!

3. **Use proxies for anonymity**: When required by scope or for privacy

4. **Document authorization**: Include authorization details in metadata

   .. code-block:: yaml
   
      metadata:
        authorization: "Approved by security@example.com - Ticket #12345"
        scope: "staging.example.com only"

5. **Clean up test data**: Remove test accounts and transactions after testing

Performance Tips
~~~~~~~~~~~~~~~~

1. **Optimize thread count**: Usually 10-30 threads is optimal

   * Too few: May not trigger race condition
   * Too many: Network congestion, slower timing

2. **Use preconnect strategy**: Eliminates connection overhead

   .. code-block:: yaml
   
      race:
        connection_strategy: preconnect  # < 1μs race window

3. **Monitor race window**: Keep it under 10ms for reliable results

   .. code-block:: yaml
   
      logger:
        on_state_leave: |
          Race window: {{ race_window }}ms
          {% if race_window < 1 %}✓ Excellent
          {% elif race_window < 10 %}✓ Very Good
          {% elif race_window < 100 %}⚠ Good
          {% else %}❌ Poor{% endif %}

4. **Test network latency**: Lower latency = better precision

   .. code-block:: bash
   
      # Check latency
      ping api.example.com
      
      # Optimal: < 10ms
      # Good: 10-50ms
      # Poor: > 100ms

5. **Avoid proxies for race testing**: Unless absolutely necessary

   * Direct connection: < 1μs race window
   * With proxy: 50-200ms race window

6. **Use Python 3.14t**: For best performance (GIL-free)

   .. code-block:: bash
   
      # Install Python 3.14t
      uv python install 3.14t
      uv sync

Troubleshooting
~~~~~~~~~~~~~~~

**Issue: Poor race window (> 100ms)**

*Solution:*

.. code-block:: yaml

   race:
     sync_mechanism: barrier       # Use barrier, not semaphore
     connection_strategy: preconnect  # Essential!
     threads: 20                   # Reduce if very high

**Issue: Connection timeouts**

*Solution:*

.. code-block:: yaml

   target:
     timeout: 60  # Increase timeout
   
   race:
     threads: 10  # Reduce thread count

**Issue: Proxy authentication fails**

*Solution:*

.. code-block:: bash

   # Verify environment variables
   echo $PROXY_USER
   echo $PROXY_PASS
   
   # Test proxy manually
   curl -x http://user:pass@proxy:8080 https://api.example.com

**Issue: SSL certificate errors**

*Solution:*

.. code-block:: yaml

   target:
     tls:
       verify_cert: false  # Only for testing!
       # Or provide custom CA bundle
       cert_path: "/path/to/ca-bundle.crt"

See Also
--------

* :doc:`synchronization` - Synchronization mechanisms in detail
* :doc:`connection-strategies` - Connection strategies explained
* :doc:`extractors` - Data extraction methods
* :doc:`templates` - Template syntax and filters
* :doc:`examples` - Real-world attack examples
* :doc:`cli` - Command-line interface reference
* :doc:`troubleshooting` - Common issues and solutions