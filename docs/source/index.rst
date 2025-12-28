TRECO Documentation
===================

.. image:: ../../static/treco.png
   :alt: TRECO Logo
   :align: center
   :width: 220px

.. raw:: html

   <div align="center">
   <h2>Tactical Race Exploitation & Concurrency Orchestrator</h2>
   <p><em>A specialized framework for identifying and exploiting race condition vulnerabilities in HTTP APIs with sub-microsecond precision.</em></p>
   </div>

.. image:: https://img.shields.io/badge/python-3.14t-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.14t

.. image:: https://img.shields.io/badge/python-3.10%2B-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.10+

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

.. image:: https://img.shields.io/badge/GIL-Free-green.svg
   :target: https://peps.python.org/pep-0703/
   :alt: Free-Threaded

----

Welcome to TRECO
----------------

TRECO enables security researchers to orchestrate highly precise concurrent HTTP attacks with **sub-microsecond timing accuracy**, making it possible to reliably trigger race conditions in web applications. Built for both Python 3.10+ (with GIL) and Python 3.14t (GIL-free), TRECO achieves unprecedented timing precision for race condition exploitation.

**Quick Links:**

* :doc:`installation` - Get started in 5 minutes
* :doc:`quickstart` - Your first race condition test
* :doc:`examples` - Real-world attack scenarios
* `GitHub Repository <https://github.com/maycon/TRECO>`_

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   about
   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   configuration
   input-sources
   extractors
   templates
   when-blocks
   synchronization
   connection-strategies
   advanced-features
   examples

.. toctree::
   :maxdepth: 2
   :caption: Reference
   :hidden:

   cli
   api
   troubleshooting
   best-practices

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources
   :hidden:

   contributing
   license

----

Overview
--------

TRECO is a specialized framework designed for **authorized security testing** of web applications, focusing on race condition vulnerabilities that are notoriously difficult to detect and exploit.

What Makes TRECO Unique
~~~~~~~~~~~~~~~~~~~~~~~~

**Sub-Microsecond Precision**
   Race windows consistently below 1 microsecond through pre-connection and barrier synchronization, making it possible to reliably trigger even the most difficult race conditions.

**True Parallelism**
   Built specifically for Python 3.14t free-threaded build, eliminating GIL constraints for genuine concurrent execution. Also works with Python 3.10+ with good performance.

**State Machine Architecture**
   Complex multi-state attack flows with conditional transitions, allowing sophisticated testing scenarios that mirror real-world attack patterns.

**Flexible Synchronization**
   Barrier, countdown latch, and semaphore patterns for different attack scenarios, giving researchers precise control over thread coordination.

**Production-Grade Analysis**
   Automatic race window calculation, vulnerability detection, and detailed statistics to help identify and validate vulnerabilities.

**Extensible Design**
   Plugin-based architecture for extractors and connection strategies, making it easy to adapt TRECO to new testing scenarios.

----

Key Features
------------

Core Capabilities
~~~~~~~~~~~~~~~~~

⚡ **Precision Timing**
   Sub-microsecond race window (< 1μs with Python 3.14t, ~10μs with Python 3.10+) through pre-connection and barrier synchronization

🔓 **GIL-Free Option**
   Python 3.14t free-threaded build for true parallel execution without GIL contention. Compatible with Python 3.10+ for broader accessibility.

🔄 **Multiple Sync Mechanisms**
   Barrier, countdown latch, and semaphore patterns for different attack scenarios and timing requirements

🌐 **Full HTTP/HTTPS Support**
   Complete HTTP/1.1 implementation with configurable TLS/SSL settings and certificate validation options

🎨 **Powerful Template Engine**
   Jinja2-based with custom filters for TOTP, hashing (MD5, SHA1, SHA256), environment variables, and CLI arguments

📊 **Automatic Analysis**
   Race window calculation, vulnerability detection, timing statistics, and success rate reporting

🔌 **Extensible Architecture**
   Plugin-based extractors (regex, JSONPath, XPath, boundary, header, cookie) and custom connection strategies

Advanced Features
~~~~~~~~~~~~~~~~~

**State Machine Engine**

* Multi-state attack flows with conditional transitions
* Context preservation and variable sharing across states
* Sequential and parallel execution modes
* Thread propagation strategies (single/parallel)

**Data Extraction**

* JSONPath for JSON responses
* XPath for XML/HTML responses
* Regular expressions for custom patterns
* Boundary extraction for delimiter-based data
* Header extraction from HTTP response headers
* Cookie extraction from Set-Cookie headers

**Request Templates**

* Dynamic HTTP request generation with Jinja2
* Variable interpolation and substitution
* Custom filters (totp, md5, sha1, sha256, env, argv, average)
* Multi-line support with YAML pipe syntax
* Conditional logic and loops

**Logging & Reporting**

* Per-state and per-thread logging
* Detailed timing statistics (min, max, avg, race window)
* Race window quality assessment
* Vulnerability assessment and recommendations

