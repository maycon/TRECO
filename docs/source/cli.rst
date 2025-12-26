Command-Line Interface
======================

TRECO provides a command-line interface for running race condition attacks.

Basic Usage
-----------

.. code-block:: bash

   treco [OPTIONS] CONFIG_FILE

**Arguments:**

* ``CONFIG_FILE`` - Path to the YAML configuration file (required)

Options
-------

Authentication Options
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   --user USERNAME       Username for authentication
   --password PASSWORD   Password for authentication (prefer env var)
   --seed SEED          TOTP seed for 2FA generation

**Example:**

.. code-block:: bash

   treco attack.yaml --user alice --password secret123
   treco attack.yaml --user admin --seed JBSWY3DPEHPK3PXP

Target Options
~~~~~~~~~~~~~~

.. code-block:: bash

   --host HOST          Override target hostname
   --port PORT          Override target port

**Example:**

.. code-block:: bash

   treco attack.yaml --host api.staging.example.com --port 8443

Execution Options
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   --threads COUNT      Override thread count for race attacks

**Example:**

.. code-block:: bash

   treco attack.yaml --threads 50

Output Options
~~~~~~~~~~~~~~

.. code-block:: bash

   --verbose, -v        Enable verbose/debug output

**Example:**

.. code-block:: bash

   treco attack.yaml --verbose
   treco attack.yaml -v

Information Options
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   --version            Show version number
   --help               Show help message

**Example:**

.. code-block:: bash

   treco --version
   treco --help

Using uv
--------

When running with ``uv``, prefix commands with ``uv run``:

.. code-block:: bash

   # Basic usage
   uv run treco attack.yaml
   
   # With options
   uv run treco attack.yaml --user alice --threads 20
   
   # Verbose mode
   uv run treco attack.yaml -v

Or activate the virtual environment first:

.. code-block:: bash

   source .venv/bin/activate
   treco attack.yaml --user alice

Environment Variables
---------------------

TRECO can read sensitive data from environment variables using the ``env()`` filter in YAML:

.. code-block:: bash

   # Set environment variables
   export USERNAME='testuser'
   export PASSWORD='secretpassword'
   export API_KEY='abc123xyz'
   export TOTP_SEED='JBSWY3DPEHPK3PXP'
   
   # Run attack
   treco attack.yaml

Reference in YAML:

.. code-block:: yaml

   entrypoint:
     state: login
      input:
      username: "{{ env('USERNAME') }}"
      password: "{{ env('PASSWORD') }}"
      api_key: "{{ env('API_KEY', 'default_key') }}"

Complete Examples
-----------------

Basic Attack
~~~~~~~~~~~~

.. code-block:: bash

   treco configs/simple-attack.yaml

With Authentication
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   treco configs/auth-attack.yaml --user admin --password admin123

With 2FA
~~~~~~~~

.. code-block:: bash

   export TOTP_SEED='JBSWY3DPEHPK3PXP'
   treco configs/2fa-attack.yaml --user admin

Custom Target
~~~~~~~~~~~~~

.. code-block:: bash

   treco configs/attack.yaml --host staging.example.com --port 8443

High Thread Count
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   treco configs/race-attack.yaml --threads 100

Full Example with All Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   export PASSWORD='secret'
   uv run treco configs/full-attack.yaml \
     --user alice \
     --host api.staging.example.com \
     --port 443 \
     --threads 30 \
     --seed JBSWY3DPEHPK3PXP \
     --verbose

Exit Codes
----------

TRECO uses standard exit codes:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Code
     - Meaning
   * - 0
     - Success - attack completed normally
   * - 1
     - Error - attack failed
   * - 130
     - Interrupted - user pressed Ctrl+C

Output Format
-------------

TRECO outputs detailed information during execution:

.. code-block:: text

   ======================================================================
   Treco - Race Condition PoC Framework
   ======================================================================
   Attack: Double Redemption Test
   Version: 1.0
   Vulnerability: CWE-362
   Target: https://api.example.com:443
   ======================================================================

   Executing state: login
   [State] Status: 200
   Extracted: {'token': 'eyJhbGciOiJIUzI1NiIs...'}

   ======================================================================
   RACE ATTACK: race_attack
   ======================================================================
   Threads: 20
   Sync Mechanism: barrier
   Connection Strategy: preconnect
   Thread Propagation: single
   ======================================================================

   [Thread 0] Ready, waiting at sync point...
   [Thread 1] Ready, waiting at sync point...
   ...

   ======================================================================
   RACE ATTACK RESULTS
   ======================================================================
   Total threads: 20
   Successful: 18
   Failed: 2

   Timing Analysis:
     Average response time: 46.5ms
     Fastest response: 45.2ms
     Slowest response: 48.7ms
     Race window: 3.5ms
     ✓ EXCELLENT race window (< 1ms)

   Vulnerability Assessment:
     ⚠ VULNERABLE: Multiple requests succeeded (18)
     ⚠ Potential race condition detected!
   ======================================================================

   ======================================================================
   Attack Completed Successfully
   ======================================================================

   ✓ Attack completed successfully
     Total states executed: 4

Tips and Best Practices
-----------------------

Security
~~~~~~~~

1. **Never pass passwords on command line** - Use environment variables instead
2. **Use --seed for TOTP** - Only when the seed is not sensitive
3. **Store configs securely** - Don't commit sensitive data to version control

Debugging
~~~~~~~~~

1. **Start with --verbose** - See detailed execution flow
2. **Use fewer threads first** - Start with 5-10 threads
3. **Check network connectivity** - Verify target is reachable

Performance
~~~~~~~~~~~

1. **Adjust thread count** - Usually 10-30 is optimal
2. **Test on same network** - Lower latency = better race precision
3. **Monitor system resources** - Too many threads can hurt performance

See Also
--------

* :doc:`configuration` - YAML configuration reference
* :doc:`quickstart` - Getting started guide
* :doc:`examples` - Real-world attack examples
