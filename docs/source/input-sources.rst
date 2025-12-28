Input Sources
==============

TRECO supports dynamic input distribution across race threads, enabling brute-force attacks, credential stuffing, enumeration, and combination testing.

Overview
--------

Input sources allow each thread in a race attack to use different values, making it possible to test multiple credentials, IDs, or parameters simultaneously. This is particularly useful for:

- **Brute-Force Attacks**: Each thread tries a different password
- **Credential Stuffing**: Test all username/password combinations
- **ID Enumeration**: Sequential ID or resource testing
- **Wordlist Attacks**: Load from files or built-in wordlists
- **Random Fuzzing**: Random value generation per thread

Input Modes
-----------

TRECO supports four input distribution modes:

distribute
~~~~~~~~~~

Round-robin distribution - each thread gets a different value from the input list:

.. code-block:: yaml

   entrypoint:
     state: race_attack
     input:
       username:
         mode: distribute
         values: ["user1", "user2", "user3", "user4"]

With 4 threads:
- Thread 0: user1
- Thread 1: user2
- Thread 2: user3
- Thread 3: user4

product
~~~~~~~

Cartesian product - generates all combinations of multiple inputs:

.. code-block:: yaml

   entrypoint:
     state: race_attack
     input:
       username:
         mode: product
         values: ["admin", "user"]
       password:
         mode: product
         values: ["pass123", "admin123"]

With 4 threads:
- Thread 0: admin / pass123
- Thread 1: admin / admin123
- Thread 2: user / pass123
- Thread 3: user / admin123

random
~~~~~~

Random selection - each thread randomly selects a value:

.. code-block:: yaml

   entrypoint:
     state: race_attack
     input:
       user_agent:
         mode: random
         values: ["Mozilla/5.0...", "Chrome/...", "Safari/..."]

Each thread gets a random value from the list.

same
~~~~

Same value - all threads use the same value (default):

.. code-block:: yaml

   entrypoint:
     state: race_attack
     input:
       voucher_code: "DISCOUNT50"  # All threads use this value

Input Sources
-------------

Inline Lists
~~~~~~~~~~~~

Define values directly in YAML:

.. code-block:: yaml

   input:
     username:
       mode: distribute
       values: ["alice", "bob", "charlie"]

File Sources
~~~~~~~~~~~~

Load values from external files:

.. code-block:: yaml

   input:
     password:
       mode: distribute
       source: "file:passwords.txt"

The file should contain one value per line:

.. code-block:: text

   password123
   admin123
   test123

Built-in Wordlists
~~~~~~~~~~~~~~~~~~

TRECO includes built-in wordlists for common testing scenarios:

.. code-block:: yaml

   input:
     password:
       mode: distribute
       source: "builtin:passwords-top-100"
     username:
       mode: distribute
       source: "builtin:usernames-common"

Available built-in wordlists:

- ``builtin:passwords-top-30`` - Top 30 most common passwords
- ``builtin:passwords-top-100`` - Top 100 most common passwords
- ``builtin:usernames-common`` - Common usernames
- ``builtin:user-agents-1k`` - 1000 user agent strings

Generator Expressions
~~~~~~~~~~~~~~~~~~~~~

Use Jinja2 expressions to generate values dynamically:

.. code-block:: yaml

   input:
     user_id:
       mode: distribute
       values: "{{ range(1000, 2000) }}"

This generates user IDs from 1000 to 1999.

Numeric Ranges
~~~~~~~~~~~~~~

Special syntax for numeric ranges:

.. code-block:: yaml

   input:
     transaction_id:
       mode: distribute
       source: "range:1:1000"  # IDs from 1 to 1000

Or with step:

.. code-block:: yaml

   input:
     port:
       mode: distribute
       source: "range:8000:9000:10"  # Ports 8000, 8010, 8020, ...

Examples
--------

Password Brute-Force
~~~~~~~~~~~~~~~~~~~~

Test multiple passwords against a login endpoint:

.. code-block:: yaml

   metadata:
     name: "Password Brute-Force"
   
   target:
     host: "api.example.com"
     port: 443
     tls:
       enabled: true
   
   entrypoint:
     state: login_attack
     input:
       username: "admin"
       password:
         mode: distribute
         source: "builtin:passwords-top-100"
   
   states:
     login_attack:
       description: "Try multiple passwords"
       race:
         threads: 100
         sync_mechanism: barrier
       
       request: |
         POST /api/login HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/json
         
         {"username": "{{ username }}", "password": "{{ password }}"}
       
       next:
         - on_status: 200
           goto: success
         - on_status: 401
           goto: end
     
     success:
       description: "Password found!"
       request: |
         GET /api/profile HTTP/1.1
         Host: {{ config.host }}
     
     end:
       description: "Attack completed"

Credential Stuffing
~~~~~~~~~~~~~~~~~~~

Test username/password combinations:

.. code-block:: yaml

   entrypoint:
     state: credential_test
     input:
       username:
         mode: product
         source: "file:usernames.txt"
       password:
         mode: product
         source: "file:passwords.txt"
   
   states:
     credential_test:
       race:
         threads: 50
       
       request: |
         POST /api/login HTTP/1.1
         Content-Type: application/json
         
         {"user": "{{ username }}", "pass": "{{ password }}"}

ID Enumeration
~~~~~~~~~~~~~~

Enumerate resource IDs:

.. code-block:: yaml

   entrypoint:
     state: enum_resources
     input:
       resource_id:
         mode: distribute
         source: "range:1:10000"
   
   states:
     enum_resources:
       race:
         threads: 100
       
       request: |
         GET /api/resource/{{ resource_id }} HTTP/1.1
         Host: {{ config.host }}
       
       next:
         - on_status: 200
           goto: found
         - on_status: 404
           goto: end
     
     found:
       description: "Resource exists!"

User Agent Rotation
~~~~~~~~~~~~~~~~~~~

Rotate user agents to avoid detection:

.. code-block:: yaml

   entrypoint:
     state: scrape
     input:
       user_agent:
         mode: random
         source: "builtin:user-agents-1k"
   
   states:
     scrape:
       race:
         threads: 20
       
       request: |
         GET /api/data HTTP/1.1
         User-Agent: {{ user_agent }}

Best Practices
--------------

Thread Count vs Input Size
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Match thread count to input size:

.. code-block:: yaml

   # Good: 100 passwords, 100 threads
   input:
     password:
       mode: distribute
       source: "builtin:passwords-top-100"
   
   states:
     attack:
       race:
         threads: 100

If threads > inputs, values will be reused:

.. code-block:: yaml

   # 10 passwords, 20 threads
   # Values will cycle: 0-9, then 0-9 again
   input:
     password:
       mode: distribute
       values: [...10 passwords...]
   
   states:
     attack:
       race:
         threads: 20

Rate Limiting Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using distribute or product modes, be aware of rate limiting:

.. code-block:: yaml

   # This might trigger rate limiting
   states:
     attack:
       race:
         threads: 1000  # Too many simultaneous requests

Consider using smaller batches or delays:

.. code-block:: yaml

   states:
     attack:
       race:
         threads: 50  # More reasonable
       timeout: 30

Memory Usage
~~~~~~~~~~~~

Large input sources consume memory. For very large wordlists, consider:

1. Using file sources instead of inline values
2. Reducing thread count
3. Breaking attack into multiple runs

Performance Tips
~~~~~~~~~~~~~~~~

1. **Use Built-in Wordlists**: Faster than loading from files
2. **Optimize Thread Count**: Match input size when using distribute
3. **Cache File Sources**: File contents are cached after first load
4. **Use Generators**: Jinja2 generators are memory-efficient

Common Patterns
---------------

Multi-Factor Testing
~~~~~~~~~~~~~~~~~~~~

Test multiple factors with product mode:

.. code-block:: yaml

   input:
     username:
       mode: product
       values: ["admin", "user", "guest"]
     password:
       mode: product
       source: "builtin:passwords-top-30"
     mfa_code:
       mode: product
       values: "{{ range(0, 10000) | map('string') | map('zfill', 4) }}"

Sequential Testing
~~~~~~~~~~~~~~~~~~

Test IDs sequentially:

.. code-block:: yaml

   input:
     order_id:
       mode: distribute
       source: "range:1000:2000"

Random Fuzzing
~~~~~~~~~~~~~~

Generate random values:

.. code-block:: yaml

   input:
     random_param:
       mode: random
       values: "{{ range(1000000) | random }}"

Troubleshooting
---------------

Thread Count Mismatch
~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Unexpected value distribution

**Solution**: Ensure thread count matches input size for distribute mode:

.. code-block:: yaml

   # BAD: 10 values, 20 threads
   input:
     password:
       mode: distribute
       values: [...10 items...]
   states:
     attack:
       race:
         threads: 20  # Values will cycle
   
   # GOOD: 10 values, 10 threads
   input:
     password:
       mode: distribute
       values: [...10 items...]
   states:
     attack:
       race:
         threads: 10

File Not Found
~~~~~~~~~~~~~~

**Problem**: Cannot load file source

**Solution**: Use absolute or relative paths:

.. code-block:: yaml

   # Relative to config file
   source: "file:wordlists/passwords.txt"
   
   # Absolute path
   source: "file:/home/user/wordlists/passwords.txt"

Product Mode Too Large
~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Product mode generates too many combinations

**Solution**: Reduce input sizes or use distribute:

.. code-block:: yaml

   # BAD: 1000 x 1000 = 1,000,000 combinations
   input:
     username:
       mode: product
       source: "range:1:1000"
     password:
       mode: product
       source: "range:1:1000"
   
   # GOOD: Test separately
   input:
     username:
       mode: distribute
       source: "range:1:1000"

See Also
--------

- :doc:`configuration` - Full configuration reference
- :doc:`templates` - Template engine and filters
- :doc:`examples` - Real-world examples
- :doc:`best-practices` - Performance optimization
