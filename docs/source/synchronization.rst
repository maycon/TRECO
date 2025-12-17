Synchronization Mechanisms
==========================

Understanding how TRECO synchronizes threads is crucial for achieving optimal race condition timing. This guide explains the three synchronization mechanisms available in TRECO and when to use each one.

----

Overview
--------

TRECO provides three synchronization primitives for coordinating concurrent requests:

1. **Barrier**: All threads wait until the last arrives, then release simultaneously
2. **Countdown Latch**: Threads count down to zero, then all waiting threads proceed
3. **Semaphore**: Controls the number of threads that can execute concurrently

Each mechanism has different timing characteristics and use cases.

----

Barrier (Recommended)
---------------------

The barrier synchronization mechanism provides the **best timing precision** for race condition testing.

How It Works
~~~~~~~~~~~~

1. All threads arrive at the barrier and wait
2. When the last thread arrives, all threads are released simultaneously
3. All threads proceed with their requests at the same instant

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: barrier
     connection_strategy: preconnect  # Highly recommended with barrier

Timing Characteristics
~~~~~~~~~~~~~~~~~~~~~~

* **Race Window**: < 1μs with Python 3.14t, ~10μs with Python 3.10+
* **Precision**: Excellent - highest precision available
* **Consistency**: Very consistent timing across runs
* **Best for**: True race conditions where simultaneous execution is critical

Visual Representation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Thread 1: ----[wait]-------|---> Request
   Thread 2: ------[wait]-----|---> Request
   Thread 3: --------[wait]---|---> Request
   Thread 4: ----------[wait]-|---> Request
                            ↑
                         Barrier
                    (all release together)

Use Cases
~~~~~~~~~

**Best for:**

* Double-spending attacks
* Inventory manipulation
* Fund redemption exploits
* TOCTOU vulnerabilities
* Any scenario requiring true simultaneous execution

**Example: Fund Redemption**

.. code-block:: yaml

   states:
     race_redeem:
       description: "Redeem gift card multiple times"
       request: |
         POST /api/redeem HTTP/1.1
         Authorization: Bearer {{ token }}
         {"code": "GIFT100"}
       
       race:
         threads: 20
         sync_mechanism: barrier
         connection_strategy: preconnect
       
       logger:
         on_state_leave: |
           {% if successful_requests > 1 %}
           🚨 VULNERABLE: Gift card redeemed {{ successful_requests }} times!
           {% endif %}

**Example: Double-Spending**

.. code-block:: yaml

   states:
     race_payment:
       description: "Process same payment multiple times"
       request: |
         POST /api/process-payment HTTP/1.1
         Authorization: Bearer {{ token }}
         {"token": "{{ payment_token }}"}
       
       race:
         threads: 5
         sync_mechanism: barrier
         connection_strategy: preconnect

Performance Tips
~~~~~~~~~~~~~~~~

1. **Always use with preconnect**: Eliminates connection overhead
2. **Optimal thread count**: 10-30 threads for most scenarios
3. **Python 3.14t**: Use for sub-microsecond precision
4. **Low latency network**: Test on same network or localhost

----

Countdown Latch
---------------

The countdown latch provides controlled thread release based on a countdown mechanism.

How It Works
~~~~~~~~~~~~

1. Latch is initialized with a count (equal to number of threads)
2. Each thread decrements the count when ready
3. When count reaches zero, all waiting threads proceed
4. Threads can wait before or after decrementing

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: countdown_latch
     connection_strategy: preconnect

Timing Characteristics
~~~~~~~~~~~~~~~~~~~~~~

* **Race Window**: Similar to barrier (~1-10μs depending on Python version)
* **Precision**: Excellent - comparable to barrier
* **Consistency**: Very consistent
* **Best for**: Scenarios where threads need to signal readiness

Visual Representation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Thread 1: ----ready (count: 3)----[wait]---|---> Request
   Thread 2: ------ready (count: 2)--[wait]---|---> Request
   Thread 3: --------ready (count: 1)-[wait]---|---> Request
   Thread 4: ----------ready (count: 0)--------|---> Request
                                              ↑
                                         Count = 0
                                    (all threads proceed)

