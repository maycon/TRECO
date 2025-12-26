Best Practices
==============

This guide provides recommendations for using TRECO effectively, securely, and professionally.

----

Performance Optimization
------------------------

Achieving Optimal Race Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For best race condition timing (< 1μs):

**1. Use Python 3.14t (Free-Threaded)**

.. code-block:: bash

   # Install Python 3.14t
   uv python install 3.14t
   
   # Create environment with 3.14t
   uv sync
   
   # Verify
   python --version  # Should show 3.14.0t or later

**2. Always Use Preconnect + Barrier**

.. code-block:: yaml

   race:
     sync_mechanism: barrier           # Best timing precision
     connection_strategy: preconnect   # Eliminates connection overhead
     threads: 20                       # Optimal range: 10-30

**3. Test on Low-Latency Network**

.. code-block:: bash

   # Check network latency
   ping api.example.com
   
   # Optimal: < 10ms
   # Good: 10-50ms
   # Acceptable: 50-100ms
   # Poor: > 100ms

**4. Avoid Proxies for Race Testing**

.. code-block:: yaml

   # For race conditions, use direct connection
   target:
     host: "api.example.com"
     # proxy:  # Comment out proxy for race testing

**Performance Targets:**

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Configuration
     - Race Window
     - Quality
   * - Python 3.14t + Preconnect + Barrier + Local
     - < 1μs
     - 🟢 Excellent
   * - Python 3.10+ + Preconnect + Barrier + Local
     - 1-10μs
     - 🟢 Very Good
   * - Preconnect + Barrier + LAN
     - 10-50ms
     - 🟡 Good
   * - Lazy or Semaphore
     - 50-200ms
     - 🔴 Poor
   * - With Proxy
     - 100-500ms+
     - 🔴 Not Suitable

Thread Count Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~

**General Guidelines:**

.. code-block:: yaml

   # Start low, increase gradually
   race:
     threads: 10  # Initial test
     # If race not triggered, increase to 20, then 30, etc.

**By Attack Type:**

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Attack Type
     - Threads
     - Rationale
   * - Double-spending
     - 2-10
     - Few attempts usually sufficient
   * - Inventory manipulation
     - 20-50
     - Depends on stock quantity
   * - Rate limiting bypass
     - 50-200
     - Test concurrent quota exhaustion
   * - Fund redemption
     - 10-30
     - Balance between coverage and timing

**Signs of Too Many Threads:**

* Race window increases
* Connection timeouts
* High failure rate
* System instability

**Optimal Range:**

Most scenarios: **10-30 threads** provides best balance of coverage and timing precision.

Connection Management
~~~~~~~~~~~~~~~~~~~~~

**Best Practices:**

.. code-block:: yaml

   # 1. Don't reuse connections for race testing
   target:
     reuse_connection: false  # Default and recommended
   
   race:
     reuse_connections: false  # Don't reuse in race
   
   # 2. Clean connections are more realistic
   connection_strategy: preconnect  # Establishes fresh connections

**When to Reuse Connections:**

* Testing keep-alive behavior
* Sequential request testing
* Non-race scenarios

**When NOT to Reuse:**

* Race condition testing (default)
* Testing connection-level vulnerabilities
* Measuring true cold-start performance

----

Security Best Practices
-----------------------

Authorization and Scope
~~~~~~~~~~~~~~~~~~~~~~~

**Always Obtain Written Authorization:**

.. code-block:: yaml

   metadata:
     name: "Authorized Security Test"
     author: "Security Team"
     authorization: "Approved by security@example.com - Ticket #12345"
     scope: "staging.example.com only"
     date: "2025-01-15"

**Define Clear Boundaries:**

1. **Scope Document:**
   
   * Which systems/endpoints
   * Which test types allowed
   * Time windows for testing
   * Data handling requirements

2. **Point of Contact:**
   
   * Primary contact name/email
   * Escalation contact
   * Incident reporting procedure

