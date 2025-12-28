Troubleshooting
===============

This guide helps you diagnose and fix common issues when using TRECO.

----

Quick Diagnostic Checklist
---------------------------

Before diving into specific issues, run through this checklist:

.. code-block:: bash

   # 1. Verify installation
   treco --version
   
   # 2. Check Python version
   python --version
   
   # 3. Test basic connectivity
   ping api.example.com
   
   # 4. Verify dependencies
   pip list | grep -E "httpx|jinja2|pyyaml"
   
   # 5. Check configuration syntax
   treco your-config.yaml --dry-run  # If supported

----

Installation Issues
-------------------

Issue: "treco: command not found"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: bash

   $ treco --version
   bash: treco: command not found

**Causes:**

* TRECO not installed
* Virtual environment not activated
* Installation path not in PATH

**Solutions:**

.. code-block:: bash

   # Solution 1: Install from PyPI
   pip install treco-framework
   
   # Solution 2: Activate virtual environment
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   
   # Solution 3: Install with uv
   uv pip install treco-framework
   
   # Solution 4: Use full path
   python -m treco --version

Issue: Wrong Python Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Python 3.9 is not supported
   Requires Python 3.10 or later

**Solution:**

.. code-block:: bash

   # Check current version
   python --version
   
   # Install Python 3.10+ with uv
   uv python install 3.12
   
   # Create environment with specific version
   uv venv --python 3.12
   
   # Or use system Python 3.10+
   python3.12 -m venv .venv
   source .venv/bin/activate

Issue: Dependency Installation Fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Could not find a version that satisfies the requirement httpx>=0.27.0

**Solutions:**

.. code-block:: bash

   # Update pip
   pip install --upgrade pip
   
   # Install with uv (handles dependencies better)
   uv pip install treco-framework
   
   # Manual dependency installation
   pip install httpx>=0.27.0 pyyaml>=6.0.1 jinja2>=3.1.2

----

Configuration Issues
--------------------

Issue: YAML Syntax Error
~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Invalid YAML syntax at line 45
   yaml.scanner.ScannerError: mapping values are not allowed here

**Common Causes:**

1. **Incorrect indentation**

   .. code-block:: yaml
   
      # Wrong
      states:
        login:
        description: "Login"  # Missing indent
      
      # Correct
      states:
        login:
          description: "Login"

2. **Missing colons**

   .. code-block:: yaml
   
      # Wrong
      config
        host: "example.com"
      
      # Correct
      target:
        host: "example.com"

3. **Unescaped special characters**

   .. code-block:: yaml
   
      # Wrong
      description: "Test: Race condition"
      
      # Correct
      description: "Test - Race condition"
      # Or use quotes
      description: 'Test: Race condition'

**Solution:**

Use a YAML validator:

.. code-block:: bash

   # Install yamllint
   pip install yamllint
   
   # Validate configuration
   yamllint your-config.yaml

Issue: Template Rendering Error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Undefined variable 'token'
   jinja2.exceptions.UndefinedError: 'token' is undefined

**Causes:**

* Variable not extracted from previous state
* Typo in variable name
* State not executed before reference

**Solutions:**

.. code-block:: yaml

   # 1. Verify variable extraction
   states:
     login:
       extract:
         token:  # Must match reference name
           type: jpath
           pattern: "$.access_token"
     
     use_token:
       request: |
         Authorization: Bearer {{ login.token }}  # Prefix with state name

            # 2. Use default values
            {{ token | default('fallback-token') }}
            
            # 3. Check variable exists
            {% if token %}
                {{ token }}
            {% else %}
                No token available
            {% endif %}
   
   # 4. Debug available variables
   logger:
     on_state_enter: |
       Available: {{ context.keys() | list }}

Issue: Invalid Configuration Value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Invalid sync_mechanism: 'barier'
   Valid options: barrier, countdown_latch, semaphore

**Solution:**

Check spelling and valid values:

.. code-block:: yaml

   race:
     # Valid synchronization mechanisms
     sync_mechanism: barrier  # NOT 'barier' or 'Barrier'
     
     # Valid connection strategies
     connection_strategy: preconnect  # NOT 'pre-connect' or 'PreConnect'
     
     # Valid thread propagation
     thread_propagation: single  # NOT 'Single' or 'one'

----

Connection Issues
-----------------

Issue: Connection Timeout
~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Connection timeout after 30s
   httpx.ConnectTimeout

**Causes:**

* Server not reachable
* Firewall blocking connection
* Too many concurrent connections
* Network latency too high

**Solutions:**

.. code-block:: yaml

   # Solution 1: Increase timeout
   target:
     timeout: 60  # Increase from default 30s
   
   # Solution 2: Reduce thread count
   race:
     threads: 10  # Reduce from 50
   
   # Solution 3: Check connectivity
   # Run in terminal:
   # curl -I https://api.example.com
   # ping api.example.com

.. code-block:: bash

   # Solution 4: Check firewall
   telnet api.example.com 443
   
   # Solution 5: Use proxy if needed
   # See proxy configuration in docs

Issue: SSL Certificate Error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: SSL certificate verify failed
   ssl.SSLCertVerificationError: certificate verify failed

**Causes:**

* Self-signed certificate
* Expired certificate
* Certificate chain issue
* Corporate proxy intercepting SSL

**Solutions:**

.. code-block:: yaml

   # Solution 1: Disable verification (TESTING ONLY!)
   target:
     tls:
       enabled: true
       verify_cert: false  # Only for testing!
   
   # Solution 2: Provide CA bundle
   target:
     tls:
       enabled: true
       verify_cert: true
       cert_path: "/path/to/ca-bundle.crt"

.. code-block:: bash

   # Solution 3: Update CA certificates
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install ca-certificates
   
   # macOS
   brew install ca-certificates
   
   # Solution 4: Get certificate chain
   openssl s_client -connect api.example.com:443 -showcerts

Issue: Too Many Open Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: [Errno 24] Too many open files
   OSError: [Errno 24] Too many open files

**Cause:**

Using ``preconnect`` strategy with high thread count exceeds file descriptor limit.

**Solutions:**

.. code-block:: bash

   # Solution 1: Check current limit
   ulimit -n
   
   # Solution 2: Increase limit (temporary)
   ulimit -n 4096
   
   # Solution 3: Increase limit (permanent)
   # Add to /etc/security/limits.conf:
   * soft nofile 4096
   * hard nofile 8192

.. code-block:: yaml

   # Solution 4: Reduce thread count
   race:
     threads: 50  # Reduce from 200

Issue: Connection Refused
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Connection refused
   httpx.ConnectError: [Errno 111] Connection refused

**Causes:**

* Wrong host or port
* Service not running
* Firewall blocking access

**Solutions:**

.. code-block:: bash

   # Verify host and port
   telnet api.example.com 443
   
   # Check if service is running
   curl https://api.example.com/health
   
   # Verify DNS resolution
   nslookup api.example.com

.. code-block:: yaml

   # Check configuration
   target:
     host: "api.example.com"  # Verify correct hostname
     port: 443                # Verify correct port

----

Proxy Issues
------------

Issue: Proxy Authentication Failed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Proxy authentication required
   httpx.ProxyError: 407 Proxy Authentication Required

**Solutions:**

.. code-block:: yaml

   # Verify proxy authentication
   target:
     proxy:
       host: "proxy.example.com"
       port: 8080
       auth:
         username: "{{ env('PROXY_USER') }}"
         password: "{{ env('PROXY_PASS') }}"

.. code-block:: bash

   # Check environment variables
   echo $PROXY_USER
   echo $PROXY_PASS
   
   # Export if not set
   export PROXY_USER="your-username"
   export PROXY_PASS="your-password"
   
   # Test proxy manually
   curl -x http://user:pass@proxy.example.com:8080 https://api.example.com

Issue: Proxy Connection Failed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Cannot connect to proxy
   httpx.ProxyError: Cannot connect to proxy

**Solutions:**

.. code-block:: yaml

   # Verify proxy configuration
   target:
     proxy:
       host: "proxy.example.com"  # Check hostname
       port: 8080                 # Check port
       type: "http"               # Check type