Use Cases
~~~~~~~~~

**Best for:**

* Multi-stage attacks where threads need to signal completion
* Scenarios requiring controlled coordination
* When you need finer control over thread release timing
* Coordinated attacks across different endpoints

**Example: Multi-Stage Attack**

.. code-block:: yaml

   states:
     prepare:
       description: "Each thread prepares its attack"
       request: |
         POST /api/prepare HTTP/1.1
         {"session": "{{ thread.id }}"}
       
       race:
         threads: 10
         sync_mechanism: countdown_latch
         connection_strategy: preconnect
       
       next:
         - on_status: 200
           goto: execute

     execute:
       description: "Execute attack after all prepared"
       request: |
         POST /api/execute HTTP/1.1
         {"session": "{{ thread.id }}"}

**Example: Coordinated Resource Allocation**

.. code-block:: yaml

   states:
     allocate:
       description: "Allocate limited resources concurrently"
       request: |
         POST /api/allocate HTTP/1.1
         Authorization: Bearer {{ token }}
         {"resource_id": "LIMITED_RESOURCE"}
       
       race:
         threads: 50
         sync_mechanism: countdown_latch

Comparison with Barrier
~~~~~~~~~~~~~~~~~~~~~~~~

**Similarities:**

* Both provide excellent timing precision
* Both achieve sub-microsecond race windows
* Both suitable for race condition testing

**Differences:**

* Latch: Threads signal readiness before waiting
* Barrier: All threads wait at the same point
* Latch: Slightly more flexible for complex scenarios
* Barrier: Simpler mental model

**When to choose:**

* Use **barrier** for most race condition tests (simpler, well-tested)
* Use **countdown_latch** when threads need to signal readiness or completion

----

Semaphore
---------

The semaphore mechanism controls the number of threads that can execute concurrently using permits.

How It Works
~~~~~~~~~~~~

1. Semaphore is initialized with a permit count
2. Threads acquire a permit before proceeding
3. If no permits available, thread waits
4. Thread releases permit after completing
5. Waiting threads acquire released permits

.. code-block:: yaml

   race:
     threads: 50
     sync_mechanism: semaphore
     permits: 10  # Max 10 threads execute at once

Timing Characteristics
~~~~~~~~~~~~~~~~~~~~~~

* **Race Window**: Variable, depends on permit count (typically 10-100ms+)
* **Precision**: Lower than barrier/latch - not designed for tight races
* **Consistency**: Less consistent due to permit acquisition overhead
* **Best for**: Controlled concurrency, rate limiting tests

Visual Representation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Permits: [P1][P2][P3]...[P10]  (10 permits available)

   Thread 1-10:  Acquire permit → Execute → Release permit
   Thread 11-20: Wait for permit → Acquire → Execute → Release
   Thread 21-30: Wait for permit → Acquire → Execute → Release
   ...

Use Cases
~~~~~~~~~

**Best for:**

* Rate limiting bypass tests
* Controlled concurrency testing
* Testing systems under specific load levels
* Scenarios where you want to limit concurrent execution

**NOT recommended for:**

* True race condition testing (use barrier instead)
* Double-spending attacks (timing too imprecise)
* Inventory manipulation (race window too large)

**Example: Rate Limiting Test**

.. code-block:: yaml

   states:
     test_rate_limit:
       description: "Test API rate limiting"
       request: |
         GET /api/resource HTTP/1.1
         Authorization: Bearer {{ token }}
       
       race:
         threads: 100
         sync_mechanism: semaphore
         permits: 10  # Max 10 concurrent
       
       logger:
         on_state_leave: |
           Total requests: 100
           Successful: {{ successful_requests }}
           Failed (rate limited): {{ failed_requests }}
           
           {% if successful_requests > 10 %}
           ⚠️ Rate limiting bypassed!
           Expected max: 10
           Actual: {{ successful_requests }}
           {% endif %}

**Example: Controlled Load Testing**

.. code-block:: yaml

   states:
     load_test:
       description: "Test under controlled load"
       request: |
         POST /api/process HTTP/1.1
         {"data": "{{ test_data }}"}
       
       race:
         threads: 200
         sync_mechanism: semaphore
         permits: 20  # Limit to 20 concurrent

