Connection Strategies
=====================

Connection strategies determine how TRECO establishes and manages TCP/TLS connections for HTTP requests. The choice of connection strategy significantly impacts race window timing and overall performance.

----

Overview
--------

TRECO provides four connection strategies:

1. **Preconnect** (Recommended): Establish connections before synchronization point
2. **Lazy**: Connect on-demand when sending requests
3. **Pooled**: Share connection pool across threads
4. **Multiplexed**: HTTP/2 multiplexing over single connection

Each strategy has different performance characteristics and use cases.

----

Preconnect Strategy (Recommended)
----------------------------------

The preconnect strategy provides the **best timing precision** for race condition testing by eliminating connection overhead from the race window.

How It Works
~~~~~~~~~~~~

1. Establish TCP/TLS connections for all threads **before** reaching the synchronization point
2. Threads perform complete handshake (TCP + TLS if applicable)
3. Connections are ready and warm when threads synchronize
4. Threads send requests immediately after release from barrier
5. No connection setup time included in race window

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: barrier
     connection_strategy: preconnect  # Recommended for race conditions

Performance Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Race Window**: < 1μs with Python 3.14t, ~10μs with Python 3.10+
* **Connection Overhead**: Eliminated from race window
* **Memory Usage**: Higher (one connection per thread)
* **CPU Usage**: Moderate (during connection phase)
* **Best For**: Race condition testing (all types)

Visual Representation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Timeline:

   [Pre-connection Phase]
   Thread 1: TCP handshake → TLS handshake → [Ready]
   Thread 2: TCP handshake → TLS handshake → [Ready]
   Thread 3: TCP handshake → TLS handshake → [Ready]
   Thread 4: TCP handshake → TLS handshake → [Ready]

   [Synchronization Phase]
   All threads: [Wait at barrier] → [Release] → Send requests
                                              ↑
                                    Race window starts here
                                    (no connection overhead!)

Advantages
~~~~~~~~~~

**✅ Eliminates Connection Overhead**
   TCP and TLS handshakes completed before race, resulting in sub-microsecond race windows

**✅ Consistent Timing**
   All threads start from the same ready state, minimizing timing variance

**✅ Best Success Rate**
   Highest probability of triggering race conditions

**✅ Predictable Performance**
   Connection issues detected before the race begins

**✅ Optimal for Python 3.14t**
   Fully leverages GIL-free parallelism for connection establishment

Disadvantages
~~~~~~~~~~~~~

**❌ Higher Memory Usage**
   Maintains one connection per thread simultaneously

**❌ More Socket Descriptors**
   May hit OS limits with very high thread counts (>100)

**❌ Connection Establishment Time**
   Additional upfront time before race begins (but not in race window)

**❌ Server Load**
   Creates burst of connections during setup phase

Use Cases
~~~~~~~~~

**Ideal for:**

* ✅ All race condition testing
* ✅ Double-spending attacks
* ✅ Inventory manipulation
* ✅ Fund redemption exploits
* ✅ TOCTOU vulnerabilities
* ✅ Any scenario requiring sub-microsecond timing

**Example: Double-Spending Attack**

.. code-block:: yaml

   states:
     race_payment:
       description: "Process payment multiple times"
       request: |
         POST /api/process-payment HTTP/1.1
         Authorization: Bearer {{ token }}
         Content-Type: application/json
         
         {"payment_token": "{{ payment_token }}"}
       
       race:
         threads: 5
         sync_mechanism: barrier
         connection_strategy: preconnect  # Essential for timing
       
       logger:
         on_state_leave: |
           Race window: {{ race_window }}μs
           {% if race_window < 1 %}
           ✓ EXCELLENT: Sub-microsecond precision
           {% elif race_window < 10 %}
           ✓ VERY GOOD: Optimal for race conditions
           {% else %}
           ⚠ Check configuration
           {% endif %}

**Example: Inventory Race**

.. code-block:: yaml

   states:
     race_purchase:
       description: "Purchase limited stock concurrently"
       request: |
         POST /api/purchase HTTP/1.1
         Authorization: Bearer {{ token }}
         Content-Type: application/json
         
         {"item_id": "LIMITED_001", "quantity": 1}
       
       race:
         threads: 50
         sync_mechanism: barrier
         connection_strategy: preconnect

Configuration Tips
~~~~~~~~~~~~~~~~~~

