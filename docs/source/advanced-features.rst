Advanced Features
=================

This document covers advanced TRECO features for specialized testing scenarios.

.. contents:: Table of Contents
   :local:
   :depth: 2

mTLS (Mutual TLS) Support
--------------------------

TRECO supports mutual TLS authentication for certificate-based authentication.

Why mTLS?
~~~~~~~~~

Many enterprise applications require mutual TLS:

- **Financial Services**: Banking APIs, payment processors
- **Healthcare Systems**: HIPAA-compliant endpoints
- **Government & Military**: Classified systems
- **Zero-Trust Architecture**: Internal microservices
- **IoT Devices**: Device-to-server authentication

Configuration
~~~~~~~~~~~~~

**Separate Certificate and Key Files**:

.. code-block:: yaml

   config:
     host: secure-api.internal
     port: 443
     tls:
       enabled: true
       verify_cert: true
       client_cert: "./certs/client.crt"
       client_key: "./certs/client.key"
       client_key_password: "{{ env('CLIENT_KEY_PASSWORD') }}"  # Optional

**Combined PEM File**:

.. code-block:: yaml

   config:
     tls:
       enabled: true
       verify_cert: true
       client_pem: "./certs/client.pem"

**PKCS12 Conversion**:

PKCS12 format (.pfx/.p12) must be converted to PEM:

.. code-block:: bash

   # Convert to combined PEM
   openssl pkcs12 -in client.pfx -out client.pem -nodes
   
   # Or separate files
   openssl pkcs12 -in client.pfx -clcerts -nokeys -out client.crt
   openssl pkcs12 -in client.pfx -nocerts -nodes -out client.key

Template Support
~~~~~~~~~~~~~~~~

Certificate paths support Jinja2 templates:

.. code-block:: yaml

   config:
     tls:
       client_cert: "{{ env('CERT_PATH') }}/client.crt"
       client_key: "{{ env('CERT_PATH') }}/client.key"
       client_key_password: "{{ env('KEY_PASSWORD') }}"

Example
~~~~~~~

.. code-block:: yaml

   metadata:
     name: "mTLS API Test"
   
   config:
     host: secure-api.example.com
     port: 443
     tls:
       enabled: true
       verify_cert: true
       client_cert: "./certs/client.crt"
       client_key: "./certs/client.key"
   
   entrypoint:
     state: test_mtls
     input: {}
   
   states:
     test_mtls:
       race:
         threads: 10
       
       request: |
         GET /api/secure/data HTTP/1.1
         Host: {{ config.host }}

Proxy Support
-------------

TRECO supports HTTP, HTTPS, and SOCKS5 proxies with authentication.

Configuration
~~~~~~~~~~~~~

**HTTP/HTTPS Proxy**:

.. code-block:: yaml

   config:
     proxy:
       http: "http://proxy.example.com:8080"
       https: "http://proxy.example.com:8080"

**With Authentication**:

.. code-block:: yaml

   config:
     proxy:
       http: "http://user:pass@proxy.example.com:8080"
       https: "http://user:pass@proxy.example.com:8080"

**SOCKS5 Proxy**:

.. code-block:: yaml

   config:
     proxy:
       http: "socks5://localhost:9050"
       https: "socks5://localhost:9050"

**Environment Variables**:

.. code-block:: yaml

   config:
     proxy:
       http: "{{ env('HTTP_PROXY') }}"
       https: "{{ env('HTTPS_PROXY') }}"

Use Cases
~~~~~~~~~

1. **Corporate Networks**: Route through corporate proxy
2. **Tor Network**: Use SOCKS5 for anonymity
3. **Debugging**: Capture traffic with Burp Suite/mitmproxy
4. **IP Rotation**: Rotate IPs via proxy services
5. **Geo-Restriction Bypass**: Access region-locked APIs

Example with Burp Suite
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   config:
     host: api.example.com
     port: 443
     tls:
       enabled: true
       verify_cert: false  # Burp uses self-signed cert
     proxy:
       http: "http://127.0.0.1:8080"
       https: "http://127.0.0.1:8080"

HTTP/2 Support
--------------

TRECO supports HTTP/2 via the multiplexed connection strategy.

Configuration
~~~~~~~~~~~~~

