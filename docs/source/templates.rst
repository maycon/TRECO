Template Engine
===============

TRECO uses a Jinja2-based template engine with custom filters for dynamic HTTP request generation.

Overview
--------

Templates allow you to create dynamic requests with variables, conditionals, loops, and custom filters. The syntax follows Jinja2 conventions.

Basic Syntax
------------

Variables
~~~~~~~~~

Use double curly braces to interpolate variables:

.. code-block:: yaml

   request: |
     GET /api/users/{{ user_id }} HTTP/1.1
     Host: {{ config.host }}
     Authorization: Bearer {{ login.token }}

Variable Sources
~~~~~~~~~~~~~~~~

Variables can come from multiple sources:

.. code-block:: yaml

   # Entrypoint input
   {{ username }}
   
   # Config section
   {{ config.host }}
   {{ config.port }}
   
   # Previous state extraction
   {{ login.token }}
   {{ get_balance.amount }}
   
   # Thread info (race states)
   {{ thread.id }}
   {{ thread.count }}
   
   # Environment variables
   {{ env('API_KEY') }}
   
   # CLI arguments
   {{ argv('user', 'default') }}

Built-in Filters
----------------

TRECO provides several custom filters for security testing scenarios.

TOTP (totp)
~~~~~~~~~~~

Generate Time-based One-Time Passwords for 2FA testing.

**Usage:**

.. code-block:: yaml

   # Function syntax (recommended)
   {{ totp(seed) }}
   {{ totp('JBSWY3DPEHPK3PXP') }}
   
   # Filter syntax
   {{ seed | totp }}

**Example:**

.. code-block:: yaml

   states:
     login_2fa:
       request: |
         POST /api/login HTTP/1.1
         Content-Type: application/json
         
         {
           "username": "{{ username }}",
           "password": "{{ password }}",
           "totp_code": "{{ totp(totp_seed) }}"
         }

MD5 (md5)
~~~~~~~~~

Compute MD5 hash of a value.

**Usage:**

.. code-block:: yaml

   # Function syntax
   {{ md5(password) }}
   
   # Filter syntax
   {{ password | md5 }}

**Example:**

.. code-block:: yaml

   states:
     login:
       request: |
         POST /api/login HTTP/1.1
         Content-Type: application/json
         
         {"username": "{{ username }}", "password_hash": "{{ password | md5 }}"}

SHA1 (sha1)
~~~~~~~~~~~

Compute SHA1 hash of a value.

**Usage:**

.. code-block:: yaml

   # Function syntax
   {{ sha1(data) }}
   
   # Filter syntax
   {{ data | sha1 }}

SHA256 (sha256)
~~~~~~~~~~~~~~~

Compute SHA256 hash of a value.

**Usage:**

.. code-block:: yaml

   # Function syntax
   {{ sha256(data) }}
   
   # Filter syntax
   {{ data | sha256 }}

**Example:**

.. code-block:: yaml

   states:
     api_call:
       request: |
         POST /api/secure HTTP/1.1
         X-Signature: {{ (timestamp + secret) | sha256 }}

Environment Variables (env)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Access environment variables with optional default values.

**Usage:**

.. code-block:: yaml

   # Without default (returns empty if not set)
   {{ env('API_KEY') }}
   
   # With default value
   {{ env('API_KEY', 'default_key') }}

**Example:**

.. code-block:: yaml

   entrypoint:
     state: login
     input:
       username: "{{ env('USERNAME', 'testuser') }}"
       password: "{{ env('PASSWORD') }}"
       api_key: "{{ env('API_KEY', 'demo_key') }}"

CLI Arguments (argv)
~~~~~~~~~~~~~~~~~~~~

Access command-line arguments passed to TRECO.

**Usage:**

.. code-block:: yaml

   # With default value
   {{ argv('user', 'guest') }}
   {{ argv('threads', '20') }}

**Example:**

.. code-block:: yaml

   # In YAML
   entrypoint:
     state: login
     input:
       username: "{{ argv('user', 'testuser') }}"
       thread_count: "{{ argv('threads', '10') }}"
   
   # Run with:
   # treco attack.yaml --user alice --threads 20

Average (average)
~~~~~~~~~~~~~~~~~

Compute the average of a list of values.

**Usage:**

.. code-block:: yaml

   # Simple list
   {{ values | average }}
   
   # List of objects with attribute
   {{ results | average(attribute='timing') }}

**Example:**

.. code-block:: yaml

   states:
     analyze:
       logger:
         on_state_leave: |
           Average response time: {{ timings | average }}ms

Control Structures
------------------

Conditionals
~~~~~~~~~~~~

Use ``{% if %}`` blocks for conditional content:

.. code-block:: yaml

   logger:
     on_state_leave: |
       {% if status == 200 %}
       ✓ Request succeeded
       {% elif status == 401 %}
       ✗ Authentication failed
       {% else %}
       ? Unexpected status: {{ status }}
       {% endif %}

**Comparison operators:**

* ``==`` - Equal
* ``!=`` - Not equal
* ``<``, ``>`` - Less than, greater than
* ``<=``, ``>=`` - Less/greater or equal
* ``in`` - Contains
* ``not in`` - Does not contain

Loops
~~~~~

Use ``{% for %}`` for iteration:

.. code-block:: yaml

   logger:
     on_state_leave: |
       Results:
       {% for result in results %}
       - Thread {{ result.thread_id }}: {{ result.status }}
       {% endfor %}