3. **Legal Compliance:**
   
   * Terms of service review
   * Privacy laws (GDPR, CCPA, etc.)
   * Computer fraud laws (CFAA, etc.)
   * Industry regulations (PCI-DSS, HIPAA, etc.)

Credential Management
~~~~~~~~~~~~~~~~~~~~~

**Never Hardcode Credentials:**

.. code-block:: yaml

   # ❌ BAD: Hardcoded credentials
   input:
     username: "admin"
     password: "MyPassword123"
     api_key: "sk-1234567890abcdef"
   
   # ✅ GOOD: Environment variables
   input:
     username: "{{ env('TEST_USER') }}"
     password: "{{ env('TEST_PASS') }}"
     api_key: "{{ env('API_KEY') }}"

**Environment Variable Management:**

.. code-block:: bash

   # Use .env file (DO NOT commit to git)
   cat > .env << EOF
   TEST_USER=testuser
   TEST_PASS=SecurePassword123!
   API_KEY=sk-your-api-key
   EOF
   
   # Add to .gitignore
   echo ".env" >> .gitignore
   
   # Load environment
   set -a
   source .env
   set +a
   
   # Run tests
   treco attack.yaml

**Credential Storage:**

1. **Development:** Environment variables, .env files
2. **CI/CD:** Secret management systems (GitHub Secrets, HashiCorp Vault)
3. **Production Testing:** Secure credential stores only

SSL/TLS Configuration
~~~~~~~~~~~~~~~~~~~~~

**Production Systems:**

.. code-block:: yaml

   # Always verify certificates in production
   target:
     tls:
       enabled: true
       verify_cert: true  # REQUIRED for production

**Development/Staging:**

.. code-block:: yaml

   # Only disable for internal testing with explicit authorization
   target:
     tls:
       enabled: true
       verify_cert: false  # Document why this is acceptable

.. warning::
   Disabling certificate verification should only be done:
   
   * In isolated test environments
   * With explicit authorization
   * Documented in configuration
   * Never in production testing

Data Handling
~~~~~~~~~~~~~

**Sensitive Data:**

1. **Never log sensitive data:**

   .. code-block:: yaml
   
      # ❌ BAD
      logger:
        on_state_leave: |
          Password: {{ password }}
          Credit card: {{ credit_card }}
      
      # ✅ GOOD
      logger:
        on_state_leave: |
          Authentication: {{ 'Success' if token else 'Failed' }}
          Payment: {{ 'Processed' if payment_id else 'Failed' }}

2. **Sanitize outputs:**

   .. code-block:: yaml
   
      logger:
        on_state_leave: |
          Token: {{ token[:10] }}...  # Only show first 10 chars
          Email: {{ email | replace('@', '[at]') }}  # Obfuscate

3. **Clean up test data:**

   .. code-block:: yaml
   
      states:
        cleanup:
          description: "Remove test data"
          request: |
            DELETE /api/test-accounts/{{ test_account_id }} HTTP/1.1
            Authorization: Bearer {{ admin_token }}

Responsible Testing
~~~~~~~~~~~~~~~~~~~

**Testing Checklist:**

.. code-block:: text

   Before Testing:
   ☐ Written authorization obtained
   ☐ Scope clearly defined
   ☐ Test environment identified
   ☐ Backup/rollback plan ready
   ☐ Incident response contact known
   
   During Testing:
   ☐ Stay within authorized scope
   ☐ Monitor system impact
   ☐ Document all findings
   ☐ Stop if unexpected issues occur
   ☐ Communicate with stakeholders
   
   After Testing:
   ☐ Clean up test data
   ☐ Remove test accounts
   ☐ Document vulnerabilities found
   ☐ Report responsibly
   ☐ Verify fixes (if authorized)

**Red Flags - Stop Testing If:**

* System becomes unstable
* Production data appears accessible
* Unexpected scope discovered
* Legal concerns arise
* Authorization unclear

----

Configuration Best Practices
-----------------------------

File Organization
~~~~~~~~~~~~~~~~~