**Optimal Configuration:**

.. code-block:: yaml

   race:
     threads: 20                    # Reasonable count
     sync_mechanism: barrier         # Best with preconnect
     connection_strategy: preconnect # Always use for races
     thread_propagation: single      # Default

**Thread Count Guidelines:**

* Start with 10-20 threads
* Increase gradually if needed
* Monitor connection success rate
* Consider system limits (ulimit -n)

**System Tuning:**

.. code-block:: bash

   # Check current file descriptor limit
   ulimit -n

   # Increase if needed (temporary)
   ulimit -n 4096

   # Permanent (add to /etc/security/limits.conf)
   * soft nofile 4096
   * hard nofile 4096

----

Lazy Strategy
-------------

The lazy strategy connects on-demand when sending each request, without pre-establishing connections.

How It Works
~~~~~~~~~~~~

1. Threads synchronize at barrier/latch
2. Threads are released simultaneously
3. Each thread establishes TCP/TLS connection **after** release
4. Connection overhead included in race window
5. Requests sent after connection completes

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: barrier
     connection_strategy: lazy  # Not recommended for races

Performance Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Race Window**: 50-500ms+ (includes connection time)
* **Connection Overhead**: Included in race window
* **Memory Usage**: Lower (connects only when needed)
* **CPU Usage**: Lower overall
* **Best For**: Testing connection timing, sequential requests

Visual Representation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Timeline:

   [Synchronization Phase]
   All threads: [Wait at barrier] → [Release] → Connect → Send requests
                                              ↑
                                    Race window starts here
                                    (includes connection overhead!)

   Thread 1: TCP → TLS → Request (total: 100ms)
   Thread 2: TCP → TLS → Request (total: 105ms)
   Thread 3: TCP → TLS → Request (total: 98ms)
   Thread 4: TCP → TLS → Request (total: 110ms)

   Race window: ~12ms (variation in connection times)

Advantages
~~~~~~~~~~

**✅ Lower Memory Usage**
   Connections created only when needed

**✅ Simpler Implementation**
   No pre-connection management required

**✅ Tests Real Conditions**
   Includes connection overhead in timing

**✅ Fewer Socket Descriptors**
   Suitable for very high thread counts

Disadvantages
~~~~~~~~~~~~~

**❌ Poor Timing Precision**
   Race window typically 50-500ms or more

**❌ Variable Timing**
   Connection times introduce significant variance

**❌ Lower Success Rate**
   Difficult to trigger race conditions reliably

**❌ Not Suitable for Races**
   Should not be used for race condition testing

Use Cases
~~~~~~~~~

**Suitable for:**

* Testing connection timing vulnerabilities
* Sequential request testing
* Low-resource environments
* Scenarios where connection timing matters

**NOT suitable for:**

* ❌ Race condition testing
* ❌ Double-spending attacks
* ❌ Inventory manipulation
* ❌ Time-sensitive exploits

**Example: Connection Timing Test**

.. code-block:: yaml

   states:
     test_connection:
       description: "Test authentication during connection"
       request: |
         GET /api/resource HTTP/1.1
         Authorization: Bearer {{ token }}
       
       race:
         threads: 10
         sync_mechanism: barrier
         connection_strategy: lazy  # Include connection in timing
       
       logger:
         on_thread_leave: |
           [Thread {{ thread.id }}] Total time: {{ response_time }}ms
           (includes connection establishment)

When to Use
~~~~~~~~~~~

Use lazy strategy when:

* Testing scenarios where connection timing is relevant
* Memory is severely constrained
* You need many threads (>100) with socket descriptor limits
* Not testing race conditions

Don't use lazy strategy when:

* Testing race conditions (use preconnect)
* Need sub-100ms timing precision (use preconnect)
* Testing double-spending or similar (use preconnect)

----

Pooled Strategy
---------------

The pooled strategy shares a connection pool across threads, reusing connections for multiple requests.

How It Works
~~~~~~~~~~~~

1. Connection pool created with configurable size
2. Threads acquire connection from pool
3. Requests serialized through pool
4. Connection released back to pool after use
5. Next thread acquires same connection

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: barrier
     connection_strategy: pooled
     pool_size: 5  # Share 5 connections among 20 threads

