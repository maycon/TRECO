# TRECO

<div align="center">
<img src="static/treco.png" alt="TRECO Logo" width="220" />

**T**actical **R**ace **E**xploitation & **C**oncurrency **O**rchestrator

*A specialized framework for identifying and exploiting race condition vulnerabilities in HTTP APIs with sub-microsecond precision.*

[![Python 3.14t](https://img.shields.io/badge/python-3.14t-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Free-Threaded](https://img.shields.io/badge/GIL-Free-green.svg)](https://peps.python.org/pep-0703/)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue.svg)](https://treco.readthedocs.io)

[Documentation](https://treco.readthedocs.io) | [PyPI Package](https://pypi.org/project/treco-framework/) | [Installation](#installation) | [Quick Start](#quick-start) | [Examples](#examples)

</div>

---

## 🎯 Overview

TRECO enables security researchers to orchestrate highly precise concurrent HTTP attacks with **sub-microsecond timing accuracy**, making it possible to reliably trigger race conditions in web applications. Built for both Python 3.10+ (with GIL) and Python 3.14t (GIL-free), TRECO achieves unprecedented timing precision for race condition exploitation.

### Common Vulnerabilities Tested

- 💰 **Double-spending attacks** (payment processing)
- 🎁 **Fund redemption exploits** (financial applications, gift cards, coupons)
- 📦 **Inventory manipulation** (e-commerce, limited stock bypasses)
- 🔐 **Privilege escalation** (authentication and authorization systems)
- ⚡ **Rate limiting bypasses** (API quota exhaustion)
- 🎟️ **Voucher abuse** (single-use code reuse)
- 🏦 **TOCTOU vulnerabilities** (Time-of-Check to Time-of-Use)

---

## ✨ Key Features

### Core Capabilities

- **⚡ Precision Timing**: Sub-microsecond race window (< 1μs) with barrier synchronization
- **🔓 GIL-Free Option**: Python 3.14t free-threaded build for true parallel execution
- **🔄 Flexible Synchronization**: Barrier, countdown latch, and semaphore mechanisms
- **🌐 Full HTTP/HTTPS Support**: Complete HTTP/1.1 with configurable TLS/SSL
- **🎨 Powerful Template Engine**: Jinja2-based with custom filters (TOTP, hashing, env vars, CLI args)
- **📊 Automatic Analysis**: Race window calculation, vulnerability detection, and detailed statistics
- **🔌 Extensible Architecture**: Plugin-based extractors and connection strategies
- **🖥️ Multi-Platform**: Linux, macOS, and Windows (WSL recommended)
- **✅ JSON Schema Validation**: Catch configuration errors early with IDE integration and real-time validation

### Advanced Features

TRECO also provides additional advanced features for specialized testing scenarios:

- **🔀 Multi-Condition When Blocks**: Complex state transitions with boolean expressions, body matching, and header checks
- **🌐 Proxy Support**: HTTP, HTTPS, and SOCKS5 proxies with authentication
- **🚀 HTTP/2 Support**: Testing with HTTP/2 protocol via multiplexed strategy
- **🔄 Connection Reuse**: Control over TCP connection reuse behavior
- **↪️ Redirect Handling**: Configurable HTTP redirect following
- **⏱️ Timeout Configuration**: Global and per-state timeout control

📖 **See [docs/WHEN_BLOCKS.md](docs/WHEN_BLOCKS.md) for multi-condition when blocks documentation:**
- Status code matching (exact, range, multiple)
- Jinja2 expression evaluation
- Body content matching (contains, regex, equals)
- Header checks (exists, equals, contains, numeric comparison)
- Response time analysis
- Complete examples and best practices

📖 **See [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) for complete documentation on:**
- Proxy configuration and use cases
- HTTP/2 setup and limitations
- Connection reuse strategies
- All 7 available extractors (JSONPath, XPath, Regex, Boundary, Header, Cookie, etc.)
- All 7 template filters (TOTP, MD5, SHA1, SHA256, env, argv, average)
- Performance considerations
- Troubleshooting advanced features

📖 **See [docs/SCHEMA_VALIDATION.md](docs/SCHEMA_VALIDATION.md) for JSON Schema validation:**
- IDE setup instructions (VSCode, PyCharm)
- Pre-commit hook configuration
- CI/CD integration examples
- Common validation errors and fixes

---

## 🚀 Why Python 3.14t?

Python 3.14t is the **free-threaded** build that removes the Global Interpreter Lock (GIL):

| Feature | Python 3.10-3.13 (GIL) | Python 3.14t (GIL-Free) |
|---------|------------------------|-------------------------|
| **True Parallelism** | ❌ Single thread at a time | ✅ Multiple threads simultaneously |
| **Race Window Timing** | ~10-100μs | **< 1μs** (sub-microsecond) |
| **CPU Utilization** | Limited by GIL | Full multi-core usage |
| **Consistency** | Variable timing | Highly consistent |
| **Best for TRECO** | Good | **Excellent** |

> **Note**: TRECO works with both Python 3.10+ and 3.14t, but achieves optimal performance with 3.14t's free-threaded build.

---

## 📦 Installation

### Prerequisites

- **Python 3.10+** or **Python 3.14t** (free-threaded build recommended)
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package installer (recommended)

### Option 1: Install from PyPI (Recommended)

TRECO is available on PyPI as `treco-framework`:

```bash
# Install with pip
pip install treco-framework

# Or install with uv (faster)
uv pip install treco-framework

# Verify installation
treco --version
```

### Option 2: Install from PyPI with uv (Virtual Environment)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project directory
mkdir my-treco-tests
cd my-treco-tests

# Initialize with uv
uv init
uv add treco-framework

# Run TRECO
uv run treco --version
```

### Option 3: Install from Source with uv

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/maycon/TRECO.git
cd TRECO

# Install with uv (automatically creates virtual environment)
uv sync

# Optional: Install with development dependencies
uv sync --all-extras
```

### Option 4: Install from Source with pip

```bash
# Clone repository
git clone https://github.com/maycon/TRECO.git
cd TRECO

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e .

# Optional: Install with development dependencies
pip install -e ".[dev]"
```

### Python 3.14t Installation (Optional, for Best Performance)

For optimal race condition timing with GIL-free execution:

```bash
# Install Python 3.14t with uv
uv python install 3.14t

# Verify installation
uv run python --version
# Should show: Python 3.14.0t (or later)

# Install TRECO with Python 3.14t
uv pip install treco-framework --python 3.14t
```

### Verify Installation

```bash
# Check TRECO version
treco --version

# Check Python version
python --version

# Test with a simple command
treco --help
```

### Quick Test

Create a simple test file `test.yaml`:

```yaml
metadata:
  name: "Installation Test"
  version: "1.0"

config:
  host: "httpbin.org"
  port: 443
  tls:
    enabled: true

entrypoint:
  state: test
  input: {}

states:
  test:
    description: "Test installation"
    request: |
      GET /get HTTP/1.1
      Host: {{ config.host }}
    
    next:
      - on_status: 200
        goto: end
  
  end:
    description: "Success"
```

Run the test:

```bash
treco test.yaml
```

If you see successful output, TRECO is installed correctly!

### Validate Configuration

Before running attacks, you can validate your configuration files:

```bash
# Validate configuration without executing
treco --validate-only attack.yaml
```

This will check for:
- ✅ Valid YAML syntax
- ✅ Required fields present
- ✅ Correct data types
- ✅ Valid enum values (sync mechanisms, connection strategies, etc.)
- ✅ State references are valid
- ✅ Extractor patterns are correct

See [docs/SCHEMA_VALIDATION.md](docs/SCHEMA_VALIDATION.md) for IDE setup and advanced validation features.

---

## 🏁 Quick Start

### 1. Create Your First Attack Configuration

Create a file named `attack.yaml`:

```yaml
metadata:
  name: "Fund Redemption Race Condition"
  version: "1.0"
  author: "Security Researcher"
  vulnerability: "CWE-362"

config:
  host: "api.example.com"
  port: 443
  tls:
    enabled: true
    verify_cert: true

entrypoint:
  state: login
  input:
    username: "testuser"
    password: "testpass"

states:
  login:
    description: "Authenticate and obtain access token"
    request: |
      POST /api/login HTTP/1.1
      Host: {{ config.host }}
      Content-Type: application/json
      
      {"username": "{{ username }}", "password": "{{ password }}"}
    
    extract:
      token:
        type: jpath
        pattern: "$.access_token"
      balance:
        type: jpath
        pattern: "$.user.balance"
    
    logger:
      on_state_leave: |
        ✓ Authenticated as {{ username }}
        Initial balance: ${{ balance }}
    
    next:
      - on_status: 200
        goto: race_attack
      - on_status: 401
        goto: end

  race_attack:
    description: "Concurrent fund redemption attack"
    request: |
      POST /api/redeem HTTP/1.1
      Host: {{ config.host }}
      Authorization: Bearer {{ login.token }}
      Content-Type: application/json
      
      {"amount": 100, "code": "GIFT100"}
    
    race:
      threads: 20
      sync_mechanism: barrier
      connection_strategy: preconnect
      thread_propagation: single
    
    extract:
      final_balance:
        type: jpath
        pattern: "$.balance"
    
    logger:
      on_state_leave: |
        {% if final_balance > balance %}
        ⚠️  VULNERABLE: Balance increased from ${{ balance }} to ${{ final_balance }}
        ⚠️  Successfully exploited race condition!
        {% else %}
        ✓ No vulnerability detected (balance unchanged)
        {% endif %}
    
    next:
      - on_status: 200
        goto: end

  end:
    description: "Attack completed"
```

### 2. Run the Attack

```bash
# Using uv run
uv run treco attack.yaml

# Or activate the environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
treco attack.yaml

# With custom parameters
treco attack.yaml --user alice --password secret123 --threads 30

# Verbose output for debugging
treco attack.yaml --verbose
```

### 3. Analyze Results

```
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
Successful: 18
Failed: 2

Timing Analysis:
  Average response time: 46.5ms
  Fastest response: 45.2ms
  Slowest response: 48.7ms
  Race window: 3.5ms
  
  ✓ EXCELLENT race window (< 10ms)

Vulnerability Assessment:
  ⚠️  VULNERABLE: Multiple requests succeeded (18)
  ⚠️  Potential race condition detected!
  ⚠️  Balance increased from $1000 to $2800
======================================================================
```

**Race Window Quality Assessment:**
- **< 1ms**: 🟢 Excellent (true race condition, sub-microsecond precision)
- **1-10ms**: 🟢 Very Good (sufficient for most race conditions)
- **10-100ms**: 🟡 Good (adequate for many scenarios)
- **> 100ms**: 🔴 Poor (timing too imprecise, likely false negatives)

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────┐
│   YAML Config   │
│   (attack.yaml) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Configuration  │──────│   State Machine  │
│     Parser      │      │      Engine      │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Template Engine  │
                         │    (Jinja2)      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      Race        │
                         │   Coordinator    │
                         └────────┬─────────┘
                                  │
          ┌───────────────────────┼─────────────────────┐
          │                       │                     │
          ▼                       ▼                     ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Connection      │   │  Synchronization │   │   HTTP Client    │
│   Strategy       │   │   Mechanism      │   │   (httpx)        │
└──────────────────┘   └──────────────────┘   └──────────────────┘
    │                         │                         │
    │                         ▼                         │
    │                  ┌─────────────┐                  │
    │                  │   Barrier   │                  │
    │                  │    Sync     │                  │
    │                  └──────┬──────┘                  │
    │                         │                         │
    └─────────────────────────┼─────────────────────────┘
                              │
                              ▼
                  [Concurrent HTTP Requests]
                              │
                              ▼
                      ┌──────────────┐
                      │   Target     │
                      │   Server     │
                      └──────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  Response Processing  │
                  │   Data Extraction     │
                  │  Metrics Collection   │
                  └───────────────────────┘
```

### Core Components

#### 1. State Machine Engine
- Orchestrates multi-state attack flows
- Manages state transitions with conditional logic
- Preserves context and variables across states
- Supports sequential and parallel execution

#### 2. Race Coordinator
- Manages thread synchronization and lifecycle
- Implements barrier, latch, and semaphore patterns
- Coordinates simultaneous request dispatch
- Collects and aggregates results with timing metrics

#### 3. Template Engine
- Jinja2-based request rendering
- Custom filters: `totp()`, `md5`, `sha256`, `env()`, `argv()`, `average`
- Dynamic variable substitution
- Support for conditionals and loops

#### 4. HTTP Client
- Built on httpx for robust HTTP/HTTPS communication
- Configurable connection strategies (preconnect, lazy, pooled, multiplexed)
- TLS/SSL configuration with certificate validation
- Connection pooling and reuse management

#### 5. Data Extractors
- **JSONPath**: Extract from JSON responses
- **XPath**: Extract from XML/HTML responses
- **Regex**: Pattern-based extraction
- **Boundary**: Delimiter-based extraction
- **Header**: HTTP header extraction
- **Cookie**: Cookie value extraction

#### 6. Synchronization Mechanisms
- **Barrier**: All threads wait and release simultaneously (best for races)
- **Countdown Latch**: Threads count down to zero, then all proceed
- **Semaphore**: Control concurrent execution with permits

---

## 📚 Configuration Reference

### YAML Structure

```yaml
metadata:
  name: string              # Attack name
  version: string           # Version (e.g., "1.0")
  author: string            # Author name (optional)
  vulnerability: string     # CVE/CWE ID (optional)
  description: string       # Attack description (optional)

config:
  host: string              # Target host (required)
  port: integer             # Target port (default: 80/443)
  threads: integer          # Default thread count (optional)
  timeout: integer          # Request timeout in seconds (default: 30)
  reuse_connection: bool    # Reuse TCP connections (default: false)
  tls:
    enabled: bool           # Use HTTPS (default: false)
    verify_cert: bool       # Verify SSL certificates (default: true)
    cert_path: string       # Custom CA cert path (optional)
  http:
    follow_redirects: bool  # Follow HTTP redirects (default: true)
  proxy:                    # Optional proxy configuration
    host: string            # Proxy hostname or IP
    port: integer           # Proxy port
    type: string            # Proxy type: http, https, socks5 (default: http)
    auth:                   # Optional proxy authentication
      username: string      # Proxy username
      password: string      # Proxy password

entrypoint:
  state: string           # Starting state name
  input:                  # Initial variables (key-value pairs)
    key: value

states:
  state_name:
    description: string     # State description
    request: string         # HTTP request template (multiline)
    
    extract:                # Response data extraction (optional)
      variable_name:
        type: jpath|xpath|regex|boundary|header|cookie
        pattern: string
        default: any        # Default value if extraction fails
    
    race:                   # Race configuration (optional)
      threads: integer      # Number of threads
      sync_mechanism: barrier|countdown_latch|semaphore
      connection_strategy: preconnect|lazy|pooled|multiplexed
      thread_propagation: single|parallel
      permits: integer      # For semaphore only
    
    logger:                 # Logging configuration (optional)
      on_state_enter: string
      on_state_leave: string
      on_thread_enter: string
      on_thread_leave: string
    
    next:                   # State transitions (required)
      - on_status: integer|list[integer]
        goto: string
        delay_ms: integer   # Optional delay before transition
      - on_extract: dict    # Conditional based on extracted values
        goto: string
```

### Synchronization Mechanisms Explained

#### Barrier (Recommended for Race Conditions)
All threads wait at the barrier until the last thread arrives, then all are released simultaneously.

```yaml
race:
  threads: 20
  sync_mechanism: barrier
  connection_strategy: preconnect  # Pre-establish connections
```

**Best for:** True race conditions, double-spending, inventory manipulation

**Timing precision:** < 1μs with Python 3.14t, ~10μs with Python 3.10+

#### Countdown Latch
Threads count down a counter; when it reaches zero, all waiting threads are released.

```yaml
race:
  threads: 20
  sync_mechanism: countdown_latch
```

**Best for:** Coordinated attacks where threads need to signal readiness

**Timing precision:** Similar to barrier

#### Semaphore
Controls the number of threads that can execute concurrently using permits.

```yaml
race:
  threads: 50
  sync_mechanism: semaphore
  permits: 10  # Max 10 threads execute at once
```

**Best for:** Rate limiting tests, controlled concurrency

**Timing precision:** Lower precision, not ideal for race conditions

### Connection Strategies

#### Preconnect (Recommended)
Establishes TCP/TLS connections before reaching the synchronization point.

```yaml
race:
  connection_strategy: preconnect
```

**Advantages:**
- Eliminates connection overhead from race window
- Achieves sub-microsecond timing precision
- Highest success rate for race conditions

**Use when:** Testing race conditions (recommended for all race tests)

#### Lazy
Connects on-demand when sending the request.

```yaml
race:
  connection_strategy: lazy
```

**Advantages:**
- Simpler implementation
- Lower resource usage

**Disadvantages:**
- Higher latency
- Poor timing precision
- Lower success rate

**Use when:** Testing scenarios where connection timing matters

#### Pooled
Shares a connection pool across threads.

```yaml
race:
  connection_strategy: pooled
```

**Advantages:**
- Resource efficient
- Connection reuse

**Disadvantages:**
- Serializes requests
- Not suitable for race conditions

**Use when:** Sequential testing, connection reuse testing

#### Multiplexed
HTTP/2 multiplexing over a single connection.

```yaml
race:
  connection_strategy: multiplexed
```

**Advantages:**
- Single TCP connection
- HTTP/2 features

**Disadvantages:**
- Requires HTTP/2 support
- Complex setup

**Use when:** Testing HTTP/2-specific race conditions

### Thread Propagation

#### Single (Default)
Only one thread from the race attack continues to the next state.

```yaml
race:
  thread_propagation: single
```

**Use when:** Next state doesn't need race behavior, sequential flow

#### Parallel
All threads continue to the next state in parallel.

```yaml
race:
  thread_propagation: parallel
```

**Use when:** Multi-stage race attacks, cascading exploits

---

## 🎨 Template Syntax

### Variable Interpolation

```yaml
# Access configuration values
{{ config.host }}
{{ config.port }}

# Access variables from previous states
{{ login.token }}
{{ check_balance.current_balance }}

# Access thread information
{{ thread.id }}
{{ thread.name }}

# Access global context
{{ username }}
{{ password }}
```

### Custom Filters

#### TOTP (Time-Based One-Time Password)

```yaml
# Generate TOTP code
{{ totp(secret_seed) }}

# Use in request
request: |
  POST /api/verify HTTP/1.1
  {"code": "{{ totp('JBSWY3DPEHPK3PXP') }}"}
```

#### Hashing Filters

```yaml
# MD5 hash
{{ password | md5 }}

# SHA1 hash
{{ data | sha1 }}

# SHA256 hash
{{ sensitive_data | sha256 }}

# Example usage
request: |
  POST /api/authenticate HTTP/1.1
  {"password_hash": "{{ password | sha256 }}"}
```

#### Environment Variables

```yaml
# Get environment variable
{{ env('API_KEY') }}

# With default value
{{ env('API_KEY', 'default-key') }}

# Example usage
request: |
  GET /api/data HTTP/1.1
  X-API-Key: {{ env('API_KEY') }}
```

#### Command-Line Arguments

```yaml
# Get CLI argument
{{ argv('user') }}

# With default value
{{ argv('user', 'guest') }}

# Example usage
request: |
  POST /api/login HTTP/1.1
  {"username": "{{ argv('user', 'testuser') }}"}
```

#### Average Filter

```yaml
# Calculate average from list
{{ [10, 20, 30, 40] | average }}  # Returns 25

# Use with extracted data
logger:
  on_state_leave: |
    Average response time: {{ response_times | average }}ms
```

### Conditionals and Loops

```yaml
logger:
  on_state_leave: |
    {% if balance > initial_balance %}
      ⚠️  VULNERABLE: Money multiplied!
      Initial: ${{ initial_balance }}
      Final: ${{ balance }}
      Profit: ${{ balance - initial_balance }}
    {% else %}
      ✓ No vulnerability detected
    {% endif %}

# Loops
logger:
  on_state_enter: |
    Testing with users:
    {% for user in users %}
      - {{ user }}
    {% endfor %}
```

---

## 🔍 Data Extraction

### JSONPath Extractor

Extract data from JSON responses using JSONPath expressions.

```yaml
extract:
  # Simple field extraction
  token:
    type: jpath
    pattern: "$.access_token"
  
  # Nested field extraction
  user_id:
    type: jpath
    pattern: "$.user.id"
  
  # Array element extraction
  first_item:
    type: jpath
    pattern: "$.items[0].name"
  
  # Filtered array extraction
  active_users:
    type: jpath
    pattern: "$.users[?(@.active==true)].username"
  
  # With default value
  balance:
    type: jpath
    pattern: "$.account.balance"
    default: 0
```

### XPath Extractor

Extract data from XML/HTML responses using XPath expressions.

```yaml
extract:
  # Extract CSRF token from HTML form
  csrf_token:
    type: xpath
    pattern: '//input[@name="csrf_token"]/@value'
  
  # Extract text content
  title:
    type: xpath
    pattern: '//h1[@class="title"]/text()'
  
  # Extract attribute
  user_id:
    type: xpath
    pattern: '//div[@id="user"]/@data-id'
  
  # Extract from XML
  api_version:
    type: xpath
    pattern: '/response/version/text()'
```

### Regex Extractor

Extract data using regular expressions.

```yaml
extract:
  # Extract session ID
  session_id:
    type: regex
    pattern: "SESSION=([A-Z0-9]+)"
  
  # Extract with groups
  user_info:
    type: regex
    pattern: "User: (\\w+), Role: (\\w+)"
  
  # Extract numbers
  order_id:
    type: regex
    pattern: "Order #(\\d+)"
  
  # Extract email
  email:
    type: regex
    pattern: "([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})"
```

### Boundary Extractor

Extract data between delimiters.

```yaml
extract:
  # Extract between custom delimiters
  content:
    type: boundary
    pattern: "START:END"
  
  # Extract JSON from text
  json_data:
    type: boundary
    pattern: "```json:```"
  
  # Extract HTML tag content
  script_content:
    type: boundary
    pattern: "<script>:</script>"
```

### Header Extractor

Extract values from HTTP response headers.

```yaml
extract:
  # Extract specific header
  rate_limit:
    type: header
    pattern: "X-RateLimit-Remaining"
  
  # Extract with case-insensitive matching
  content_type:
    type: header
    pattern: "content-type"
  
  # Extract custom header
  request_id:
    type: header
    pattern: "X-Request-ID"
```

### Cookie Extractor

Extract cookie values from Set-Cookie headers.

```yaml
extract:
  # Extract session cookie
  session:
    type: cookie
    pattern: "session"
  
  # Extract with path and domain
  auth_token:
    type: cookie
    pattern: "auth_token"
  
  # Extract tracking cookie
  tracking_id:
    type: cookie
    pattern: "_ga"
```

---

## 💡 Examples

### Example 1: Double-Spending Attack

Test payment processing for race conditions where the same payment token can be used multiple times.

```yaml
metadata:
  name: "Double-Spending Attack"
  version: "1.0"
  vulnerability: "CWE-362"

config:
  host: "payment.example.com"
  port: 443
  tls:
    enabled: true

entrypoint:
  state: get_token
  input:
    card_number: "4111111111111111"
    amount: 1000

states:
  get_token:
    description: "Generate payment token"
    request: |
      POST /api/payment/tokenize HTTP/1.1
      Host: {{ config.host }}
      Content-Type: application/json
      
      {
        "card": "{{ card_number }}",
        "amount": {{ amount }}
      }
    
    extract:
      payment_token:
        type: jpath
        pattern: "$.token"
    
    next:
      - on_status: 200
        goto: race_payment

  race_payment:
    description: "Process payment multiple times"
    request: |
      POST /api/payment/process HTTP/1.1
      Host: {{ config.host }}
      Content-Type: application/json
      
      {"token": "{{ get_token.payment_token }}"}
    
    race:
      threads: 5
      sync_mechanism: barrier
      connection_strategy: preconnect
    
    logger:
      on_state_leave: |
        ⚠️  Testing complete: {{ successful_requests }} payments processed
        {% if successful_requests > 1 %}
        🚨 VULNERABLE: Double-spending detected!
        {% endif %}
    
    next:
      - on_status: 200
        goto: end

  end:
    description: "Attack completed"
```

### Example 2: Inventory Race Condition

Test e-commerce inventory management for concurrent purchase vulnerabilities.

```yaml
metadata:
  name: "Inventory Race Condition"
  version: "1.0"
  vulnerability: "CWE-362"

config:
  host: "shop.example.com"
  port: 443
  tls:
    enabled: true

entrypoint:
  state: login
  input:
    username: "{{ argv('user', 'testuser') }}"
    password: "{{ argv('pass', 'testpass') }}"

states:
  login:
    description: "Authenticate user"
    request: |
      POST /api/auth/login HTTP/1.1
      Host: {{ config.host }}
      Content-Type: application/json
      
      {"username": "{{ username }}", "password": "{{ password }}"}
    
    extract:
      token:
        type: jpath
        pattern: "$.access_token"
    
    next:
      - on_status: 200
        goto: check_stock

  check_stock:
    description: "Check item availability"
    request: |
      GET /api/products/LIMITED_ITEM HTTP/1.1
      Host: {{ config.host }}
      Authorization: Bearer {{ login.token }}
    
    extract:
      stock:
        type: jpath
        pattern: "$.stock"
      price:
        type: jpath
        pattern: "$.price"
    
    logger:
      on_state_leave: |
        Item: LIMITED_ITEM
        Stock: {{ stock }} units
        Price: ${{ price }}
    
    next:
      - on_status: 200
        goto: race_purchase

  race_purchase:
    description: "Concurrent purchase attempts"
    request: |
      POST /api/cart/purchase HTTP/1.1
      Host: {{ config.host }}
      Authorization: Bearer {{ login.token }}
      Content-Type: application/json
      
      {"item_id": "LIMITED_ITEM", "quantity": 1}
    
    race:
      threads: 50
      sync_mechanism: barrier
      connection_strategy: preconnect
    
    logger:
      on_state_leave: |
        Original stock: {{ check_stock.stock }}
        Purchase attempts: 50
        Successful purchases: {{ successful_requests }}
        {% if successful_requests > check_stock.stock %}
        🚨 VULNERABLE: Overselling detected!
        Oversold by: {{ successful_requests - check_stock.stock }} units
        {% endif %}
    
    next:
      - on_status: 200
        goto: end

  end:
    description: "Test completed"
```

### Example 3: 2FA Bypass with TOTP

Test two-factor authentication with time-based one-time passwords.

```yaml
metadata:
  name: "2FA Authentication Test"
  version: "1.0"

config:
  host: "secure.example.com"
  port: 443
  tls:
    enabled: true

entrypoint:
  state: login
  input:
    username: "{{ argv('user') }}"
    password: "{{ argv('pass') }}"
    totp_seed: "{{ env('TOTP_SEED') }}"

states:
  login:
    description: "Initial authentication"
    request: |
      POST /api/auth/login HTTP/1.1
      Host: {{ config.host }}
      Content-Type: application/json
      
      {"username": "{{ username }}", "password": "{{ password }}"}
    
    extract:
      temp_token:
        type: jpath
        pattern: "$.temp_token"
    
    next:
      - on_status: 200
        goto: verify_2fa

  verify_2fa:
    description: "Verify TOTP code"
    request: |
      POST /api/auth/verify-2fa HTTP/1.1
      Host: {{ config.host }}
      Authorization: Bearer {{ login.temp_token }}
      Content-Type: application/json
      
      {"code": "{{ totp(totp_seed) }}"}
    
    extract:
      access_token:
        type: jpath
        pattern: "$.access_token"
    
    logger:
      on_state_leave: |
        ✓ 2FA verification successful
        Access token: {{ access_token[:20] }}...
    
    next:
      - on_status: 200
        goto: end

  end:
    description: "Authentication completed"
```

### Example 4: Rate Limiting Bypass

Test API rate limiting with concurrent requests.

```yaml
metadata:
  name: "Rate Limiting Bypass"
  version: "1.0"
  vulnerability: "CWE-770"

config:
  host: "api.example.com"
  port: 443
  tls:
    enabled: true

entrypoint:
  state: authenticate
  input:
    api_key: "{{ env('API_KEY') }}"

states:
  authenticate:
    description: "Get access token"
    request: |
      POST /api/auth HTTP/1.1
      Host: {{ config.host }}
      X-API-Key: {{ api_key }}
    
    extract:
      token:
        type: jpath
        pattern: "$.token"
    
    next:
      - on_status: 200
        goto: race_requests

  race_requests:
    description: "Concurrent API requests"
    request: |
      GET /api/resource HTTP/1.1
      Host: {{ config.host }}
      Authorization: Bearer {{ authenticate.token }}
    
    race:
      threads: 100
      sync_mechanism: barrier
      connection_strategy: preconnect
    
    extract:
      rate_limit:
        type: header
        pattern: "X-RateLimit-Remaining"
    
    logger:
      on_thread_leave: |
        [Thread {{ thread.id }}] Rate limit remaining: {{ rate_limit }}
      on_state_leave: |
        Total requests: 100
        Successful: {{ successful_requests }}
        Failed (rate limited): {{ failed_requests }}
        {% if successful_requests > 10 %}
        🚨 VULNERABLE: Rate limiting bypassed!
        Expected limit: 10 requests
        Actual processed: {{ successful_requests }} requests
        {% endif %}
    
    next:
      - on_status: 200
        goto: end

  end:
    description: "Test completed"
```

---

## 🖥️ CLI Usage

### Basic Commands

```bash
# Run attack with default configuration
treco attack.yaml

# Override credentials
treco attack.yaml --user alice --password secret123

# Override thread count
treco attack.yaml --threads 50

# Override target host and port
treco attack.yaml --host api.staging.com --port 8443

# Enable verbose logging
treco attack.yaml --verbose

# Combine multiple options
treco attack.yaml --user bob --threads 30 --host test.example.com --verbose
```

### Available CLI Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `config_file` | Path to YAML configuration file | `attack.yaml` |
| `--user` | Override username | `--user alice` |
| `--password` | Override password | `--password secret` |
| `--threads` | Override default thread count | `--threads 50` |
| `--host` | Override target host | `--host api.example.com` |
| `--port` | Override target port | `--port 8443` |
| `--verbose` | Enable verbose logging | `--verbose` |
| `--version` | Show version and exit | `--version` |
| `--help` | Show help message | `--help` |

### Environment Variables

TRECO respects the following environment variables:

```bash
# Set API credentials
export API_KEY="your-api-key"
export API_SECRET="your-secret"

# Set TOTP seed for 2FA
export TOTP_SEED="JBSWY3DPEHPK3PXP"

# Set custom configuration path
export TRECO_CONFIG="/path/to/config.yaml"

# Run with environment variables
treco attack.yaml
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Configuration error |
| 2 | Execution error |
| 3 | Network error |
| 4 | Authentication error |

---

## 🔧 Troubleshooting

### Issue: Wrong Python Version

**Problem**: TRECO requires Python 3.10+ but system has an older version.

**Solution**:
```bash
# Check Python version
python --version

# Using uv to install correct Python version
uv python install 3.14t  # For free-threaded build
# or
uv python install 3.12   # For regular build

# Verify installation
uv run python --version
```

### Issue: Poor Race Window (> 100ms)

**Problem**: Race window is too large to reliably trigger race conditions.

**Solutions**:

1. **Use preconnect strategy**:
```yaml
race:
  connection_strategy: preconnect  # Eliminates TCP/TLS overhead
  sync_mechanism: barrier
```

2. **Upgrade to Python 3.14t**:
```bash
uv python install 3.14t
```

3. **Reduce network latency**:
- Test against localhost or local network
- Use VPS close to target server
- Check network connection stability

4. **Optimize thread count**:
```yaml
race:
  threads: 10  # Start low, increase gradually
```

### Issue: Connection Timeouts

**Problem**: Requests timing out, especially with high thread counts.

**Solutions**:

1. **Increase timeout**:
```yaml
config:
  timeout: 60  # Seconds
```

2. **Reduce thread count**:
```yaml
race:
  threads: 10  # Reduce from 50
```

3. **Check network connectivity**:
```bash
ping api.example.com
curl -I https://api.example.com
```

### Issue: SSL Certificate Errors

**Problem**: SSL verification failing for self-signed or invalid certificates.

**Solutions**:

1. **Disable certificate verification** (development only):
```yaml
config:
  tls:
    enabled: true
    verify_cert: false  # Only for testing!
```

2. **Provide custom CA certificate**:
```yaml
config:
  tls:
    enabled: true
    verify_cert: true
    cert_path: "/path/to/ca-bundle.crt"
```

### Issue: Template Rendering Errors

**Problem**: Variables not found or Jinja2 syntax errors.

**Solutions**:

1. **Debug available variables**:
```yaml
logger:
  on_state_enter: |
    Available variables: {{ context.keys() | list }}
```

2. **Check variable names**:
```yaml
# Correct: Use state_name.variable_name
{{ login.token }}

# Incorrect: Missing state prefix
{{ token }}
```

3. **Provide default values**:
```yaml
extract:
  balance:
    type: jpath
    pattern: "$.balance"
    default: 0  # Fallback if extraction fails
```

### Issue: Import Errors

**Problem**: Module not found errors when running TRECO.

**Solution**:
```bash
# Reinstall dependencies
uv sync

# Or with pip
pip install -e .

# Verify installation
treco --version
```

### Issue: Permission Denied

**Problem**: Cannot write to log files or temp directories.

**Solution**:
```bash
# Check directory permissions
ls -la logs/

# Fix permissions
chmod 755 logs/
chmod 644 logs/*.log

# Or run from writable directory
cd ~/treco
treco attack.yaml
```

---

## 📋 Best Practices

### 1. Performance Optimization

#### Use Preconnect for Race Attacks
Always use preconnect strategy to eliminate connection overhead:

```yaml
race:
  connection_strategy: preconnect
  sync_mechanism: barrier
```

#### Tune Thread Count
Start with lower thread counts and increase gradually:

```yaml
race:
  threads: 10  # Start here
  # Increase to 20, then 30, etc. based on results
```

#### Optimize for Python 3.14t
When available, use Python 3.14t for best timing precision:

```bash
uv python install 3.14t
uv sync
```

#### Minimize Network Latency
- Test against localhost or local network when possible
- Use VPS geographically close to target
- Ensure stable network connection

#### Clean Up Resources
Ensure proper cleanup after tests:

```yaml
states:
  cleanup:
    description: "Clean up test data"
    request: |
      DELETE /api/test-data HTTP/1.1
      Authorization: Bearer {{ token }}
```

### 2. Security Testing Guidelines

#### Always Obtain Authorization
- Get written permission before testing
- Define clear scope and boundaries
- Document authorization in attack metadata

```yaml
metadata:
  name: "Authorized Security Test"
  authorization: "Ticket #12345 - Approved by security@example.com"
  scope: "staging.example.com only"
```

#### Use Test Environments
- Prefer staging/test environments
- Avoid production systems when possible
- Use test accounts and data

#### Document Findings
- Capture detailed logs
- Take screenshots of results
- Note exact reproduction steps
- Record timing information

#### Report Responsibly
- Report to appropriate security contact
- Provide clear reproduction steps
- Allow reasonable fix time before disclosure
- Follow coordinated disclosure practices

#### Clean Up After Testing
- Delete test accounts
- Remove test data
- Restore any modified state
- Verify no lasting impact

### 3. Configuration Management

#### Use Environment Variables for Secrets
Never hardcode credentials in YAML files:

```yaml
# Bad
config:
  api_key: "secret-key-here"

# Good
config:
  api_key: "{{ env('API_KEY') }}"
```

#### Separate Development and Production Configs
Maintain separate configuration files:

```
configs/
  dev/
    attack-payment.yaml
    attack-inventory.yaml
  staging/
    attack-payment.yaml
  prod/  # Only with authorization!
    attack-payment.yaml
```

#### Version Control Configuration
- Keep configurations in version control
- Document changes in commit messages
- Use meaningful branch names
- Review configurations before merging

#### Use Descriptive Metadata
Always include complete metadata:

```yaml
metadata:
  name: "Payment Race Condition Test"
  version: "2.1"
  author: "Security Team"
  vulnerability: "CWE-362"
  description: "Tests double-spending in payment processing"
  created: "2025-01-15"
  updated: "2025-01-20"
```

### 4. Logging and Monitoring

#### Use Structured Logging
Provide clear, actionable log messages:

```yaml
logger:
  on_state_leave: |
    State: {{ state.name }}
    Status: {{ status }}
    Duration: {{ duration }}ms
    Variables: {{ extracted_vars | tojson }}
```

#### Monitor Timing Metrics
Track race window quality:

```yaml
logger:
  on_state_leave: |
    Race window: {{ race_window }}ms
    {% if race_window < 1 %}✓ Excellent{% elif race_window < 10 %}✓ Very Good{% elif race_window < 100 %}⚠ Good{% else %}⚠ Poor{% endif %}
```

#### Implement Error Handling
Gracefully handle failures:

```yaml
next:
  - on_status: 200
    goto: success
  - on_status: 401
    goto: handle_auth_error
  - on_status: 500
    goto: handle_server_error
```

### 5. Testing Methodology

#### Start Simple, Iterate
Begin with basic tests and add complexity:

1. Test single request (1 thread)
2. Test small race (2-5 threads)
3. Scale up threads gradually
4. Optimize timing and strategy

#### Baseline Before Racing
Understand normal behavior first:

```yaml
states:
  baseline:
    description: "Test single request"
    request: "{{ request_template }}"
    next:
      - on_status: 200
        goto: race_test

  race_test:
    description: "Test with race condition"
    request: "{{ request_template }}"
    race:
      threads: 20
      sync_mechanism: barrier
```

#### Vary Test Parameters
Test different scenarios:

```yaml
# Test with different thread counts
- threads: 2    # Minimal race
- threads: 10   # Moderate race
- threads: 50   # Aggressive race
- threads: 100  # Stress test
```

#### Validate Results
Don't rely solely on HTTP status codes:

```yaml
extract:
  balance:
    type: jpath
    pattern: "$.balance"

logger:
  on_state_leave: |
    {% if balance != expected_balance %}
    ⚠️  VULNERABLE: Balance mismatch detected!
    Expected: ${{ expected_balance }}
    Actual: ${{ balance }}
    {% endif %}
```

---

## ⚖️ Security & Legal

### ⚠️ Authorized Testing Only

**TRECO is designed for authorized security testing only.**

### Legal Requirements

Before using TRECO, you MUST:

✅ **Obtain Written Authorization**
- Get explicit permission from system owner
- Define clear scope and boundaries
- Document authorization terms

✅ **Comply with Applicable Laws**
- Computer Fraud and Abuse Act (CFAA) in USA
- Computer Misuse Act in UK
- Local and international cybersecurity laws

✅ **Test Within Agreed Scope**
- Only test authorized systems
- Stay within defined boundaries
- Respect rate limits and resource usage

✅ **Report Responsibly**
- Follow coordinated disclosure practices
- Allow reasonable time for remediation
- Do not publicly disclose before fixes

### Prohibited Uses

❌ **Never Use TRECO For:**
- Unauthorized testing of systems you don't own
- Testing without explicit written permission
- Malicious attacks or causing harm
- Illegal activities or criminal purposes
- Disrupting services or causing damage

### Legal Disclaimer

**The developers of TRECO:**
- Are not responsible for any misuse of this tool
- Do not encourage or condone illegal activities
- Provide this tool for educational and authorized testing only

**Users are solely responsible for:**
- Ensuring compliance with applicable laws
- Obtaining proper authorization
- Any consequences of their actions
- Legal and ethical use of the tool

### Ethical Guidelines

**When using TRECO:**

1. **Professionalism**
   - Act professionally at all times
   - Respect organizational boundaries
   - Maintain confidentiality

2. **Responsibility**
   - Report vulnerabilities promptly
   - Provide detailed reproduction steps
   - Assist with remediation when appropriate

3. **Transparency**
   - Be honest about findings
   - Document all testing activities
   - Communicate clearly with stakeholders

4. **Respect**
   - Minimize impact on systems
   - Avoid service disruption
   - Clean up after testing

### Responsible Disclosure

**Recommended Process:**

1. **Discovery**
   - Document vulnerability details
   - Create proof-of-concept
   - Assess impact and severity

2. **Initial Report**
   - Contact appropriate security contact
   - Provide clear description
   - Include reproduction steps
   - Suggest fix timeline (e.g., 90 days)

3. **Collaboration**
   - Work with security team
   - Answer questions promptly
   - Provide additional details if needed

4. **Disclosure**
   - Wait for fix deployment
   - Coordinate public disclosure
   - Credit appropriate parties

### Bug Bounty Programs

**When participating in bug bounties:**

- ✅ Read and follow program rules
- ✅ Test only in-scope systems
- ✅ Respect rate limits
- ✅ Avoid data exfiltration
- ✅ Report through proper channels

---

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, improving documentation, or sharing attack patterns, your help is appreciated.

### Ways to Contribute

- 🐛 **Report Bugs**: Submit detailed bug reports with reproduction steps
- 💡 **Suggest Features**: Propose new features or improvements
- 🔧 **Submit Pull Requests**: Fix bugs or implement features
- 📚 **Improve Documentation**: Enhance docs, add examples, fix typos
- 🎯 **Share Attack Patterns**: Contribute working attack configurations
- 🧪 **Write Tests**: Add unit tests or integration tests
- 🎨 **Improve UI/UX**: Enhance console output or reporting

### Development Setup

```bash
# Fork and clone repository
git clone https://github.com/YOUR-USERNAME/TRECO.git
cd TRECO

# Install with development dependencies
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"

# Verify installation
uv run pytest
```

### Code Quality Standards

Before submitting, ensure code meets quality standards:

```bash
# Format code with Black
uv run black src/treco/

# Lint with Ruff
uv run ruff check src/treco/

# Type checking with mypy (if configured)
# uv run mypy src/treco/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=treco --cov-report=html
```

### Coding Standards

**Follow these guidelines:**

1. **PEP 8 Compliance**
   - Follow Python PEP 8 style guide
   - Use Black formatter (line length: 88)
   - Maintain consistent code style

2. **Type Hints**
   - Add type hints to all functions
   - Use modern typing features (Python 3.10+)
   - Import types from `typing` module

```python
from typing import Optional, Dict, List

def extract_value(response: dict, pattern: str, default: Optional[str] = None) -> Optional[str]:
    """Extract value from response using pattern."""
    pass
```

3. **Docstrings**
   - Add docstrings to all public classes and methods
   - Use Google-style or NumPy-style docstrings
   - Include parameter descriptions and return values

```python
def coordinate_race(threads: int, sync_mechanism: str) -> List[Result]:
    """
    Coordinate race attack with multiple threads.
    
    Args:
        threads: Number of threads to use
        sync_mechanism: Synchronization mechanism (barrier, latch, semaphore)
    
    Returns:
        List of Result objects containing response data
    
    Raises:
        ValueError: If threads < 1 or invalid sync_mechanism
    """
    pass
```

4. **Logging**
   - Use logging module, not print statements
   - Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
   - Include contextual information

```python
import logging

logger = logging.getLogger(__name__)

def process_request():
    logger.debug("Starting request processing")
    logger.info("Request completed successfully")
    logger.warning("Slow response time detected")
    logger.error("Request failed", exc_info=True)
```

5. **Error Handling**
   - Use specific exception types
   - Provide helpful error messages
   - Include context in exceptions

```python
if threads < 1:
    raise ValueError(f"threads must be >= 1, got {threads}")
```

### Testing Guidelines

**Write tests for:**
- New features
- Bug fixes
- Edge cases
- Error handling

```python
import pytest
from treco.connection import PreconnectStrategy

def test_preconnect_strategy():
    """Test preconnect strategy creates connections."""
    strategy = PreconnectStrategy(host="example.com", port=443)
    connections = strategy.create_connections(threads=5)
    assert len(connections) == 5

def test_preconnect_invalid_threads():
    """Test preconnect with invalid thread count."""
    strategy = PreconnectStrategy(host="example.com", port=443)
    with pytest.raises(ValueError):
        strategy.create_connections(threads=0)
```

### Pull Request Process

1. **Create Feature Branch**
```bash
git checkout -b feature/amazing-feature
```

2. **Make Changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation

3. **Commit Changes**
```bash
git add .
git commit -m "feat: add amazing feature"
```

**Use Conventional Commits:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

4. **Push to Fork**
```bash
git push origin feature/amazing-feature
```

5. **Create Pull Request**
   - Provide clear description
   - Reference related issues
   - Include test results
   - Update CHANGELOG.md

### Documentation Contributions

**To improve documentation:**

1. **README.md**
   - Fix typos or unclear sections
   - Add missing information
   - Improve examples

2. **docs/source/\*.rst**
   - Update API documentation
   - Add tutorials
   - Clarify configuration options

3. **Code Comments**
   - Add missing docstrings
   - Clarify complex logic
   - Update outdated comments

### Community Guidelines

**Be respectful and professional:**

- 🤝 Treat everyone with respect
- 💬 Communicate clearly and constructively
- 🎯 Stay focused on technical issues
- 📚 Help others learn and improve
- 🌟 Celebrate contributions from all levels

### Getting Help

**Need help contributing?**

- 📖 Read the [Documentation](https://treco.readthedocs.io)
- 💬 Open a [Discussion](https://github.com/maycon/TRECO/discussions)
- 🐛 Check [Issues](https://github.com/maycon/TRECO/issues)
- 📧 Contact maintainers through GitHub

---

## 📄 License

TRECO is released under the **MIT License**.

### What This Means

**You can:**
- ✅ Use commercially
- ✅ Modify and distribute
- ✅ Use privately
- ✅ Sublicense

**You must:**
- 📋 Include license and copyright notice
- 📄 State changes made to the code

**You cannot:**
- ⚠️ Hold authors liable for damages
- ⚠️ Use without proper authorization for testing

See the [LICENSE](LICENSE) file for full terms.

---

## 🙏 Acknowledgments

TRECO was built on the shoulders of giants. We'd like to thank:

### Inspiration
- **[TREM](https://github.com/otavioarj/TREM)**: The project that inspired TRECO's initial approach and design

### Technologies
- **Python Community**: For Python 3.14t free-threaded build
- **httpx**: Modern, full-featured HTTP client
- **Jinja2**: Powerful template engine
- **PyYAML**: YAML parser and emitter
- **PyOTP**: TOTP generation library

### Security Community
- Security researchers who discovered and disclosed race condition vulnerabilities
- Bug bounty hunters who test and improve web application security
- Open source contributors who make tools like this possible

### Contributors
- All contributors who have submitted code, documentation, or bug reports
- Users who have provided feedback and suggestions
- Security professionals who have tested and validated TRECO

---

## 📞 Support

### Documentation

- 📖 **Read the Docs**: [treco.readthedocs.io](https://treco.readthedocs.io)
- 📚 **Installation Guide**: See [Installation](#installation)
- 🚀 **Quick Start**: See [Quick Start](#quick-start)
- 💡 **Examples**: See [Examples](#examples)

### Community

- 💬 **GitHub Discussions**: [github.com/maycon/TRECO/discussions](https://github.com/maycon/TRECO/discussions)
- 🐛 **GitHub Issues**: [github.com/maycon/TRECO/issues](https://github.com/maycon/TRECO/issues)
- 📧 **Contact**: Create an issue for support requests

### Getting Help

**Before asking for help:**

1. Check the [documentation](https://treco.readthedocs.io)
2. Search [existing issues](https://github.com/maycon/TRECO/issues)
3. Review [discussions](https://github.com/maycon/TRECO/discussions)
4. Try [troubleshooting](#troubleshooting) steps

**When asking for help, include:**

- TRECO version: `treco --version`
- Python version: `python --version`
- Operating system
- Complete error messages
- Configuration file (sanitized)
- Steps to reproduce

---

## 🔗 Related Projects

### Official Package

- **[PyPI: treco-framework](https://pypi.org/project/treco-framework/)**: Official Python package on PyPI

### Vulnerable Testing Targets

- **[Hack N' Roll Racing Bank](https://github.com/maycon/racing-bank)**: A deliberately vulnerable banking application designed for race condition testing with TRECO

### Similar Tools

- **[Turbo Intruder](https://github.com/PortSwigger/turbo-intruder)**: Burp Suite extension for high-speed HTTP requests
- **[Race The Web](https://github.com/TheHackerDev/race-the-web)**: Web application race condition testing tool
- **[HTTP Request Smuggler](https://github.com/PortSwigger/http-request-smuggler)**: Burp Suite extension for request smuggling

---

## 📊 Project Status

**Current Version**: 1.2.0

**Development Status**: Beta (Production Ready for Authorized Testing)

**Maintenance**: Actively Maintained

**API Stability**: Stable

---

## 🎓 Citation

If you use TRECO in academic research or security publications, please cite:

```bibtex
@software{treco2025,
  title = {TRECO: Tactical Race Exploitation \& Concurrency Orchestrator},
  author = {Vitali, Maycon Maia},
  year = {2025},
  version = {1.2.0},
  url = {https://github.com/maycon/TRECO},
  license = {MIT}
}
```

---

<div align="center">

**⚠️ USE RESPONSIBLY - AUTHORIZED TESTING ONLY ⚠️**

---

Made with ❤️ by security researchers, for security researchers

[⭐ Star on GitHub](https://github.com/maycon/TRECO) | [📖 Documentation](https://treco.readthedocs.io) | [🐛 Report Bug](https://github.com/maycon/TRECO/issues) | [💡 Request Feature](https://github.com/maycon/TRECO/issues)

</div>