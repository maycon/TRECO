About TRECO
===========

What is TRECO?
--------------

**TRECO** (Tactical Race Exploitation & Concurrency Orchestrator) is a specialized security testing framework designed to identify and exploit race condition vulnerabilities in HTTP APIs through precise concurrent request orchestration.

TRECO enables security researchers and penetration testers to conduct sophisticated timing attacks with sub-microsecond precision, making it possible to reliably trigger race conditions that are typically difficult to reproduce in real-world scenarios.

The Problem: Race Conditions in Web Applications
-------------------------------------------------

Race conditions occur when multiple concurrent operations access shared resources without proper synchronization, leading to unexpected behavior. In web applications, these vulnerabilities can result in:

**Financial Impact**

* **Double-spending attacks**: Process the same payment multiple times
* **Fund redemption exploits**: Redeem gift cards or coupons beyond their limit
* **Credit manipulation**: Artificially increase account balances
* **Transaction bypasses**: Complete purchases without payment

**Security Impact**

* **Privilege escalation**: Gain unauthorized administrative access
* **Authentication bypasses**: Circumvent login restrictions
* **Access control violations**: Access resources beyond permissions
* **Data corruption**: Inconsistent state in databases

**Business Logic Impact**

* **Inventory manipulation**: Purchase limited items beyond stock
* **Rate limiting bypasses**: Exceed API quotas
* **Reservation conflicts**: Double-book limited resources
* **Voucher abuse**: Use single-use codes multiple times

Why Race Conditions Are Hard to Test
-------------------------------------

Traditional security testing tools struggle with race conditions because:

1. **Timing Precision**: Race windows are often measured in microseconds
2. **Network Variability**: Network latency makes timing unpredictable
3. **GIL Limitations**: Python's Global Interpreter Lock prevents true parallelism
4. **Coordination Complexity**: Synchronizing multiple threads precisely is difficult
5. **Reproducibility**: Race conditions are inherently non-deterministic

The TRECO Solution
------------------

TRECO addresses these challenges through:

**Sub-Microsecond Timing**

* Race windows consistently below 1 microsecond
* Pre-established connections eliminate TCP/TLS handshake overhead
* HTTP/2 multiplexed connections for even tighter race windows
* Barrier synchronization ensures simultaneous request dispatch
* High-resolution timing measurements for analysis

**True Parallel Execution**

* Supports Python 3.10+ with full functionality
* Optimized for Python 3.14t (free-threaded build)
* No Global Interpreter Lock (GIL) constraints with Python 3.14t
* Multiple threads execute truly in parallel
* Better CPU utilization for concurrent operations

**Flexible Synchronization Mechanisms**

* **Barrier**: All threads wait and release simultaneously (best for races)
* **Countdown Latch**: Threads count down to zero, then all proceed
* **Semaphore**: Control concurrent execution with permits

**Connection Strategies**

* **Preconnect**: Establish TCP/TLS connections before synchronization point
* **Multiplexed**: Single HTTP/2 connection shared by all threads (tightest race window)
* **Lazy**: Connect on-demand (higher latency)
* **Pooled**: Reuse connection pool

**State Machine Architecture**

* YAML-based configuration for attack flows
* Sequential state transitions with conditional logic
* Context preservation across states
* Variable extraction from responses

**Template Engine**

* Jinja2-based request templates
* Custom filters (TOTP, hashing, environment variables)
* Dynamic request generation
* Loop and conditional support

Key Features
------------

Core Capabilities
~~~~~~~~~~~~~~~~~

⚡ **Precision Timing**
   Sub-microsecond race window (< 1μs) through pre-connection and barrier synchronization

🔓 **GIL-Free Ready**
   Python 3.14t free-threaded build support for true parallel execution without GIL contention

🌐 **HTTP/2 Support**
   Multiplexed connections via httpx for tighter race windows

🔄 **Multiple Sync Mechanisms**
   Barrier, countdown latch, and semaphore patterns for different attack scenarios

🔌 **Four Connection Strategies**
   Preconnect, multiplexed, lazy, and pooled for different scenarios

🎨 **Powerful Template Engine**
   Jinja2-based with custom filters for TOTP, hashing, environment variables, and CLI arguments

📊 **Automatic Analysis**
   Race window calculation, vulnerability detection, and detailed statistics reporting

🔧 **Extensible Design**
   Plugin-based extractors (regex, JSONPath, XPath, boundary, header, cookie) and custom connection strategies

🌍 **Proxy Support**
   HTTP, HTTPS, and SOCKS5 proxy configuration

Advanced Features
~~~~~~~~~~~~~~~~~