Performance Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Race Window**: Variable, depends on pool size and contention
* **Connection Overhead**: Mixed (first request per connection, then reuse)
* **Memory Usage**: Low (limited by pool size)
* **CPU Usage**: Low
* **Best For**: Sequential testing, connection reuse scenarios

Visual Representation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Connection Pool: [C1][C2][C3][C4][C5]

   Thread 1: Acquire C1 → Request → Release C1
   Thread 2: Acquire C2 → Request → Release C2
   Thread 3: Acquire C3 → Request → Release C3
   Thread 4: Acquire C4 → Request → Release C4
   Thread 5: Acquire C5 → Request → Release C5
   Thread 6: Wait for C1 → Acquire C1 → Request → Release C1
   ...

   Serialization: Threads wait for available connections

Advantages
~~~~~~~~~~

**✅ Resource Efficient**
   Limited number of connections regardless of thread count

**✅ Connection Reuse**
   Amortizes connection overhead across requests

**✅ Predictable Resource Usage**
   Won't exceed pool size connections

**✅ Server-Friendly**
   Limits connection burst to target

Disadvantages
~~~~~~~~~~~~~

**❌ Serializes Requests**
   Threads wait for available connections, destroying race timing

**❌ Unpredictable Timing**
   Pool contention introduces significant variance

**❌ NOT for Race Conditions**
   Should never be used for race condition testing

**❌ Complex Behavior**
   Pool dynamics can be difficult to reason about

Use Cases
~~~~~~~~~

**Suitable for:**

* Connection reuse testing
* Sequential request patterns
* Resource-constrained environments
* Testing keep-alive behavior

**NOT suitable for:**

* ❌ Race condition testing (destroys timing)
* ❌ Concurrent request scenarios
* ❌ Double-spending or inventory races
* ❌ Any scenario requiring simultaneous execution

**Example: Sequential API Testing**

.. code-block:: yaml

   states:
     sequential_test:
       description: "Test API with connection reuse"
       request: |
         GET /api/data/{{ thread.id }} HTTP/1.1
         Authorization: Bearer {{ token }}
       
       race:
         threads: 50
         sync_mechanism: semaphore
         connection_strategy: pooled
         pool_size: 10  # Reuse 10 connections
       
       logger:
         on_thread_leave: |
           [Thread {{ thread.id }}] Completed using pooled connection

When to Use
~~~~~~~~~~~

Use pooled strategy when:

* Testing connection reuse behavior
* Making sequential requests
* Need to limit connections to server
* Testing keep-alive functionality

Don't use pooled strategy when:

* Testing race conditions (use preconnect)
* Need concurrent execution (use preconnect)
* Timing precision matters (use preconnect)

----

Multiplexed Strategy
--------------------

The multiplexed strategy uses HTTP/2 multiplexing to send multiple requests over a single connection.

How It Works
~~~~~~~~~~~~

1. Single HTTP/2 connection established
2. Multiple streams created over connection
3. Requests multiplexed over streams
4. Server processes streams concurrently (if supported)
5. Responses received asynchronously

.. code-block:: yaml

   race:
     threads: 20
     sync_mechanism: barrier
     connection_strategy: multiplexed
     http_version: "2"  # Required

Performance Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Race Window**: Variable, depends on HTTP/2 support and implementation
* **Connection Overhead**: Single connection for all requests
* **Memory Usage**: Low (single connection)
* **CPU Usage**: Moderate (stream management)
* **Best For**: HTTP/2-specific testing

Visual Representation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Single HTTP/2 Connection
   │
   ├─ Stream 1: Request 1 → Response 1
   ├─ Stream 2: Request 2 → Response 2
   ├─ Stream 3: Request 3 → Response 3
   ├─ Stream 4: Request 4 → Response 4
   └─ ...

   All streams over single TCP connection

Advantages
~~~~~~~~~~

**✅ Single Connection**
   Minimal connection overhead and resource usage

**✅ HTTP/2 Features**
   Access to header compression, server push, etc.

**✅ Server-Friendly**
   Single connection to server

**✅ Efficient for High Thread Counts**
   No socket descriptor limits

Disadvantages
~~~~~~~~~~~~~

**❌ Requires HTTP/2**
   Not all servers support HTTP/2

**❌ Complex Implementation**
   HTTP/2 adds significant complexity

**❌ Stream Ordering**
   Server may process streams sequentially despite concurrency

**❌ Unpredictable Timing**
   Difficult to achieve precise race windows