.. code-block:: bash

   # Test proxy connectivity
   telnet proxy.example.com 8080
   
   # Test with curl
   curl -x http://proxy.example.com:8080 https://api.example.com

Issue: Slow Performance with Proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom:**

Race window > 200ms when using proxy.

**Explanation:**

Proxies add significant latency. This is expected behavior.

**Solutions:**

1. Use local proxy if possible
2. Use direct connection for race testing
3. Accept higher race window
4. Test proxy latency:

.. code-block:: bash

   # Measure proxy latency
   time curl -x http://proxy:8080 https://api.example.com

----

Race Condition Issues
---------------------

Issue: Poor Race Window (> 100ms)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   Race window: 150ms
   ⚠ Poor race window

**Causes:**

* Not using preconnect strategy
* Using semaphore instead of barrier
* High network latency
* Using proxy

**Solutions:**

.. code-block:: yaml

   # Solution 1: Use optimal configuration
   race:
     sync_mechanism: barrier           # Must use barrier!
     connection_strategy: preconnect   # Must use preconnect!
     threads: 20                       # Moderate thread count

.. code-block:: bash

   # Solution 2: Test network latency
   ping -c 10 api.example.com
   # Should be < 50ms for good results
   
   # Solution 3: Use Python 3.14t
   uv python install 3.14t
   uv sync

.. code-block:: yaml

   # Solution 4: Remove proxy if possible
   target:
     # proxy:  # Comment out proxy
     #   host: "proxy.example.com"

Issue: No Successful Race Attacks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

All threads succeed with status 200, but race condition not triggered.

**Possible Causes:**

1. **Application has proper locking**

   .. code-block:: text
   
      ✓ This is actually good news!
      The application is properly protected.

2. **Race window too large**

   .. code-block:: yaml
   
      # Optimize configuration
      race:
        sync_mechanism: barrier
        connection_strategy: preconnect

3. **Wrong endpoint tested**

   .. code-block:: text
   
      Make sure you're testing vulnerable endpoint

4. **Authentication required**

   .. code-block:: yaml
   
      # Ensure token is valid
      request: |
        Authorization: Bearer {{ login.token }}

Issue: Inconsistent Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

Race condition triggers sometimes but not always.

**Cause:**

This is the nature of race conditions - they're non-deterministic.

**Solutions:**

1. **Run multiple times**

   .. code-block:: bash
   
      # Run 10 times and check results
      for i in {1..10}; do
        echo "Run $i"
        treco attack.yaml
      done

2. **Increase thread count**

   .. code-block:: yaml
   
      race:
        threads: 50  # More attempts

3. **Optimize timing**

   .. code-block:: yaml
   
      race:
        sync_mechanism: barrier
        connection_strategy: preconnect

4. **Check race window**

   .. code-block:: yaml
   
      logger:
        on_state_leave: |
          Race window: {{ race_window }}ms
          # Should be < 10ms

----

Extractor Issues
----------------

Issue: Extractor Returns Nothing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   WARNING: Could not extract 'token'
   Variable 'token' is undefined

**Solutions:**

.. code-block:: yaml

   # Solution 1: Add default value
   extract:
     token:
       type: jpath
       pattern: "$.access_token"
       default: "not_found"  # Fallback value
   
   # Solution 2: Debug response
   logger:
     on_state_leave: |
       Response body: {{ response_body }}
       Status: {{ status }}
   
   # Solution 3: Verify pattern
   # For JSONPath, test at: https://jsonpath.com/
   # For XPath, test at: https://www.freeformatter.com/xpath-tester.html

Issue: JSONPath Pattern Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

Pattern doesn't match expected value.

**Common Issues:**

.. code-block:: yaml

   # Wrong: Missing $
   pattern: "access_token"
   
   # Correct: Must start with $
   pattern: "$.access_token"
   
   # Wrong: Incorrect nested access
   pattern: "$.user-balance"
   
   # Correct: Use dot notation
   pattern: "$.user.balance"
   
   # Wrong: Array access
   pattern: "$.items"
   
   # Correct: Get first item
   pattern: "$.items[0].name"