**State Machine**

* Multi-state attack flows
* Conditional transitions based on status codes and response content
* Context sharing between states
* Sequential and parallel execution
* Thread propagation modes (single/parallel)

**Data Extraction**

* JSONPath for JSON responses
* XPath for XML/HTML responses
* Regular expressions for custom patterns
* Boundary extraction for delimiter-based data
* Header extraction for response headers
* Cookie extraction from Set-Cookie headers

**Request Templates**

* Dynamic HTTP request generation
* Variable interpolation
* Custom Jinja2 filters (totp, md5, sha1, sha256, env, argv, average)
* Multi-line support with YAML pipe syntax

**Logging & Reporting**

* Per-state and per-thread logging
* Detailed timing statistics (min, max, avg)
* Race window analysis
* Vulnerability assessment

**Thread Management**

* Configurable thread count (1-1000)
* Thread propagation strategies (single, parallel)
* Thread-safe state management
* Resource cleanup

Technical Architecture
----------------------

Components
~~~~~~~~~~

**State Machine Engine**

* Orchestrates multi-state attack flows
* Manages state transitions and context
* Handles conditional branching
* Controls thread lifecycle

**Race Coordinator**

* Manages thread synchronization
* Implements barrier/latch/semaphore patterns
* Coordinates simultaneous request dispatch
* Collects and aggregates results

**HTTP Client**

* Handles HTTP/1.1 and HTTP/2 communication
* Uses httpx for modern async HTTP support
* Manages connection lifecycle
* Pre-connection strategy implementation
* TLS/SSL and proxy configuration

**Template Engine**

* Jinja2-based request rendering
* Custom filter implementation
* Variable substitution
* Dynamic content generation

**Extractor Framework**

* Plugin-based architecture with auto-discovery
* JSONPath, XPath, Regex, Boundary, Header, Cookie extractors
* Custom extractor support via ``@register_extractor`` decorator
* Automatic variable binding

Execution Flow
~~~~~~~~~~~~~~

1. **Configuration Loading**: Parse YAML attack definition
2. **State Initialization**: Set up initial state and variables
3. **State Execution**: Execute states sequentially
4. **Race Coordination**: Synchronize threads for race attacks
5. **Request Dispatch**: Send HTTP requests simultaneously
6. **Response Processing**: Extract data and analyze results
7. **Transition Logic**: Determine next state based on conditions
8. **Reporting**: Generate detailed attack report

Design Philosophy
-----------------

**Security First**

* Designed for authorized testing only
* Clear security warnings throughout
* Responsible disclosure encouragement
* Compliance-focused design

**Precision Over Simplicity**

* Sub-microsecond timing precision prioritized
* True parallelism through GIL-free architecture
* Deterministic behavior through synchronization
* Reproducible attacks

**Flexibility and Extensibility**

* YAML-based configuration for easy customization
* Plugin architecture for extractors and strategies
* Template system for dynamic requests
* State machine for complex attack flows

**Developer Experience**

* Clear, readable YAML syntax
* Comprehensive error messages
* Detailed logging and reporting
* Easy debugging and iteration

Use Cases
---------

Penetration Testing
~~~~~~~~~~~~~~~~~~~

* **API Security Assessment**: Test REST/GraphQL APIs for race conditions
* **Payment Gateway Testing**: Verify transaction handling under concurrency
* **Authentication Testing**: Check session management and token handling
* **Authorization Testing**: Verify access control under concurrent requests

Bug Bounty Hunting
~~~~~~~~~~~~~~~~~~

* **E-commerce Platforms**: Test checkout, inventory, and payment flows
* **Financial Applications**: Verify fund transfer and balance operations
* **Booking Systems**: Check reservation and availability logic
* **Gaming Platforms**: Test in-game currency and item systems

Security Research
~~~~~~~~~~~~~~~~~

* **Vulnerability Discovery**: Systematic race condition research
* **Proof-of-Concept Development**: Create reproducible exploits
* **Attack Pattern Analysis**: Study race condition behavior
* **Defense Validation**: Verify mitigation effectiveness

Quality Assurance
~~~~~~~~~~~~~~~~~

* **Load Testing**: Verify system behavior under concurrent load
* **Stress Testing**: Identify breaking points and limits
* **Concurrency Testing**: Validate thread-safe implementations
* **Integration Testing**: Test multi-component interactions

Common Vulnerability Patterns
------------------------------

Time-of-Check to Time-of-Use (TOCTOU)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Scenario**: Check balance, then withdraw funds