Use Cases
~~~~~~~~~

**Suitable for:**

* HTTP/2-specific vulnerability testing
* Testing stream-based race conditions
* Server push vulnerabilities
* Header compression attacks

**NOT typically suitable for:**

* Traditional race condition testing (use preconnect)
* Double-spending attacks (use preconnect)
* Most common vulnerabilities (use preconnect)

**Example: HTTP/2 Stream Race**

.. code-block:: yaml

   states:
     http2_race:
       description: "Test HTTP/2 stream handling"
       request: |
         POST /api/resource HTTP/2
         Authorization: Bearer {{ token }}
         {"action": "process"}
       
       race:
         threads: 10
         sync_mechanism: barrier
         connection_strategy: multiplexed
       
       logger:
         on_state_leave: |
           Tested HTTP/2 multiplexing with {{ threads }} streams

When to Use
~~~~~~~~~~~

Use multiplexed strategy when:

* Specifically testing HTTP/2 vulnerabilities
* Target only supports HTTP/2
* Testing stream-based race conditions
* Testing server push behavior

Don't use multiplexed strategy when:

* Target doesn't support HTTP/2
* Testing traditional race conditions (use preconnect)
* Need predictable timing (use preconnect)
* HTTP/1.1 is sufficient (use preconnect)

----

Comparison Table
----------------

+---------------------------+---------------+---------------+---------------+---------------+
| Feature                   | Preconnect    | Lazy          | Pooled        | Multiplexed   |
+===========================+===============+===============+===============+===============+
| **Race Window**           | < 1-10μs      | 50-500ms+     | Variable      | Variable      |
+---------------------------+---------------+---------------+---------------+---------------+
| **Precision**             | Excellent     | Poor          | Poor          | Moderate      |
+---------------------------+---------------+---------------+---------------+---------------+
| **Memory Usage**          | High          | Low           | Low           | Very Low      |
+---------------------------+---------------+---------------+---------------+---------------+
| **Connection Overhead**   | Before race   | In race       | Mixed         | Single conn   |
+---------------------------+---------------+---------------+---------------+---------------+
| **Best For**              | Race          | Connection    | Sequential    | HTTP/2        |
|                           | conditions    | timing        | testing       | testing       |
+---------------------------+---------------+---------------+---------------+---------------+
| **Recommended**           | ✅ Yes        | ⚠️ Rarely     | ⚠️ Rarely     | ⚠️ Specific   |
|                           |               |               |               | cases         |
+---------------------------+---------------+---------------+---------------+---------------+
| **Race Testing**          | ✅ Excellent  | ❌ Poor       | ❌ Poor       | ⚠️ Limited    |
+---------------------------+---------------+---------------+---------------+---------------+

----

Choosing the Right Strategy
----------------------------

Decision Tree
~~~~~~~~~~~~~

.. code-block:: text

   Testing race condition?
   │
   ├─ Yes → Use PRECONNECT
   │        (99% of cases)
   │
   └─ No → Testing HTTP/2?
           │
           ├─ Yes → Use MULTIPLEXED
           │
           └─ No → Need connection reuse?
                   │
                   ├─ Yes → Use POOLED
                   │
                   └─ No → Testing connection timing?
                           │
                           ├─ Yes → Use LAZY
                           │
                           └─ No → Use PRECONNECT
                                   (safest default)

Quick Reference
~~~~~~~~~~~~~~~

**For Race Conditions (99% of cases):**

.. code-block:: yaml

   race:
     connection_strategy: preconnect  # Always use this
     sync_mechanism: barrier
     threads: 20

**For HTTP/2 Testing:**

.. code-block:: yaml

   race:
     connection_strategy: multiplexed
     http_version: "2"

**For Connection Reuse:**

.. code-block:: yaml

   race:
     connection_strategy: pooled
     pool_size: 10

**For Connection Timing:**

.. code-block:: yaml

   race:
     connection_strategy: lazy

----

Performance Optimization
------------------------

Achieving Optimal Timing
~~~~~~~~~~~~~~~~~~~~~~~~

To achieve the best possible race window with preconnect:

**1. Use Python 3.14t**

.. code-block:: bash

   uv python install 3.14t
   uv sync

**2. Configure for optimal performance**