**Thread Management**

* Configurable thread count (1-1000)
* Thread propagation strategies
* Thread-safe state management
* Automatic resource cleanup

----

Common Vulnerabilities Tested
------------------------------

TRECO is designed to identify and exploit these common race condition vulnerabilities:

💰 **Double-Spending Attacks**
   Process the same payment or transaction multiple times due to race conditions in payment processing systems.

🎁 **Fund Redemption Exploits**
   Redeem gift cards, coupons, or promotional codes beyond their intended limit by exploiting concurrent redemption logic.

📦 **Inventory Manipulation**
   Purchase limited stock items beyond available quantity by racing inventory check and purchase operations.

🔐 **Privilege Escalation**
   Gain unauthorized access or elevated privileges through race conditions in authentication and authorization systems.

⚡ **Rate Limiting Bypasses**
   Exceed API quotas and rate limits by exploiting race conditions in rate limiting implementations.

🎟️ **Voucher Abuse**
   Reuse single-use vouchers or discount codes multiple times through concurrent usage.

🏦 **TOCTOU Vulnerabilities**
   Exploit Time-of-Check to Time-of-Use vulnerabilities in financial transactions, resource allocation, and access control.

----

Quick Example
-------------

Here's a simple example of a race condition test for a fund redemption vulnerability:

.. code-block:: yaml

   metadata:
     name: "Fund Redemption Race Condition"
     version: "1.0"
     vulnerability: "CWE-362"

   target:
     host: "api.example.com"
     port: 443
     tls:
       enabled: true

   entrypoint:
     state: login
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
         Authorization: Bearer {{ login.token }}
         Content-Type: application/json
         
         {"amount": 100}
       
       race:
         threads: 20
         sync_mechanism: barrier
         connection_strategy: preconnect
       
       next:
         - on_status: 200
           goto: end

     end:
       description: "Attack complete"

**Run the test:**

.. code-block:: bash

   treco attack.yaml

**Expected output:**

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
     ✓ EXCELLENT race window (< 10ms)

   Vulnerability Assessment:
     ⚠️ VULNERABLE: Multiple requests succeeded (18)
     ⚠️ Potential race condition detected!
   ======================================================================

----

Why Python 3.14t?
-----------------

Python 3.14t is the **free-threaded** build that removes the Global Interpreter Lock (GIL):

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Feature
     - Python 3.10-3.13 (GIL)
     - Python 3.14t (GIL-Free)
   * - **True Parallelism**
     - Single thread at a time
     - Multiple threads simultaneously
   * - **Race Window Timing**
     - ~10-100μs
     - **< 1μs** (sub-microsecond)
   * - **CPU Utilization**
     - Limited by GIL
     - Full multi-core usage
   * - **Consistency**
     - Variable timing
     - Highly consistent
   * - **Best for TRECO**
     - Good
     - **Excellent**

.. note::
   TRECO works with both Python 3.10+ and 3.14t, but achieves optimal performance with 3.14t's free-threaded build.

----

Real-World Applications
-----------------------

TRECO is designed for authorized security testing in various scenarios:

Security Testing
~~~~~~~~~~~~~~~~

* **Penetration Testing**: Test web APIs for race condition vulnerabilities
* **Bug Bounty Hunting**: Identify exploitable race conditions in e-commerce, financial, and gaming platforms
* **Security Assessments**: Validate security controls under concurrent load
* **Vulnerability Research**: Systematic discovery and analysis of race condition patterns

Common Attack Patterns
~~~~~~~~~~~~~~~~~~~~~~~

**Double-Spending Attacks**
   Test payment processing systems for concurrent transaction vulnerabilities. Example: Process the same payment token multiple times.

**Fund Redemption Exploits**
   Test gift card and coupon systems for redemption race conditions. Example: Redeem a gift card balance multiple times concurrently.

**Inventory Manipulation**
   Test e-commerce platforms for inventory race conditions. Example: Purchase limited stock items beyond available quantity.

**Privilege Escalation**
   Test authentication systems for concurrent access vulnerabilities. Example: Race authentication and authorization checks.

**Rate Limiting Bypasses**
   Test API rate limiting implementations for concurrent request vulnerabilities. Example: Exceed API quotas through simultaneous requests.

Quality Assurance
~~~~~~~~~~~~~~~~~

* **Concurrency Testing**: Validate thread-safe implementations
* **Load Testing**: Verify system behavior under concurrent load
* **Stress Testing**: Identify breaking points and resource limits
* **Integration Testing**: Test multi-component interactions under race conditions

----

Architecture Highlights
-----------------------

Component Overview
~~~~~~~~~~~~~~~~~~

**State Machine Engine**
   Orchestrates complex attack flows through sequential states with conditional transitions. Manages context and variables across states.

**Race Coordinator**
   Synchronizes threads using barrier, latch, or semaphore patterns. Coordinates simultaneous request dispatch for optimal race window timing.