.. code-block:: yaml

   states:
     race_withdraw:
       request: |
         POST /api/withdraw
         {"amount": 1000}
       race:
         threads: 10
         sync_mechanism: barrier

**Vulnerability**: Multiple withdrawals before balance update

Double-Spending
~~~~~~~~~~~~~~~

**Scenario**: Use same payment token multiple times

.. code-block:: yaml

   states:
     race_payment:
       request: |
         POST /api/process-payment
         {"token": "{{ payment_token }}"}
       race:
         threads: 5
         sync_mechanism: barrier

**Vulnerability**: Token processed multiple times

Resource Exhaustion
~~~~~~~~~~~~~~~~~~~

**Scenario**: Create more resources than limit allows

.. code-block:: yaml

   states:
     race_create:
       request: |
         POST /api/create-account
         {"plan": "free"}
       race:
         threads: 20
         sync_mechanism: barrier

**Vulnerability**: Bypass account creation limits

Limitations
-----------

**What TRECO Does**

* ✅ Test HTTP/HTTPS APIs
* ✅ Race condition exploitation
* ✅ Timing attack orchestration
* ✅ State-based attack flows

**What TRECO Doesn't Do**

* ❌ Web browser automation (use Selenium/Playwright)
* ❌ Network packet manipulation (use Scapy)
* ❌ Binary exploitation (use pwntools)
* ❌ Wireless security testing (use Aircrack-ng)

**Current Limitations**

* Single host per configuration
* Limited to API-based attacks

Requirements
------------

**Software**

* Python 3.10+ (Python 3.14t recommended for best performance)
* uv package manager (recommended)
* Linux, macOS, or Windows (WSL recommended)

**Hardware**

* Multi-core CPU (4+ cores recommended)
* 4GB+ RAM
* Stable network connection
* Low-latency network preferred

**Authorization**

* Written permission from target owner
* Defined scope and boundaries
* Compliance with applicable laws
* Responsible disclosure agreement

Project Status
--------------

**Current Version**: 1.2.0

**Development Status**: Beta

**Production Ready**: Use at your own risk

**API Stability**: Stable

Contributing
------------

TRECO is open source and welcomes contributions!

**Ways to Contribute**

* Report bugs and issues
* Suggest new features
* Submit pull requests
* Improve documentation
* Share attack patterns
* Write tutorials

**Resources**

* GitHub: https://github.com/maycon/TRECO
* Documentation: https://treco.readthedocs.io
* Issues: https://github.com/maycon/TRECO/issues

License
-------

TRECO is released under the MIT License.

**What this means:**

* ✅ Free to use
* ✅ Modify as needed
* ✅ Commercial use allowed
* ✅ Private use allowed
* ⚠️  No warranty provided
* ⚠️  Use at your own risk

See the LICENSE file for full terms.

Security and Ethics
-------------------

**Authorized Testing Only**

TRECO is designed for **authorized security testing** only. Unauthorized testing of systems you don't own or have permission to test is:

* **Illegal** in most jurisdictions
* **Unethical** in the security community
* **Harmful** to organizations and individuals
* **Punishable** by law (criminal and civil penalties)

**Responsible Usage**

* Obtain written authorization before testing
* Test only within agreed scope and boundaries
* Avoid causing damage or disruption
* Report findings responsibly and privately
* Allow reasonable time for fixes before disclosure
* Comply with all applicable laws and regulations

**Legal Disclaimer**

The developers of TRECO are not responsible for any misuse of this tool. Users are solely responsible for ensuring their use complies with applicable laws, regulations, and agreements.

Acknowledgments
---------------

TRECO was inspired by real-world security research and the need for precise race condition testing tools. Special thanks to:

* The Python community for Python 3.14t free-threaded build
* TREM project for initial inspiration
* httpx developers for modern HTTP client
* Security researchers who discovered and disclosed race condition vulnerabilities
* Open source community for tools and libraries

Support
-------

**Documentation**

* Read the Docs: https://treco.readthedocs.io
* Installation Guide: :doc:`installation`
* Quick Start: :doc:`quickstart`

**Community**

* GitHub Issues: https://github.com/maycon/TRECO/issues
* Discussions: https://github.com/maycon/TRECO/discussions

**Commercial Support**

For commercial support, training, or custom development, contact the project maintainers through GitHub.

Citation
--------

If you use TRECO in academic research, please cite:

.. code-block:: bibtex

   @software{treco2025,
     title = {TRECO: Tactical Race Exploitation \& Concurrency Orchestrator},
     author = {Vitali, Maycon Maia},
     year = {2025},
     url = {https://github.com/maycon/TRECO},
     version = {1.2.0}
   }