**Organize by Environment:**

.. code-block:: text

   configs/
   ├── dev/
   │   ├── payment-race.yaml
   │   ├── inventory-race.yaml
   │   └── auth-race.yaml
   ├── staging/
   │   ├── payment-race.yaml
   │   └── inventory-race.yaml
   └── production/  # Only with explicit authorization
       └── (authorized tests only)

**Use Templates:**

.. code-block:: yaml

   # base-template.yaml
   metadata:
     version: "1.0"
     author: "Security Team"
   
   target:
     timeout: 30
     tls:
       enabled: true
       verify_cert: true
     
     race:
       sync_mechanism: barrier
       connection_strategy: preconnect

**Environment-Specific Overrides:**

.. code-block:: yaml

   # dev-config.yaml
   target:
     host: "dev-api.example.com"
     tls:
       verify_cert: false  # Self-signed certs in dev
   
   # prod-config.yaml
   target:
     host: "api.example.com"
     tls:
       verify_cert: true  # Always verify in prod

Naming Conventions
~~~~~~~~~~~~~~~~~~

**Descriptive Names:**

.. code-block:: yaml

   # ✅ GOOD: Clear, descriptive names
   metadata:
     name: "Payment Processing Double-Spending Test"
   
   states:
     authenticate_user:
       description: "Obtain JWT token for API access"
     
     race_concurrent_payments:
       description: "Attempt multiple payments with same token"
     
     verify_account_balance:
       description: "Check if balance changed unexpectedly"
   
   # ❌ BAD: Vague names
   metadata:
     name: "Test 1"
   
   states:
     step1:
     step2:
     step3:

**File Naming:**

.. code-block:: text

   ✅ GOOD:
   payment-double-spending-race.yaml
   inventory-stock-bypass.yaml
   coupon-redemption-race.yaml
   
   ❌ BAD:
   test1.yaml
   attack.yaml
   config.yaml

Documentation in Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Comprehensive Metadata:**

.. code-block:: yaml

   metadata:
     name: "E-commerce Inventory Race Condition"
     version: "2.1"
     author: "Security Team <security@example.com>"
     vulnerability: "CWE-362 - Race Condition"
     description: |
       Tests for race conditions in inventory management system
       that could allow purchasing more items than available stock.
       
       Impact: Medium
       - Overselling of limited items
       - Revenue loss
       - Customer dissatisfaction
     
     references:
       - "https://cwe.mitre.org/data/definitions/362.html"
       - "Internal ticket: SEC-12345"
     
     authorization:
       approved_by: "security@example.com"
       ticket: "SEC-12345"
       scope: "staging.example.com"
       date: "2025-01-15"
     
     changelog:
       - "2.1 - 2025-01-20: Added verification step"
       - "2.0 - 2025-01-15: Optimized thread count"
       - "1.0 - 2025-01-10: Initial version"

**State Documentation:**

.. code-block:: yaml

   states:
     authenticate:
       description: |
         Authenticate using OAuth 2.0 client credentials flow.
         Obtains JWT token valid for 1 hour.
         
         Prerequisites:
         - CLIENT_ID environment variable set
         - CLIENT_SECRET environment variable set
         
         Outputs:
         - access_token: JWT bearer token
         - expires_in: Token expiration time (seconds)
       
       request: |
         POST /oauth/token HTTP/1.1
         Content-Type: application/x-www-form-urlencoded
         
         grant_type=client_credentials
         &client_id={{ env('CLIENT_ID') }}
         &client_secret={{ env('CLIENT_SECRET') }}

Version Control
~~~~~~~~~~~~~~~

**What to Commit:**

.. code-block:: text

   ✅ Commit:
   - Configuration files (sanitized)
   - Documentation
   - Templates
   - Examples
   - Scripts (sanitized)
   
   ❌ DO NOT Commit:
   - Credentials (.env files)
   - API keys
   - Tokens
   - Personal data
   - Real target URLs (use placeholders)