**HTTP Client**
   Built on httpx for robust HTTP/HTTPS communication. Implements multiple connection strategies (preconnect, lazy, pooled, multiplexed).

**Template Engine**
   Jinja2-based request rendering with custom filters for TOTP generation, hashing, environment variables, and CLI arguments.

**Data Extractors**
   Plugin-based architecture supporting JSONPath, XPath, Regex, Boundary, Header, and Cookie extractors with auto-discovery.

**Metrics System**
   Collects detailed timing statistics, calculates race windows, assesses vulnerability likelihood, and generates comprehensive reports.

Execution Flow
~~~~~~~~~~~~~~

1. **Configuration Loading**: Parse YAML attack definition and validate structure
2. **State Initialization**: Set up initial state with variables from entrypoint
3. **State Execution**: Execute states sequentially according to transition rules
4. **Race Coordination**: Synchronize threads for race attacks using selected mechanism
5. **Request Dispatch**: Send HTTP requests simultaneously for optimal timing
6. **Response Processing**: Extract data from responses using configured extractors
7. **Transition Logic**: Determine next state based on conditions and response data
8. **Reporting**: Generate detailed attack report with timing analysis and assessment

----

Learn More
----------

Ready to dive deeper? Here are the next steps:

**Getting Started**

* :doc:`about` - Complete overview of TRECO's capabilities and design philosophy
* :doc:`installation` - Detailed installation guide for all platforms
* :doc:`quickstart` - Your first race condition test in 5 minutes

**User Guide**

* :doc:`configuration` - Complete YAML configuration reference with all options
* :doc:`synchronization` - Understanding synchronization mechanisms in depth
* :doc:`connection-strategies` - Choosing the right connection strategy
* :doc:`extractors` - All available data extractors and usage examples
* :doc:`templates` - Template syntax, filters, and advanced techniques
* :doc:`examples` - Real-world attack examples and patterns

**Reference**

* :doc:`cli` - Command-line interface reference and usage
* :doc:`api` - Python API documentation for programmatic use
* :doc:`troubleshooting` - Common issues and solutions
* :doc:`best-practices` - Performance optimization and security guidelines

----

Support the Project
-------------------

If you find TRECO useful for your security research, please consider supporting its development:

.. raw:: html

   <div align="center" style="margin: 2em 0;">
   <a href="https://buymeacoffee.com/maycon" target="_blank">
     <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" 
          alt="Buy Me A Coffee" 
          style="height: 60px !important;width: 217px !important;">
   </a>
   <br><br>
   <a href="https://github.com/sponsors/maycon" target="_blank">
     <img src="https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?style=for-the-badge&logo=github&logoColor=white" 
          alt="GitHub Sponsor">
   </a>
   </div>

Your support helps maintain and improve TRECO for the security research community.

----

Getting Help
------------

Need assistance? Here's how to get help:

**Documentation**
   * Complete documentation at `Read the Docs <https://treco.readthedocs.io>`_
   * Search for specific topics using the search box
   * Review code examples and tutorials

**Community**
   * `GitHub Issues <https://github.com/maycon/TRECO/issues>`_ for bug reports
   * `GitHub Discussions <https://github.com/maycon/TRECO/discussions>`_ for questions
   * Check existing issues before creating new ones

**Before Asking**
   1. Check this documentation
   2. Search existing issues and discussions
   3. Review :doc:`troubleshooting` guide
   4. Try :doc:`examples` for working configurations

----

Security Notice
---------------

.. warning::

   **TRECO is designed for authorized security testing only.**
   
   ⚠️ **You MUST:**
   
   * Obtain written authorization before testing
   * Test only within agreed scope and boundaries
   * Comply with all applicable laws and regulations
   * Report vulnerabilities responsibly
   * Allow reasonable time for remediation
   
   ⚠️ **Unauthorized testing may result in:**
   
   * Criminal prosecution under computer fraud laws
   * Civil liability for damages
   * Loss of security credentials and reputation
   * Harm to individuals and organizations
   
   **Users are solely responsible** for ensuring their use complies with applicable laws, regulations, and agreements. The developers are not responsible for any misuse of this tool.

----

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

----

.. raw:: html

   <div align="center" style="margin-top: 2em; padding: 1em; border-top: 2px solid #ccc;">
   <p><strong>⚠️ USE RESPONSIBLY - AUTHORIZED TESTING ONLY ⚠️</strong></p>
   <p>Made with ❤️ by security researchers, for security researchers</p>
   <p>
   <a href="https://github.com/maycon/TRECO">⭐ Star on GitHub</a> |
   <a href="https://treco.readthedocs.io">📖 Documentation</a> |
   <a href="https://github.com/maycon/TRECO/issues">🐛 Report Bug</a> |
   <a href="https://github.com/maycon/TRECO/issues">💡 Request Feature</a>
   </p>
   </div>