**Test Pattern:**

.. code-block:: bash

   # Install jq for testing
   # Ubuntu/Debian
   sudo apt-get install jq
   
   # Test JSONPath-like queries
   echo '{"user":{"balance":100}}' | jq '.user.balance'

Issue: Regex Pattern Not Matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Common Issues:**

.. code-block:: yaml

   # Wrong: Not escaping special characters
   pattern: "token=([A-Z0-9]+)"
   
   # Correct: Escape backslashes in YAML
   pattern: "token=([A-Z0-9]+)"
   
   # Wrong: Greedy matching
   pattern: "START(.*)END"
   
   # Correct: Non-greedy matching
   pattern: "START(.*?)END"

**Test Pattern:**

.. code-block:: bash

   # Test regex online: https://regex101.com/
   # Or with Python:
   python3 -c "import re; print(re.search(r'token=([A-Z0-9]+)', 'token=ABC123').group(1))"

Issue: XPath Pattern Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Common Issues:**

.. code-block:: yaml

   # Wrong: Incorrect attribute access
   pattern: "//input[@name=csrf]/@value"
   
   # Correct: Quotes around attribute value
   pattern: '//input[@name="csrf"]/@value'
   
   # Wrong: Case sensitivity
   pattern: "//Input[@name='csrf']/@value"
   
   # Correct: Correct case
   pattern: '//input[@name="csrf"]/@value'

----

Performance Issues
------------------

Issue: Slow Execution
~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

Attack takes much longer than expected.

**Causes and Solutions:**

1. **High thread count**

   .. code-block:: yaml
   
      # Reduce threads
      race:
        threads: 20  # Instead of 200

2. **Network latency**

   .. code-block:: bash
   
      # Check latency
      ping api.example.com
      
      # Test on localhost or local network

3. **Slow endpoint**

   .. code-block:: yaml
   
      # Increase timeout
      target:
        timeout: 120  # For slow endpoints

4. **Not using preconnect**

   .. code-block:: yaml
   
      # Use preconnect
      race:
        connection_strategy: preconnect

Issue: High Memory Usage
~~~~~~~~~~~~~~~~~~~~~~~~~

**Cause:**

Many threads with preconnect strategy.

**Solutions:**

.. code-block:: yaml

   # Solution 1: Reduce threads
   race:
     threads: 20  # Instead of 200
   
   # Solution 2: Use pooled strategy (if race timing not critical)
   race:
     connection_strategy: pooled
     pool_size: 10

.. code-block:: bash

   # Solution 3: Monitor memory
   # Linux
   top -p $(pgrep python)
   
   # macOS
   top -pid $(pgrep python)

----

Logging Issues
--------------

Issue: No Log Output
~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

No logs appear during execution.

**Solutions:**

.. code-block:: yaml

   # Add logger configuration
   states:
     test:
       logger:
         on_state_enter: "Starting test..."
         on_state_leave: "Test complete"

.. code-block:: bash

   # Use verbose mode
   treco attack.yaml --verbose
   
   # Check log level
   export TRECO_LOG_LEVEL=DEBUG
   treco attack.yaml

Issue: Template Syntax Error in Logger
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Template syntax error in logger
   jinja2.exceptions.TemplateSyntaxError

**Solutions:**

.. code-block:: yaml

   # Wrong: Missing endif
   logger:
     on_state_leave: |
       {% if vulnerable %}
         VULNERABLE!
   
   # Correct: Proper closure
   logger:
     on_state_leave: |
       {% if vulnerable %}
         VULNERABLE!
       {% endif %}
   
   # Wrong: Invalid filter
   logger:
     on_state_leave: |
       Balance: {{ balance | invalid_filter }}
   
   # Correct: Valid filter
   logger:
     on_state_leave: |
       Balance: {{ balance | round(2) }}

----

Template Issues
---------------

Issue: TOTP Code Always Invalid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

TOTP codes generated but authentication fails.

**Causes:**

* Incorrect TOTP secret
* System time not synchronized
* Wrong time step