**.gitignore:**

.. code-block:: text

   # Environment and credentials
   .env
   .env.*
   *.key
   *.pem
   credentials/
   secrets/
   
   # Outputs and logs
   logs/
   *.log
   results/
   reports/
   
   # Python
   __pycache__/
   *.pyc
   .venv/
   venv/

----

Testing Best Practices
----------------------

Progressive Testing Approach
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Baseline Test (No Race):**

.. code-block:: yaml

   # First: Test with single request
   states:
     baseline_test:
       description: "Test single request behavior"
       request: |
         POST /api/redeem HTTP/1.1
         {"code": "TEST100"}
       
       # No race configuration
       
       logger:
         on_state_leave: |
           Single request result: {{ status }}
           Balance: {{ balance }}

**2. Small Race Test:**

.. code-block:: yaml

   # Second: Test with minimal threads
   states:
     small_race_test:
       request: |
         POST /api/redeem HTTP/1.1
         {"code": "TEST100"}
       
       race:
         threads: 2  # Start with just 2
         sync_mechanism: barrier
         connection_strategy: preconnect

**3. Scale Up Gradually:**

.. code-block:: yaml

   # Third: Increase threads if needed
   race:
     threads: 5   # Then 5
     # Then 10, 20, 30, etc.

**4. Optimize Configuration:**

.. code-block:: yaml

   # Finally: Optimize for best results
   race:
     threads: 20                       # Optimal count found
     sync_mechanism: barrier
     connection_strategy: preconnect
     thread_propagation: single

Test Multiple Scenarios
~~~~~~~~~~~~~~~~~~~~~~~~

**Variation Testing:**

.. code-block:: yaml

   # Test 1: Different thread counts
   # test-threads-10.yaml
   race:
     threads: 10
   
   # test-threads-20.yaml
   race:
     threads: 20
   
   # test-threads-50.yaml
   race:
     threads: 50

.. code-block:: bash

   # Run all variations
   for config in test-threads-*.yaml; do
     echo "Testing $config"
     treco "$config"
   done

**Different Attack Vectors:**

1. **Same endpoint, different data**
2. **Same data, different timing**
3. **Different user accounts**
4. **Different authentication methods**

Reproducibility
~~~~~~~~~~~~~~~

**Document Test Conditions:**

.. code-block:: yaml

   metadata:
     test_conditions:
       date: "2025-01-15"
       time: "14:30 UTC"
       environment: "staging"
       network: "office-lan"
       python_version: "3.14.0t"
       treco_version: "1.2.0"
       
       system:
         os: "Ubuntu 22.04"
         cpu: "Intel i7-12700K"
         ram: "32GB"
       
       results:
         race_window: "0.8μs"
         success_rate: "90%"
         vulnerabile: true

**Repeatable Tests:**

.. code-block:: bash

   # Script for repeated testing
   #!/bin/bash
   
   echo "Running reproducibility test"
   echo "Date: $(date)"
   echo "Python: $(python --version)"
   echo "TRECO: $(treco --version)"
   echo ""
   
   for i in {1..10}; do
     echo "=== Run $i/10 ==="
     treco attack.yaml
     sleep 2
   done

**Statistical Analysis:**

.. code-block:: python

   # Analyze results
   import statistics
   
   race_windows = [0.8, 0.9, 1.1, 0.7, 1.0, 0.9, 0.8, 1.2, 0.9, 1.0]
   
   print(f"Mean: {statistics.mean(race_windows):.2f}μs")
   print(f"Median: {statistics.median(race_windows):.2f}μs")
   print(f"Std Dev: {statistics.stdev(race_windows):.2f}μs")
   print(f"Min: {min(race_windows):.2f}μs")
   print(f"Max: {max(race_windows):.2f}μs")

----

Logging and Monitoring
----------------------

Effective Logging
~~~~~~~~~~~~~~~~~

**Progressive Detail Levels:**