.. code-block:: yaml

   config:
     host: api.example.com
     port: 443
     tls:
       enabled: true
     http2: true  # Enable HTTP/2
   
   states:
     test:
       race:
         threads: 20
         connection_strategy: multiplexed  # Required for HTTP/2

Benefits
~~~~~~~~

- **Multiplexing**: Multiple requests over single connection
- **Header Compression**: Reduced bandwidth
- **Server Push**: Receive resources proactively
- **Stream Prioritization**: Better resource loading

Limitations
~~~~~~~~~~~

- Must use ``multiplexed`` connection strategy
- TLS is required (HTTPS only)
- Some servers may not support HTTP/2
- Connection reuse behaves differently

Example
~~~~~~~

.. code-block:: yaml

   metadata:
     name: "HTTP/2 Test"
   
   config:
     host: http2.example.com
     port: 443
     tls:
       enabled: true
     http2: true
   
   entrypoint:
     state: race_http2
     input: {}
   
   states:
     race_http2:
       race:
         threads: 50
         connection_strategy: multiplexed
       
       request: |
         GET /api/data HTTP/2
         Host: {{ config.host }}

Connection Reuse
----------------

Control TCP connection reuse behavior for different scenarios.

Configuration
~~~~~~~~~~~~~

**Global Setting**:

.. code-block:: yaml

   config:
     connection_reuse: true  # Default: true

**Per-State Setting**:

.. code-block:: yaml

   states:
     login:
       connection_reuse: false  # Force new connection
       request: |
         POST /api/login HTTP/1.1

Strategies
~~~~~~~~~~

**Preconnect Strategy** (default):

- Creates connections before race
- Reuses connections across requests
- Best for consistent timing

**Lazy Strategy**:

- Creates connections on-demand
- No reuse by default
- Good for testing connection establishment

**Pooled Strategy**:

- Maintains connection pool
- Reuses from pool
- Good for sequential states

**Multiplexed Strategy**:

- Single connection, multiple streams
- Requires HTTP/2
- Best for high concurrency

When to Disable Reuse
~~~~~~~~~~~~~~~~~~~~~~

Disable connection reuse when:

1. Testing connection establishment timing
2. Server enforces connection limits
3. Testing connection-level vulnerabilities
4. Debugging connection issues

Example
~~~~~~~

.. code-block:: yaml

   states:
     test_new_connection:
       connection_reuse: false
       race:
         threads: 10
         connection_strategy: lazy
       
       request: |
         GET /api/test HTTP/1.1

Redirect Handling
-----------------

Configure HTTP redirect following behavior.

Configuration
~~~~~~~~~~~~~

**Follow All Redirects**:

.. code-block:: yaml

   config:
     follow_redirects: true  # Default

**Disable Redirects**:

.. code-block:: yaml

   config:
     follow_redirects: false

**Max Redirects**:

.. code-block:: yaml

   config:
     max_redirects: 5  # Default: 20

Use Cases
~~~~~~~~~

1. **Test Redirect Chains**: Follow multiple redirects
2. **Capture Location Headers**: Don't follow redirects
3. **Prevent Redirect Loops**: Limit max redirects
4. **Race Redirect Logic**: Test redirect race conditions

Example
~~~~~~~

.. code-block:: yaml

   config:
     host: api.example.com
     follow_redirects: true
     max_redirects: 3
   
   states:
     test_redirect:
       request: |
         GET /redirect-endpoint HTTP/1.1
       
       extract:
         final_url:
           type: header
           pattern: "Location"

When Blocks
-----------

Multi-condition transitions with complex boolean expressions.

Basic Syntax
~~~~~~~~~~~~

.. code-block:: yaml

   states:
     test:
       request: |
         GET /api/test HTTP/1.1
       
       next:
         - when:
             - status == 200
             - body contains "success"
           goto: success
         
         - when:
             - status == 429
           goto: rate_limited

Supported Conditions
~~~~~~~~~~~~~~~~~~~~

**Status Code Matching**:

.. code-block:: yaml

   when:
     - status == 200
     - status in [200, 201, 204]
     - status >= 200 and status < 300
     - status != 404

**Body Matching**:

.. code-block:: yaml

   when:
     - body contains "error"
     - body regex "user_id\":\s*(\d+)"
     - body equals '{"status":"ok"}'
     - body not contains "failed"

**Header Checks**:

.. code-block:: yaml

   when:
     - header "Content-Type" contains "json"
     - header "X-Rate-Limit" exists
     - header "X-Custom" equals "value"
     - header "Content-Length" > 1000

**Response Time**:

.. code-block:: yaml

   when:
     - response_time < 100  # milliseconds
     - response_time >= 1000

**Jinja2 Expressions**:

.. code-block:: yaml

   when:
     - "{{ extracted_value | int > 100 }}"
     - "{{ user_role == 'admin' }}"

Boolean Operators
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   when:
     - status == 200 and body contains "success"
     - status == 401 or status == 403
     - not (body contains "error")
     - (status >= 200 and status < 300) or status == 304

Example
~~~~~~~

.. code-block:: yaml

   states:
     login:
       request: |
         POST /api/login HTTP/1.1
         Content-Type: application/json
         
         {"user": "{{ username }}", "pass": "{{ password }}"}
       
       extract:
         token:
           type: jpath
           pattern: "$.token"
       
       next:
         - when:
             - status == 200
             - body contains "token"
             - header "Set-Cookie" exists
           goto: authenticated
         
         - when:
             - status == 401
             - body contains "invalid"
           goto: failed
         
         - when:
             - status == 429
           goto: rate_limited
         
         - when:
             - response_time > 5000
           goto: timeout

Timeout Configuration
---------------------

Configure request timeouts globally and per-state.

Global Timeout
~~~~~~~~~~~~~~

.. code-block:: yaml

   config:
     timeout: 30  # 30 seconds for all requests

Per-State Timeout
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     slow_operation:
       timeout: 60  # 60 seconds for this state
       request: |
         POST /api/slow HTTP/1.1

Race Timeout
~~~~~~~~~~~~

.. code-block:: yaml

   states:
     race_attack:
       race:
         threads: 100
         timeout: 10  # Timeout for race coordination
       
       timeout: 30  # Timeout for each request

Connection Timeout
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   config:
     connect_timeout: 5  # Connection establishment timeout
     timeout: 30  # Read timeout

Best Practices
~~~~~~~~~~~~~~

1. **Set Reasonable Defaults**: 30s for most APIs
2. **Increase for Slow Operations**: File uploads, reports
3. **Decrease for Fast APIs**: Microservices, caches
4. **Monitor Timeouts**: Track timeout occurrences

Example
~~~~~~~

.. code-block:: yaml

   config:
     timeout: 30
     connect_timeout: 5
   
   states:
     quick_check:
       timeout: 5
       request: |
         GET /health HTTP/1.1
     
     slow_report:
       timeout: 120
       request: |
         POST /api/generate-report HTTP/1.1

Schema Validation
-----------------

TRECO includes JSON Schema validation for configuration files.

IDE Integration
~~~~~~~~~~~~~~~

**VSCode**:

Add to ``.vscode/settings.json``:

.. code-block:: json

   {
     "yaml.schemas": {
       "schema/treco-config.schema.json": "*.yaml"
     }
   }

**PyCharm/IntelliJ**:

1. Settings → Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings
2. Add new mapping:
   - File: ``schema/treco-config.schema.json``
   - Pattern: ``*.yaml``

Pre-commit Hook
~~~~~~~~~~~~~~~

Add to ``.pre-commit-config.yaml``:

.. code-block:: yaml

   repos:
     - repo: local
       hooks:
         - id: validate-treco-config
           name: Validate TRECO Config
           entry: treco --validate-only
           language: system
           files: \.yaml$

Command Line
~~~~~~~~~~~~

.. code-block:: bash

   # Validate without executing
   treco --validate-only attack.yaml

Benefits
~~~~~~~~

1. **Early Error Detection**: Catch errors before execution
2. **Autocomplete**: IDE suggestions for fields
3. **Documentation**: Inline schema descriptions
4. **Type Checking**: Validate field types

See Also
--------

- :doc:`configuration` - Complete configuration reference
- :doc:`connection-strategies` - Connection strategy details
- :doc:`templates` - Template engine reference
- :doc:`troubleshooting` - Common issues and solutions