.. code-block:: yaml

   race:
     threads: 20                    # Reasonable count
     sync_mechanism: barrier         # Best timing
     connection_strategy: preconnect # Essential!
     thread_propagation: single

**3. Test on low-latency network**

* Localhost: Best (< 1ms latency)
* Same datacenter: Excellent (< 10ms)
* Same region: Good (< 50ms)
* Different regions: Poor (> 100ms)

**4. Monitor and tune**

.. code-block:: yaml

   logger:
     on_state_leave: |
       Race window: {{ race_window }}μs
       
       {% if race_window < 1 %}
       ✓ Excellent: Sub-microsecond precision
       {% elif race_window < 10 %}
       ✓ Very Good: Optimal for most races
       {% elif race_window < 100 %}
       ⚠ Good: May need optimization
       {% else %}
       ❌ Poor: Check configuration
       {% endif %}

Troubleshooting Connection Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue: Connection timeouts**

*Solution:*

.. code-block:: yaml

   target:
     timeout: 60  # Increase timeout
   
   race:
     threads: 10  # Reduce thread count

**Issue: Too many open files**

*Solution:*

.. code-block:: bash

   # Check limit
   ulimit -n
   
   # Increase limit
   ulimit -n 4096

**Issue: Connection refused**

*Solution:*

* Check target is accessible
* Verify firewall rules
* Confirm port is correct
* Reduce thread count

----

Examples
--------

Example 1: Optimal Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   metadata:
     name: "Optimal Race Configuration"
   
   target:
     host: "api.example.com"
     port: 443
     tls:
       enabled: true
       verify_cert: true
   
   states:
     race_attack:
       request: |
         POST /api/vulnerable HTTP/1.1
         Authorization: Bearer {{ token }}
       
       race:
         threads: 20
         sync_mechanism: barrier
         connection_strategy: preconnect  # Optimal!
       
       logger:
         on_state_leave: |
           Configuration: OPTIMAL
           - Strategy: preconnect ✓
           - Sync: barrier ✓
           - Threads: {{ threads }}
           - Race window: {{ race_window }}μs

Example 2: HTTP/2 Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     http2_test:
       request: |
         POST /api/resource HTTP/2
         Authorization: Bearer {{ token }}
       
       race:
         threads: 10
         sync_mechanism: barrier
         connection_strategy: multiplexed
         http_version: "2"

Example 3: Connection Reuse
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   states:
     reuse_test:
       request: |
         GET /api/data HTTP/1.1
         Connection: keep-alive
       
       race:
         threads: 50
         sync_mechanism: semaphore
         connection_strategy: pooled
         pool_size: 10

----

Best Practices
--------------

General Guidelines
~~~~~~~~~~~~~~~~~~

1. **Default to preconnect** for all race condition testing
2. **Use barrier sync** with preconnect for best results
3. **Monitor race window** and optimize based on results
4. **Test on low-latency network** for best timing
5. **Start with moderate thread counts** (10-20)

Configuration Checklist
~~~~~~~~~~~~~~~~~~~~~~~

Before running a race attack:

* ✅ Using ``preconnect`` strategy
* ✅ Using ``barrier`` or ``countdown_latch`` sync
* ✅ Thread count is reasonable (10-30 typical)
* ✅ Python 3.14t installed (for best performance)
* ✅ Network latency is low (< 50ms)
* ✅ Target system is accessible

Common Mistakes to Avoid
~~~~~~~~~~~~~~~~~~~~~~~~

**❌ Using lazy for race conditions**

.. code-block:: yaml

   # DON'T DO THIS for race testing:
   race:
     connection_strategy: lazy  # Will fail!

**❌ Using pooled for race conditions**

.. code-block:: yaml

   # DON'T DO THIS for race testing:
   race:
     connection_strategy: pooled  # Serializes requests!

**❌ Too many threads with preconnect**

.. code-block:: yaml

   # May cause issues:
   race:
     threads: 500  # Too many connections
     connection_strategy: preconnect

**✅ Correct configuration**

.. code-block:: yaml

   # DO THIS for race testing:
   race:
     threads: 20
     sync_mechanism: barrier
     connection_strategy: preconnect

----

See Also
--------

* :doc:`synchronization` - Synchronization mechanisms
* :doc:`configuration` - Complete YAML reference
* :doc:`examples` - Working examples
* :doc:`best-practices` - Performance optimization
* :doc:`troubleshooting` - Common issues and solutions