When to Use Semaphore
~~~~~~~~~~~~~~~~~~~~~

**Use semaphore when:**

* Testing rate limiting implementations
* Controlling concurrent load on system
* Testing resource exhaustion scenarios
* You need throttled concurrency

**Don't use semaphore when:**

* Testing race conditions (use barrier)
* Need sub-microsecond timing (use barrier)
* Testing double-spending (use barrier)
* Testing inventory races (use barrier)

----

Comparison Table
----------------

+-------------------------+------------------+------------------+------------------+
| Feature                 | Barrier          | Countdown Latch  | Semaphore        |
+=========================+==================+==================+==================+
| **Timing Precision**    | < 1-10μs         | < 1-10μs         | 10-100ms+        |
+-------------------------+------------------+------------------+------------------+
| **Race Window Quality** | Excellent        | Excellent        | Poor             |
+-------------------------+------------------+------------------+------------------+
| **Complexity**          | Simple           | Moderate         | Simple           |
+-------------------------+------------------+------------------+------------------+
| **Best For**            | Race conditions  | Multi-stage      | Rate limiting    |
|                         |                  | attacks          |                  |
+-------------------------+------------------+------------------+------------------+
| **Thread Coordination** | Simultaneous     | Sequential/      | Controlled       |
|                         | release          | coordinated      | concurrency      |
+-------------------------+------------------+------------------+------------------+
| **Recommended**         | ✅ Yes           | ✅ Yes           | ⚠️ Specific cases|
|                         | (most cases)     | (special cases)  | only             |
+-------------------------+------------------+------------------+------------------+

----

Choosing the Right Mechanism
-----------------------------

Decision Tree
~~~~~~~~~~~~~

.. code-block:: text

   Need to test race condition?
   │
   ├─ Yes → Need tight timing (< 10μs)?
   │        │
   │        ├─ Yes → Use BARRIER (recommended)
   │        │
   │        └─ No → Use SEMAPHORE (controlled load)
   │
   └─ No → Need controlled concurrency?
            │
            ├─ Yes → Use SEMAPHORE
            │
            └─ No → Need multi-stage coordination?
                    │
                    ├─ Yes → Use COUNTDOWN_LATCH
                    │
                    └─ No → Use BARRIER (simplest)

Quick Reference
~~~~~~~~~~~~~~~

**For Race Conditions (Most Common)**

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: barrier
     connection_strategy: preconnect

**For Rate Limiting Tests**

.. code-block:: yaml

   race:
     threads: 100
     sync_mechanism: semaphore
     permits: 10

**For Multi-Stage Attacks**

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: countdown_latch
     connection_strategy: preconnect

----

Performance Optimization
------------------------

Achieving Sub-Microsecond Timing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To achieve the best possible race window:

1. **Use Python 3.14t** (free-threaded build)

   .. code-block:: bash

      uv python install 3.14t
      uv sync

2. **Always use preconnect strategy**

   .. code-block:: yaml

      race:
        connection_strategy: preconnect  # Essential!

3. **Use barrier or countdown_latch**

   .. code-block:: yaml

      race:
        sync_mechanism: barrier  # Best timing

4. **Optimal thread count**: Start with 10-20, adjust based on results

   .. code-block:: yaml

      race:
        threads: 15  # Good starting point

5. **Test on low-latency network**: Localhost or same datacenter

Thread Count Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

**General Rules:**

* Start with 10-20 threads
* Increase gradually if needed
* Monitor race window quality
* More threads != better results

**By Attack Type:**

* **Double-spending**: 2-10 threads (usually sufficient)
* **Inventory**: 20-50 threads (depends on stock)
* **Rate limiting**: 50-200 threads (depends on limit)
* **Fund redemption**: 10-30 threads

**Signs of too many threads:**

* Increasing race window
* Connection timeouts
* System instability
* Decreased success rate

----

Common Issues
-------------

Issue: Race Window Too Large
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Race window > 100ms, race condition not triggered

**Solution**:

1. Verify preconnect is enabled:

   .. code-block:: yaml

      race:
        connection_strategy: preconnect