Filters
~~~~~~~

Use ``|`` to apply filters to values:

.. code-block:: yaml

   # String filters
   {{ username | upper }}
   {{ email | lower }}
   {{ name | title }}
   {{ text | length }}
   
   # List filters
   {{ items | first }}
   {{ items | last }}
   {{ items | join(', ') }}
   {{ items | sort }}
   
   # Number filters
   {{ price | round(2) }}
   {{ value | abs }}
   
   # Default filter
   {{ optional_value | default('N/A') }}

Request Templates
-----------------

HTTP Request Format
~~~~~~~~~~~~~~~~~~~

Requests use raw HTTP format with templates:

.. code-block:: yaml

   request: |
     POST /api/endpoint HTTP/1.1
     Host: {{ config.host }}
     Content-Type: application/json
     Authorization: Bearer {{ token }}
     X-Custom-Header: {{ custom_value }}
     
     {"key": "{{ value }}", "nested": {"field": "{{ other }}"}}

**Structure:**

1. Request line: ``METHOD /path HTTP/1.1``
2. Headers (one per line)
3. Empty line
4. Body (optional)

Dynamic Headers
~~~~~~~~~~~~~~~

.. code-block:: yaml

   request: |
     GET /api/data HTTP/1.1
     Host: {{ config.host }}
     Authorization: Bearer {{ login.token }}
     X-Request-Id: {{ uuid }}
     X-Timestamp: {{ timestamp }}
     {% if extra_header %}
     X-Extra: {{ extra_header }}
     {% endif %}

Dynamic Body
~~~~~~~~~~~~

.. code-block:: yaml

   request: |
     POST /api/action HTTP/1.1
     Host: {{ config.host }}
     Content-Type: application/json
     
     {
       "user_id": {{ user_id }},
       "amount": {{ amount }},
       "timestamp": "{{ timestamp }}",
       "items": [
         {% for item in items %}
         {"id": "{{ item.id }}", "qty": {{ item.qty }}}{% if not loop.last %},{% endif %}
         {% endfor %}
       ]
     }

Logger Templates
----------------

State Logging
~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     action:
       logger:
         on_state_enter: |
           Starting action...
           Target: {{ config.host }}
         
         on_state_leave: |
           Action complete.
           Status: {{ status }}
           {% if status == 200 %}
           ✓ Success
           {% else %}
           ✗ Failed
           {% endif %}

Thread Logging
~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     race_attack:
       logger:
         on_thread_enter: |
           [Thread {{ thread.id }}/{{ thread.count }}] Preparing...
         
         on_thread_leave: |
           [Thread {{ thread.id }}] Complete
           Status: {{ status }}
           Time: {{ timing_ms }}ms
           Balance: {{ balance }}

Analysis Logging
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     verify:
       logger:
         on_state_leave: |
           ==============================
           VULNERABILITY ASSESSMENT
           ==============================
           Initial balance: {{ initial_balance }}
           Final balance: {{ final_balance }}
           Difference: {{ final_balance - initial_balance }}
           
           {% if final_balance > initial_balance %}
           ⚠️ VULNERABLE: Balance increased!
           {% elif final_balance == initial_balance %}
           ✓ PROTECTED: Balance unchanged
           {% else %}
           ? UNEXPECTED: Balance decreased
           {% endif %}
           ==============================

Special Variables
-----------------

Thread Context
~~~~~~~~~~~~~~

Available in race states:

.. code-block:: yaml

   {{ thread.id }}      # Thread index (0 to N-1)
   {{ thread.count }}   # Total number of threads

Config Access
~~~~~~~~~~~~~

.. code-block:: yaml

   {{ config.host }}
   {{ config.port }}
   {{ config.threads }}
   {{ config.tls.enabled }}

State Results
~~~~~~~~~~~~~

Access extracted variables from previous states:

.. code-block:: yaml

   {{ state_name.variable_name }}
   {{ login.token }}
   {{ get_balance.amount }}

Best Practices
--------------

Security
~~~~~~~~

1. **Use env() for secrets**: Never hardcode passwords or API keys
2. **Use argv() for flexibility**: Allow runtime configuration
3. **Validate inputs**: Use conditionals to check values

Readability
~~~~~~~~~~~

1. **Use meaningful variable names**: ``auth_token`` not ``t``
2. **Add comments in YAML**: Explain complex templates
3. **Break up long templates**: Use multiple lines for clarity

Performance
~~~~~~~~~~~

1. **Minimize template complexity**: Simple templates render faster
2. **Cache computed values**: Extract once, use multiple times
3. **Avoid loops in hot paths**: Pre-compute where possible

Troubleshooting
---------------

**Template syntax error:**

* Check for unclosed ``{{ }}`` or ``{% %}``
* Verify filter syntax (use ``|`` not ``.``)
* Escape special characters if needed

**Variable not found:**

* Check variable spelling
* Verify state name prefix
* Use ``{{ variable | default('N/A') }}`` for optional values

**Filter not working:**

* Check filter name spelling
* Verify argument syntax
* Some filters require specific types

See Also
--------

* :doc:`configuration` - YAML configuration reference
* :doc:`extractors` - Data extraction methods
* :doc:`examples` - Real-world attack examples
* `Jinja2 Documentation <https://jinja.palletsprojects.com/>`_ - Full Jinja2 reference