.. code-block:: yaml

   # Level 1: Minimal (production)
   logger:
     on_state_leave: |
       Status: {{ status }}
   
   # Level 2: Standard (most testing)
   logger:
     on_state_enter: |
       Starting {{ state.name }}
     
     on_state_leave: |
       Completed: {{ status }}
       Duration: {{ duration }}ms
   
   # Level 3: Verbose (debugging)
   logger:
     on_state_enter: |
       === STATE: {{ state.name }} ===
       Context: {{ context.keys() | list }}
       Timestamp: {{ timestamp }}
     
     on_thread_enter: |
       [T{{ thread.id }}] Starting...
     
     on_thread_leave: |
       [T{{ thread.id }}] Status: {{ status }}, Time: {{ response_time }}ms
     
     on_state_leave: |
       Summary:
       - Status: {{ status }}
       - Duration: {{ duration }}ms
       - Race window: {{ race_window }}ms
       - Extracted: {{ extracted_vars }}

**Structured Logging:**

.. code-block:: yaml

   logger:
     on_state_leave: |
       {
         "state": "{{ state.name }}",
         "status": {{ status }},
         "duration_ms": {{ duration }},
         "timestamp": "{{ timestamp }}",
         "vulnerable": {{ 'true' if vulnerable else 'false' }}
       }

Monitoring Race Quality
~~~~~~~~~~~~~~~~~~~~~~~

**Race Window Monitoring:**

.. code-block:: yaml

   logger:
     on_state_leave: |
       Race Window Quality Assessment:
       
       Race window: {{ race_window }}μs
       
       {% if race_window < 1 %}
       ✓ EXCELLENT: Sub-microsecond precision
       ✓ Optimal for triggering race conditions
       {% elif race_window < 10 %}
       ✓ VERY GOOD: Sufficient for most races
       ✓ Recommended configuration
       {% elif race_window < 100 %}
       ⚠ GOOD: Acceptable but not optimal
       ⚠ Consider optimization
       {% else %}
       ❌ POOR: Too slow for reliable races
       ❌ Review configuration
       {% endif %}
       
       Recommendations:
       {% if race_window >= 100 %}
       - Use preconnect strategy
       - Use barrier sync mechanism
       - Reduce network latency
       - Avoid proxies
       {% endif %}

**Success Rate Tracking:**

.. code-block:: yaml

   logger:
     on_state_leave: |
       Attack Results:
       - Total threads: {{ total_threads }}
       - Successful: {{ successful_threads }}
       - Failed: {{ failed_threads }}
       - Success rate: {{ (successful_threads / total_threads * 100) | round(1) }}%
       
       {% if successful_threads > 1 %}
       ⚠️  VULNERABLE: {{ successful_threads }} requests succeeded
       {% else %}
       ✓ No race condition detected
       {% endif %}

----

Reporting and Documentation
----------------------------

Vulnerability Reports
~~~~~~~~~~~~~~~~~~~~~

**Report Template:**

.. code-block:: text

   ═══════════════════════════════════════════════════════
   SECURITY TEST REPORT
   ═══════════════════════════════════════════════════════
   
   Test Date: 2025-01-15
   Tester: Security Team
   Authorization: Ticket #SEC-12345
   
   VULNERABILITY DETAILS
   ───────────────────────────────────────────────────────
   Type: Race Condition (CWE-362)
   Severity: HIGH
   System: Payment Processing API
   Endpoint: POST /api/payments/process
   
   DESCRIPTION
   ───────────────────────────────────────────────────────
   The payment processing endpoint is vulnerable to race
   conditions, allowing the same payment token to be
   processed multiple times concurrently.
   
   IMPACT
   ───────────────────────────────────────────────────────
   - Financial loss through double-charging
   - Accounting discrepancies
   - Fraud potential
   - Customer complaints
   
   REPRODUCTION STEPS
   ───────────────────────────────────────────────────────
   1. Obtain valid payment token
   2. Send 20 concurrent requests with same token
   3. Observe multiple successful transactions
   
   TECHNICAL DETAILS
   ───────────────────────────────────────────────────────
   Race Window: 0.9μs
   Success Rate: 85% (17/20 requests succeeded)
   Configuration: Barrier sync + Preconnect strategy
   
   EVIDENCE
   ───────────────────────────────────────────────────────
   [Attach logs, screenshots, YAML config]
   
   RECOMMENDATION
   ───────────────────────────────────────────────────────
   Implement database-level transaction locking or
   idempotency key mechanism to prevent duplicate
   processing.
   
   REFERENCES
   ───────────────────────────────────────────────────────
   - https://cwe.mitre.org/data/definitions/362.html
   - OWASP Testing Guide: Race Conditions
   
   ═══════════════════════════════════════════════════════