**Solutions:**

.. code-block:: bash

   # Solution 1: Verify system time
   date
   
   # Solution 2: Synchronize time
   # Ubuntu/Debian
   sudo ntpdate pool.ntp.org
   
   # macOS
   sudo sntp -sS time.apple.com
   
   # Solution 3: Verify TOTP secret format
   # Must be base32 encoded, e.g., JBSWY3DPEHPK3PXP

.. code-block:: yaml

   # Correct TOTP usage
   request: |
     {"totp": "{{ totp(env('TOTP_SECRET')) }}"}

Issue: Environment Variable Not Found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**

.. code-block:: text

   ERROR: Environment variable 'API_KEY' not found

**Solutions:**

.. code-block:: bash

   # Solution 1: Export variable
   export API_KEY="your-api-key"
   
   # Solution 2: Create .env file
   echo "API_KEY=your-api-key" > .env
   source .env
   
   # Solution 3: Verify variable
   echo $API_KEY

.. code-block:: yaml

   # Use default value
   api_key: "{{ env('API_KEY', 'default-key') }}"

----

Common Error Messages
---------------------

"Rate limit exceeded"
~~~~~~~~~~~~~~~~~~~~~

**Meaning:** Target API is rate limiting requests.

**Solutions:**

1. Reduce thread count
2. Add delays between requests
3. Use different API keys
4. Test on dedicated test environment

"Authentication failed"
~~~~~~~~~~~~~~~~~~~~~~~

**Meaning:** Credentials invalid or token expired.

**Solutions:**

1. Verify credentials
2. Check token extraction
3. Ensure token not expired
4. Verify authentication endpoint

"Invalid JSON"
~~~~~~~~~~~~~~

**Meaning:** Response is not valid JSON.

**Solutions:**

1. Check if endpoint returns JSON
2. Verify Content-Type header
3. Use text/HTML extractors instead
4. Debug response body

----

Getting More Help
-----------------

Debug Mode
~~~~~~~~~~

Enable verbose logging:

.. code-block:: bash

   # Verbose mode
   treco attack.yaml --verbose
   
   # Debug mode (if available)
   export TRECO_LOG_LEVEL=DEBUG
   treco attack.yaml

Check Logs
~~~~~~~~~~

.. code-block:: yaml

   # Add debug logging
   logger:
     on_state_enter: |
       === STATE: {{ state.name }} ===
       Context: {{ context.keys() | list }}
       target: {{ config }}
     
     on_state_leave: |
       Status: {{ status }}
       Response: {{ response_body[:200] }}
       Extracted: {{ extracted_vars }}

Test Connectivity
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test with curl
   curl -v https://api.example.com/endpoint
   
   # Test with Python
   python3 -c "import httpx; print(httpx.get('https://api.example.com'))"

Minimal Reproduction
~~~~~~~~~~~~~~~~~~~~

Create minimal config that reproduces the issue:

.. code-block:: yaml

   metadata:
     name: "Minimal Test"
   
   target:
     host: "httpbin.org"
     port: 443
     tls:
       enabled: true
   
   entrypoint:
     state: test
   
   states:
     test:
       request: |
         GET /get HTTP/1.1
         Host: {{ config.host }}
       
       next:
         - on_status: 200
           goto: end
     
     end:
       description: "Done"

Report Issue
~~~~~~~~~~~~

If problem persists:

1. **Check existing issues**: https://github.com/maycon/TRECO/issues
2. **Create new issue** with:
   
   * TRECO version: ``treco --version``
   * Python version: ``python --version``
   * Operating system
   * Complete error message
   * Minimal configuration (sanitized)
   * Steps to reproduce

3. **Community support**: https://github.com/maycon/TRECO/discussions

----

See Also
--------

* :doc:`configuration` - Complete configuration reference
* :doc:`best-practices` - Performance and security tips
* :doc:`examples` - Working examples
* `GitHub Issues <https://github.com/maycon/TRECO/issues>`_ - Report bugs
* `GitHub Discussions <https://github.com/maycon/TRECO/discussions>`_ - Get help