2. Use barrier (not semaphore):

   .. code-block:: yaml

      race:
        sync_mechanism: barrier

3. Reduce thread count if very high

4. Check network latency

5. Consider upgrading to Python 3.14t

Issue: Inconsistent Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Race window varies significantly between runs

**Possible causes**:

* Network instability
* High system load
* Wrong sync mechanism (using semaphore)
* Missing preconnect strategy

**Solution**:

.. code-block:: yaml

   race:
     threads: 15  # Moderate count
     sync_mechanism: barrier  # Best consistency
     connection_strategy: preconnect  # Essential

Issue: Connection Failures
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Threads failing to connect

**Solution**:

1. Reduce thread count
2. Increase timeout
3. Check network connectivity
4. Verify target availability

----

Examples
--------

Example 1: Optimal Race Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     race_attack:
       description: "Optimized race condition test"
       request: |
         POST /api/vulnerable-endpoint HTTP/1.1
         Authorization: Bearer {{ token }}
         {"action": "exploit"}
       
       race:
         threads: 20                    # Optimal count
         sync_mechanism: barrier         # Best timing
         connection_strategy: preconnect # Essential
         thread_propagation: single      # Default
       
       logger:
         on_state_leave: |
           Race window: {{ race_window }}μs
           {% if race_window < 1 %}
           ✓ Excellent timing!
           {% elif race_window < 10 %}
           ✓ Very good timing
           {% elif race_window < 100 %}
           ⚠ Acceptable timing
           {% else %}
           ❌ Poor timing - optimize configuration
           {% endif %}

Example 2: Rate Limiting Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     rate_limit_test:
       description: "Test API rate limiting"
       request: |
         GET /api/limited-endpoint HTTP/1.1
         X-API-Key: {{ api_key }}
       
       race:
         threads: 100                   # High count
         sync_mechanism: semaphore      # Controlled concurrency
         permits: 10                    # Match rate limit
       
       extract:
         remaining:
           type: header
           pattern: "X-RateLimit-Remaining"
       
       logger:
         on_thread_leave: |
           [Thread {{ thread.id }}] Remaining: {{ remaining }}

Example 3: Multi-Stage Coordinated Attack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     stage1:
       description: "Prepare attack"
       request: |
         POST /api/prepare HTTP/1.1
         {"session": "{{ thread.id }}"}
       
       race:
         threads: 10
         sync_mechanism: countdown_latch
       
       next:
         - on_status: 200
           goto: stage2
     
     stage2:
       description: "Execute after all prepared"
       request: |
         POST /api/execute HTTP/1.1
         {"session": "{{ thread.id }}"}
       
       race:
         threads: 10
         sync_mechanism: barrier

----

Best Practices
--------------

General Guidelines
~~~~~~~~~~~~~~~~~~

1. **Default to barrier** unless you have specific reasons to use another mechanism
2. **Always use preconnect** with barrier or countdown_latch
3. **Start with fewer threads** (10-20) and increase if needed
4. **Monitor race window** and adjust configuration accordingly
5. **Test on low-latency network** for best results

Configuration Checklist
~~~~~~~~~~~~~~~~~~~~~~~

Before running a race attack, verify:

* ✅ Using ``barrier`` or ``countdown_latch`` (not semaphore for races)
* ✅ Using ``preconnect`` strategy
* ✅ Thread count is reasonable (10-30 is typical)
* ✅ Python 3.14t installed (for best performance)
* ✅ Network latency is low
* ✅ Target system is responsive

Monitoring and Tuning
~~~~~~~~~~~~~~~~~~~~~

**Watch these metrics:**

* Race window (target: < 10μs)
* Success rate (should be high for vulnerable systems)
* Connection failures (should be zero)
* Response times (should be consistent)

**Tune based on results:**

* If race window > 100ms: Check configuration, use preconnect
* If high connection failures: Reduce thread count
* If inconsistent timing: Switch to barrier, enable preconnect
* If no successful exploits: Increase thread count or check vulnerability

----

See Also
--------

* :doc:`connection-strategies` - Connection strategy details
* :doc:`configuration` - Complete YAML reference
* :doc:`examples` - Working examples
* :doc:`best-practices` - Performance optimization