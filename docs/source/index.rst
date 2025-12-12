TRECO Documentation
===================

.. image:: ../../static/treco.png
   :alt: TRECO Logo
   :align: center
   :width: 200px

**Tactical Race Exploitation & Concurrency Orchestrator**

A specialized framework for identifying and exploiting race condition vulnerabilities in HTTP APIs.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   about
   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   configuration
   extractors
   templates
   examples

.. toctree::
   :maxdepth: 2
   :caption: Reference

   cli
   api

Overview
--------

TRECO enables security researchers to orchestrate highly precise concurrent HTTP attacks with sub-microsecond timing accuracy, making it possible to reliably trigger race conditions in web applications.

**What makes TRECO unique:**

* **Sub-microsecond precision**: Race windows consistently below 1μs through pre-connection and barrier synchronization
* **True parallelism**: Python 3.14t free-threaded build eliminates GIL constraints for genuine concurrent execution
* **State machine architecture**: Complex multi-state attack flows with conditional transitions
* **Flexible synchronization**: Barrier, countdown latch, and semaphore patterns for different scenarios
* **Production-grade analysis**: Automatic race window calculation, vulnerability detection, and detailed statistics

Key Features
------------

* ⚡ **Precision Timing**: Sub-microsecond race window (< 1μs)
* 🔓 **GIL-Free**: Python 3.14t free-threaded build for true parallel execution
* 🔄 **Flexible Sync**: Barrier, countdown latch, and semaphore mechanisms
* 🌐 **HTTP/HTTPS**: Full HTTP/1.1 support with TLS configuration
* 🎨 **Template Engine**: Jinja2-based with custom filters (TOTP, hashing, env vars)
* 📊 **Analysis**: Automatic race window calculation and vulnerability detection
* 🔌 **Extensible**: Plugin-based extractors and connection strategies

Common Vulnerabilities Tested
------------------------------

* Double-spending attacks (payment processing)
* Fund redemption exploits (financial applications)
* Inventory manipulation (e-commerce)
* Privilege escalation (authentication systems)
* Rate limiting bypasses

Quick Example
-------------

.. code-block:: yaml

   metadata:
     name: "Race Condition Test"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-362"

   config:
     host: "api.example.com"
     port: 443
     tls:
       enabled: true

   states:
     login:
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
       request: |
         POST /api/redeem HTTP/1.1
         Authorization: Bearer {{ login.token }}
         
         {"amount": 100}
       
       race:
         threads: 20
         sync_mechanism: barrier
         connection_strategy: preconnect
       
       next:
         - on_status: 200
           goto: end

Why Python 3.14t?
-----------------

Python 3.14t is the **free-threaded** build that removes the Global Interpreter Lock (GIL):

* **True Parallelism**: Multiple threads execute simultaneously without GIL contention
* **Better Timing**: More consistent and precise race window timing
* **Improved Performance**: Better CPU utilization for multi-threaded workloads
* **Perfect for TRECO**: Race condition testing benefits significantly from true parallelism

Read more: :doc:`about`

Real-World Applications
-----------------------

TRECO is designed for:

**Security Testing**

* Penetration testing of web APIs
* Bug bounty hunting on e-commerce platforms
* Security assessments of financial applications
* Vulnerability research and proof-of-concept development

**Common Vulnerability Patterns**

* **Double-spending attacks**: Payment processing race conditions
* **Fund redemption exploits**: Gift card and coupon abuse
* **Inventory manipulation**: Purchasing limited items beyond stock
* **Privilege escalation**: Authentication and authorization bypasses
* **Rate limiting bypasses**: Exceeding API quotas

**Quality Assurance**

* Concurrency testing for multi-threaded applications
* Load testing under realistic concurrent scenarios
* Stress testing to identify system breaking points
* Integration testing with race condition scenarios

Architecture Highlights
-----------------------

**State Machine Engine**

TRECO uses a YAML-based state machine to orchestrate complex attack flows:

* Sequential state transitions with conditional logic
* Context preservation and variable sharing across states
* Multi-state attack patterns for sophisticated scenarios
* Flexible transition rules based on HTTP status and response content

**Race Coordinator**

Precise thread synchronization for reliable race condition triggering:

* Barrier synchronization for simultaneous request dispatch
* Pre-connection strategy to eliminate network latency
* Thread-safe result aggregation and analysis
* Sub-microsecond timing measurements

**Template Engine**

Dynamic HTTP request generation with Jinja2:

* Variable interpolation and conditional logic
* Custom filters for TOTP, hashing, and environment variables
* Support for complex request bodies and headers
* Multi-line YAML support for readability

**Data Extractors**

Plugin-based response parsing:

* JSONPath for JSON responses
* XPath for XML/HTML responses
* Regex for custom patterns
* Boundary for delimiter-based extraction
* Header and Cookie extractors

Learn More
----------

* :doc:`about` - Complete overview of TRECO's capabilities and architecture
* :doc:`installation` - Step-by-step installation guide
* :doc:`quickstart` - Your first race condition test in 5 minutes
* :doc:`configuration` - Complete YAML configuration reference
* :doc:`extractors` - All available data extractors
* :doc:`templates` - Template syntax and filters
* :doc:`examples` - Real-world attack examples

Getting Help
------------

* **GitHub Issues**: https://github.com/maycon/TRECO/issues
* **Documentation**: https://treco.readthedocs.io
* **Repository**: https://github.com/maycon/TRECO

Security Notice
---------------

.. warning::

   TRECO is designed for **authorized security testing only**.
   
   * Obtain written authorization before testing
   * Test only within agreed scope
   * Comply with applicable laws
   * Report vulnerabilities responsibly
   
   Users are solely responsible for ensuring compliance with applicable laws and regulations.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
