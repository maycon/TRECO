When Blocks
===========

Multi-condition when blocks enable complex state transitions with rich boolean expressions for advanced routing logic.

Overview
--------

When blocks replace simple status-based transitions with complex decision logic supporting:

- HTTP status code matching (exact, range, multiple)
- Response body content matching
- Header checks and comparisons
- Extracted variable conditions using Jinja2
- Response time analysis
- AND/OR logic for complex routing

Basic Syntax
------------

.. code-block:: yaml

   states:
     check_auth:
       request: |
         GET /api/user/profile HTTP/1.1
       
       extract:
         role:
           type: jpath
           pattern: "$.user.role"
       
       next:
         - when:
             - status: 200
             - condition: "{{ role == 'admin' }}"
           goto: admin_panel
         
         - otherwise:
           goto: normal_flow

Condition Types
---------------

Status Code Matching
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   when:
     - status: 200                    # Exact match
     - status_in: [200, 201, 202]     # Multiple statuses
     - status_range: [200, 299]       # Range (inclusive)

**Examples:**

.. code-block:: yaml

   # Success codes
   - when:
       - status_range: [200, 299]
     goto: success
   
   # Client errors
   - when:
       - status_range: [400, 499]
     goto: client_error
   
   # Specific codes
   - when:
       - status_in: [401, 403]
     goto: unauthorized

Jinja2 Expressions
~~~~~~~~~~~~~~~~~~

Evaluate complex boolean expressions using extracted variables:

.. code-block:: yaml

   when:
     - condition: "{{ role == 'admin' }}"
     - condition: "{{ balance > 1000 }}"
     - condition: "{{ age >= 18 and age <= 65 }}"
     - condition: "{{ 'premium' in user.features }}"

**Supported operators:**

- Comparison: ``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``
- Membership: ``in``, ``not in``
- Boolean: ``and``, ``or``, ``not``
- String operations via Jinja2 filters

**Examples:**

.. code-block:: yaml

   # Numeric comparisons
   - condition: "{{ balance | int > 1000 }}"
   
   # String operations
   - condition: "{{ username | lower == 'admin' }}"
   
   # List operations
   - condition: "{{ user_id in [1, 2, 3, 4, 5] }}"
   
   # Complex logic
   - condition: "{{ (balance > 100 and role == 'premium') or is_vip }}"

Body Content Matching
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   when:
     - body_contains: "success"           # Substring match
     - body_not_contains: "error"         # Negative match
     - body_matches: "^HTTP/1\\.1 200"    # Regex match
     - body_equals: '{"status": "ok"}'    # Exact match

**Examples:**

.. code-block:: yaml

   # Check for success message
   - when:
       - status: 200
       - body_contains: "operation completed"
     goto: success
   
   # Detect errors in response
   - when:
       - body_contains: "error"
       - body_not_contains: "no errors"
     goto: error_handler
   
   # Regex pattern matching
   - when:
       - body_matches: "user_id\":\\s*(\\d+)"
     goto: user_found

Header Checks
~~~~~~~~~~~~~

.. code-block:: yaml

   when:
     # Simple existence check
     - header_exists: "X-Auth-Token"
     - header_not_exists: "X-Debug"
     
     # Value matching
     - header_equals:
         name: "Content-Type"
         value: "application/json"
     
     # Substring matching
     - header_contains:
         name: "Content-Type"
         value: "json"
     
     # Numeric comparison
     - header_gt:
         name: "Content-Length"
         value: 1000

**Available header conditions:**

- ``header_exists`` - Check if header is present
- ``header_not_exists`` - Check if header is absent
- ``header_equals`` - Exact value match
- ``header_contains`` - Substring match
- ``header_gt`` - Greater than (numeric)
- ``header_lt`` - Less than (numeric)
- ``header_gte`` - Greater than or equal (numeric)
- ``header_lte`` - Less than or equal (numeric)

**Examples:**

.. code-block:: yaml

   # Rate limiting detection
   - when:
       - header_exists: "X-RateLimit-Remaining"
       - header_lt:
           name: "X-RateLimit-Remaining"
           value: 10
     goto: slow_down
   
   # Content type validation
   - when:
       - header_equals:
           name: "Content-Type"
           value: "application/json"
     goto: parse_json
   
   # Check response size
   - when:
       - header_gt:
           name: "Content-Length"
           value: 10000
     goto: large_response

Response Time Analysis
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   when:
     - response_time_lt: 100    # Less than 100ms
     - response_time_gt: 1000   # Greater than 1000ms
     - response_time_between:
         min: 100
         max: 500

**Examples:**

.. code-block:: yaml

   # Fast response detection
   - when:
       - response_time_lt: 50
     goto: cache_hit
   
   # Slow response detection
   - when:
       - response_time_gt: 2000
     goto: timeout_handling
   
   # Acceptable range
   - when:
       - response_time_between:
           min: 100
           max: 500
     goto: normal_flow

Combining Conditions
--------------------

Multiple conditions in a when block are implicitly AND'ed:

.. code-block:: yaml

   # All conditions must be true
   - when:
       - status: 200
       - body_contains: "success"
       - header_exists: "X-Auth-Token"
       - condition: "{{ balance > 100 }}"
     goto: all_conditions_met

For OR logic, use separate when blocks:

.. code-block:: yaml

   # If status is 200 OR 201
   - when:
       - status: 200
     goto: success
   
   - when:
       - status: 201
     goto: success