Test Documentation
~~~~~~~~~~~~~~~~~~

**Document Everything:**

1. **Test Plan:**
   
   * Objectives
   * Scope
   * Methodology
   * Timeline

2. **Configuration Files:**
   
   * All YAML configs used
   * Version information
   * Environment details

3. **Results:**
   
   * Test outputs
   * Screenshots
   * Logs
   * Metrics

4. **Findings:**
   
   * Vulnerabilities discovered
   * False positives
   * Unexpected behaviors

5. **Recommendations:**
   
   * Remediation steps
   * Priority levels
   * Validation methods

----

Code Quality
------------

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~

**Pre-flight Checks:**

.. code-block:: bash

   # Validate YAML syntax
   yamllint attack.yaml
   
   # Test template rendering
   # (dry-run mode if available)
   
   # Verify connectivity
   ping api.example.com
   
   # Check credentials
   echo $API_KEY

**Configuration Linting:**

.. code-block:: yaml

   # Use consistent formatting
   # 2-space indentation
   # Alphabetical ordering when logical
   
   target:
     host: "api.example.com"
     port: 443
     threads: 20
     timeout: 30
     tls:
       enabled: true
       verify_cert: true

Reusable Components
~~~~~~~~~~~~~~~~~~~

**Extract Common Patterns:**

.. code-block:: yaml

   # common/auth.yaml
   authenticate: &authenticate
     description: "OAuth 2.0 authentication"
     request: |
       POST /oauth/token HTTP/1.1
       Content-Type: application/x-www-form-urlencoded
       
       grant_type=client_credentials
       &client_id={{ env('CLIENT_ID') }}
       &client_secret={{ env('CLIENT_SECRET') }}
     
     extract:
       token:
         type: jpath
         pattern: "$.access_token"
   
   # Use in other configs
   states:
     login:
       <<: *authenticate

----

Continuous Improvement
----------------------

Regular Reviews
~~~~~~~~~~~~~~~

**Review Checklist:**

.. code-block:: text

   Monthly Review:
   ☐ Update configurations for new endpoints
   ☐ Review authorization documentation
   ☐ Update credentials
   ☐ Test on latest TRECO version
   ☐ Review and update documentation
   
   Quarterly Review:
   ☐ Audit test coverage
   ☐ Review security findings
   ☐ Update threat models
   ☐ Train team on new techniques
   ☐ Review and optimize performance
   
   Annual Review:
   ☐ Complete authorization renewal
   ☐ Comprehensive testing review
   ☐ Update methodologies
   ☐ Review legal compliance
   ☐ Update tooling and frameworks

Learning from Results
~~~~~~~~~~~~~~~~~~~~~

**Track Metrics:**

* Vulnerabilities found per test
* False positive rate
* Time to test
* Coverage achieved
* Remediation success rate

**Iterate and Improve:**

1. Analyze what worked
2. Identify gaps
3. Update methodologies
4. Share knowledge
5. Train team members

----

See Also
--------

* :doc:`configuration` - Complete configuration reference
* :doc:`synchronization` - Synchronization mechanisms
* :doc:`connection-strategies` - Connection strategies
* :doc:`troubleshooting` - Common issues and solutions
* :doc:`examples` - Working examples