Or use Jinja2 conditions:

.. code-block:: yaml

   - when:
       - condition: "{{ status == 200 or status == 201 }}"
     goto: success

Complex Examples
----------------

Role-Based Routing
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     check_user:
       request: |
         GET /api/user/profile HTTP/1.1
         Authorization: Bearer {{ token }}
       
       extract:
         role:
           type: jpath
           pattern: "$.role"
         permissions:
           type: jpath
           pattern: "$.permissions"
       
       next:
         # Admin with full access
         - when:
             - status: 200
             - condition: "{{ role == 'admin' }}"
             - condition: "{{ 'full_access' in permissions }}"
           goto: admin_panel
         
         # Moderator
         - when:
             - status: 200
             - condition: "{{ role == 'moderator' }}"
           goto: moderator_panel
         
         # Regular user
         - when:
             - status: 200
           goto: user_dashboard
         
         # Unauthorized
         - when:
             - status_in: [401, 403]
           goto: login

Error Detection
~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     api_call:
       request: |
         POST /api/process HTTP/1.1
       
       next:
         # Success
         - when:
             - status_range: [200, 299]
             - body_contains: "success"
             - body_not_contains: "error"
           goto: success
         
         # Rate limited
         - when:
             - status: 429
             - header_exists: "Retry-After"
           goto: rate_limited
         
         # Server error
         - when:
             - status_range: [500, 599]
           goto: server_error
         
         # Validation error
         - when:
             - status: 400
             - body_contains: "validation"
           goto: validation_error
         
         # Unknown error
         - otherwise:
           goto: unknown_error

Race Condition Detection
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     race_attack:
       race:
         threads: 20
       
       request: |
         POST /api/redeem HTTP/1.1
       
       extract:
         remaining:
           type: jpath
           pattern: "$.vouchers_remaining"
       
       next:
         # Multiple successes = vulnerability
         - when:
             - status: 200
             - body_contains: "redeemed"
             - condition: "{{ successful_requests | int > 1 }}"
           goto: vulnerability_found
         
         # Single success = expected
         - when:
             - status: 200
             - condition: "{{ successful_requests | int == 1 }}"
           goto: no_vulnerability
         
         # All failed = race condition prevented
         - when:
             - condition: "{{ successful_requests | int == 0 }}"
           goto: protected

Performance-Based Routing
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     load_test:
       request: |
         GET /api/heavy-operation HTTP/1.1
       
       next:
         # Fast cache hit
         - when:
             - status: 200
             - response_time_lt: 100
             - header_exists: "X-Cache-Hit"
           goto: cache_hit
         
         # Slow but successful
         - when:
             - status: 200
             - response_time_gt: 1000
           goto: slow_response
         
         # Timeout
         - when:
             - response_time_gt: 5000
           goto: timeout
         
         # Normal response
         - when:
             - status: 200
             - response_time_between:
                 min: 100
                 max: 1000
           goto: normal_response

Best Practices
--------------

1. **Order Matters**
   
   When blocks are evaluated in order. Put more specific conditions first:

   .. code-block:: yaml

      # Good - specific first
      - when:
          - status: 200
          - condition: "{{ role == 'admin' }}"
        goto: admin
      
      - when:
          - status: 200
        goto: user
      
      # Bad - general first (admin never reached)
      - when:
          - status: 200
        goto: user
      
      - when:
          - status: 200
          - condition: "{{ role == 'admin' }}"
        goto: admin

2. **Always Provide Fallback**
   
   Use ``otherwise`` to handle unexpected cases:

   .. code-block:: yaml

      - when:
          - status: 200
        goto: success
      
      - otherwise:
        goto: error_handler

3. **Keep Conditions Simple**
   
   Break complex logic into multiple when blocks:

   .. code-block:: yaml

      # Good
      - when:
          - status: 200
        goto: check_role
      
      # In check_role state
      - when:
          - condition: "{{ role == 'admin' }}"
        goto: admin
      
      # Bad - too complex
      - when:
          - condition: "{{ (status == 200 and role == 'admin') or (status == 201 and role == 'moderator') }}"
        goto: privileged

4. **Test Extracted Variables**
   
   Ensure variables exist before using in conditions:

   .. code-block:: yaml

      extract:
        balance:
          type: jpath
          pattern: "$.balance"
          default: 0  # Provide default
      
      next:
        - when:
            - condition: "{{ balance | int > 100 }}"
          goto: high_balance

5. **Use Descriptive State Names**
   
   Make flow easy to understand:

   .. code-block:: yaml

      - when:
          - status: 429
        goto: handle_rate_limit  # Not goto: state_x

Common Patterns
---------------

Authentication Flow
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   next:
     - when:
         - status: 200
         - body_contains: "token"
       goto: authenticated
     
     - when:
         - status: 401
       goto: login_failed
     
     - when:
         - status: 429
       goto: rate_limited
     
     - otherwise:
       goto: error

API Error Handling
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   next:
     - when:
         - status_range: [200, 299]
       goto: success
     
     - when:
         - status_range: [400, 499]
       goto: client_error
     
     - when:
         - status_range: [500, 599]
       goto: server_error
     
     - otherwise:
       goto: unknown_error

See Also
--------

- :doc:`configuration` - Complete YAML configuration reference
- :doc:`templates` - Jinja2 template syntax and filters
- :doc:`extractors` - Data extraction from responses
- :doc:`examples` - Real-world examples
