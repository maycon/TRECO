# TRECO

<div align="center">
<img src="static/treco.png" alt="TRECO Logo" width="220" />

**T**actical **R**ace **E**xploitation & **C**oncurrency **O**rchestrator

*A specialized framework for identifying and exploiting race condition vulnerabilities in HTTP APIs.*

[![Python 3.14t](https://img.shields.io/badge/python-3.14t-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Free-Threaded](https://img.shields.io/badge/GIL-Free-green.svg)](https://peps.python.org/pep-0703/)
</div>

---

## Overview

TRECO enables security researchers to orchestrate highly precise concurrent HTTP attacks with sub-microsecond timing accuracy, making it possible to reliably trigger race conditions in web applications.

**Common vulnerabilities tested:**
- Double-spending attacks (payment processing)
- Fund redemption exploits (financial applications)
- Inventory manipulation (e-commerce)
- Privilege escalation (authentication systems)
- Rate limiting bypasses

---

## Key Features

- **⚡ Precision Timing**: Sub-microsecond race window (< 1μs)
- **🔓 GIL-Free**: Python 3.14t free-threaded build for true parallel execution
- **🔄 Flexible Sync**: Barrier, countdown latch, and semaphore mechanisms
- **🌐 HTTP/HTTPS**: Full HTTP/1.1 support with TLS configuration
- **🎨 Template Engine**: Jinja2-based with custom filters (TOTP, hashing, env vars)
- **📊 Analysis**: Automatic race window calculation and vulnerability detection
- **🔌 Extensible**: Plugin-based extractors and connection strategies

### Why Python 3.14t?

Python 3.14t is the **free-threaded** build that removes the Global Interpreter Lock (GIL):

- **True Parallelism**: Multiple threads execute simultaneously without GIL contention
- **Better Timing**: More consistent and precise race window timing
- **Improved Performance**: Better CPU utilization for multi-threaded workloads
- **Perfect for TRECO**: Race condition testing benefits significantly from true parallelism

---

## Quick Start

### Installation

**Prerequisites:**
- Python 3.14t (free-threaded build)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/maycon/TRECO.git
cd treco

# Install with uv
uv sync
```

> **Note**: Python 3.14t is the free-threaded build that removes the GIL (Global Interpreter Lock), allowing true parallel execution. This significantly improves TRECO's race condition timing precision.

### Basic Usage

Create `attack.yaml`:

```yaml
metadata:
  name: "Race Condition Test"
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
```

Run the attack:

```bash
# Using uv run
uv run treco attack.yaml

# Or activate the environment and use treco directly
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
treco attack.yaml
```

---

## Architecture

```
┌─────────────┐
│ YAML Config │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│   State     │ ───> │    Race      │
│   Machine   │      │  Coordinator │
└─────────────┘      └──────┬───────┘
       │                    │
       ▼                    ▼
┌─────────────┐      ┌──────────────┐
│  Template   │      │ Thread Pool  │
│   Engine    │      │  (N threads) │
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Barrier    │
                     │     Sync     │
                     └──────┬───────┘
                            │
                            ▼
                     [Concurrent Requests]
                            │
                            ▼
                     ┌──────────────┐
                     │   Target     │
                     │   Server     │
                     └──────────────┘
```

### Components

- **State Machine**: Orchestrates attack flow through states
- **Race Coordinator**: Manages multi-threaded race attacks
- **HTTP Client**: Handles HTTP/HTTPS communication
- **Connection Strategy**: Pre-connection for optimal timing
- **Sync Mechanisms**: Barrier, latch, semaphore for thread coordination
- **Template Engine**: Jinja2 with custom filters for dynamic requests
- **Extractors**: Regex and JSONPath for response parsing

---

## Configuration Reference

### YAML Structure

```yaml
metadata:
  name: string              # Attack name
  version: string           # Version
  author: string            # Author
  vulnerability: string     # CVE/CWE ID

config:
  host: string              # Target host
  port: integer             # Target port
  threads: integer          # Default thread count
  tls:
    enabled: bool           # Use HTTPS
    verify_cert: bool       # Verify SSL certs

entrypoints:
  - state: string           # Starting state
    input:                  # Initial variables
      key: value

states:
  state_name:
    description: string
    request: string         # HTTP request template
    
    extract:                # Response extraction
      var_name:
        type: regex|jpath
        pattern: string
    
    race:                   # Race configuration (optional)
      threads: integer
      sync_mechanism: barrier|countdown_latch|semaphore
      connection_strategy: preconnect|lazy|pooled
      thread_propagation: single|parallel
    
    logger:                 # Logging (optional)
      on_state_enter: string
      on_state_leave: string
      on_thread_enter: string
      on_thread_leave: string
    
    next:                   # State transitions
      - on_status: integer
        goto: string
        delay_ms: integer   # Optional delay
```

### Synchronization Mechanisms

**Barrier (Recommended)**
- All threads wait until last arrives
- Simultaneous release
- Best for race conditions (< 1μs precision)

```yaml
race:
  sync_mechanism: barrier
  threads: 20
```

**Countdown Latch**
- Threads count down to zero
- All release when count reaches 0

```yaml
race:
  sync_mechanism: countdown_latch
  threads: 20
```

**Semaphore**
- Limits concurrent execution
- Good for rate limiting, not races

```yaml
race:
  sync_mechanism: semaphore
  threads: 50
  permits: 10  # Max 10 concurrent
```

### Connection Strategies

**Preconnect (Recommended)**
- Establishes TCP/TLS before race
- Eliminates connection overhead
- Achieves < 1μs race window

```yaml
race:
  connection_strategy: preconnect
```

**Lazy**
- Connects on-demand
- Higher latency, poor for races

**Pooled**
- Shares connection pool
- Serializes requests

---

## Template Syntax

### Variables

```yaml
{{ variable }}
{{ config.host }}
{{ login.token }}
{{ thread.id }}
```

### Filters

```yaml
# TOTP generation
{{ totp(seed) }}

# Hashing
{{ password | md5 }}
{{ password | sha256 }}

# Environment variables
{{ env('API_KEY') }}
{{ env('API_KEY', 'default') }}

# CLI arguments
{{ argv('user', 'guest') }}
```

### Conditionals

```yaml
logger:
  on_state_leave: |
    {% if balance > initial_balance %}
      ⚠ VULNERABLE: Money multiplied!
    {% endif %}
```

---

## Data Extraction

### JSONPath

```yaml
extract:
  token:
    type: jpath
    pattern: "$.access_token"
  
  balance:
    type: jpath
    pattern: "$.user.balance"
```

### XPath

```yaml
extract:
  csrf_token:
    type: xpath
    pattern: '//input[@type='hidden' and @name='csrf']/@value'
```

### Regex

```yaml
extract:
  session_id:
    type: regex
    pattern: "SESSION=([A-Z0-9]+)"
```

---

## Examples

### Double-Spending Attack

```yaml
states:
  race_transfer:
    description: "Transfer funds twice"
    request: |
      POST /api/transfer HTTP/1.1
      Authorization: Bearer {{ token }}
      
      {"amount": 1000, "to": "attacker"}
    
    race:
      threads: 2
      sync_mechanism: barrier
      connection_strategy: preconnect
```

### Inventory Race

```yaml
states:
  race_purchase:
    description: "Purchase limited item"
    request: |
      POST /api/purchase HTTP/1.1
      Authorization: Bearer {{ token }}
      
      {"item_id": "LIMITED_001", "qty": 1}
    
    race:
      threads: 50
      sync_mechanism: barrier
      connection_strategy: preconnect
```

### 2FA Authentication

```yaml
states:
  verify_2fa:
    request: |
      POST /api/2fa HTTP/1.1
      Authorization: Bearer {{ temp_token }}
      
      {"token": "{{ totp(totp_seed) }}"}
    
    extract:
      bearer_token:
        type: jpath
        pattern: "$.access_token"
```

---

## CLI Usage

```bash
# Basic usage
uv run treco config.yaml

# Override credentials
uv run treco config.yaml --user alice --password secret

# Override thread count
uv run treco config.yaml --threads 50

# Override target
uv run treco config.yaml --host api.example.com --port 443

# Verbose output
uv run treco config.yaml --verbose
```

---

## Output Analysis

```
======================================================================
RACE ATTACK: race_redeem
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
  ✓ EXCELLENT race window (< 1ms)

Vulnerability Assessment:
  ⚠ VULNERABLE: Multiple requests succeeded (18)
  ⚠ Potential race condition detected!
======================================================================
```

**Race Window Quality:**
- **< 1ms**: Excellent (true race condition)
- **1-100ms**: Good (sufficient precision)
- **> 100ms**: Poor (timing too imprecise)

---

## Troubleshooting

### Python Version Issues

**Problem**: Wrong Python version or GIL not disabled

**Solution**: Verify and install Python 3.14t
```bash
# Check current Python version
uv run python --version

# List available Python versions
uv python list
```

### Poor Race Window (> 100ms)

**Solution**: Use preconnect + barrier
```yaml
race:
  connection_strategy: preconnect
  sync_mechanism: barrier
```

### Connection Timeouts

**Solution**: Reduce thread count or check network
```yaml
config:
  threads: 10  # Reduce from 50
```

### SSL Certificate Errors

**Solution**: Disable verification for self-signed certs
```yaml
config:
  tls:
    enabled: true
    verify_cert: false
```

### Template Errors

**Solution**: Verify variable names exist in context
```yaml
logger:
  on_state_enter: |
    Available vars: {{ context.keys() | list }}
```

---

## Best Practices

### Performance Optimization

1. **Always use preconnect** for race attacks
2. **Use barrier sync** for best timing precision
3. **Tune thread count** (usually 10-30 is optimal)
4. **Disable connection reuse** for realistic races
5. **Clean up resources** after testing

### Security Testing

1. **Always obtain authorization** before testing
2. **Use test environments** when possible
3. **Document findings** with reproducible steps
4. **Report responsibly** to affected parties
5. **Clean up test data** after completion

---

## Security & Legal

### Responsible Disclosure

TRECO is designed for **authorized security testing only**.

**Requirements:**
- Written authorization from target owner
- Testing only within agreed scope
- Compliance with applicable laws
- Responsible disclosure of vulnerabilities

### Legal Notice

Users are solely responsible for ensuring compliance with applicable laws and regulations. The developers are not responsible for any misuse of this tool.

---

## Contributing

Contributions are welcome! Please follow these guidelines:

### Development Setup

```bash
# Clone repository
git clone https://github.com/maycon/TRECO.git
cd treco

# Install with uv (creates venv automatically)
uv sync

# Or install with development dependencies
uv sync --all-extras
```

### Code Quality

```bash
# Format code
uv run black treco/

# Lint code
uv run flake8 treco/

# Type checking
uv run mypy treco/
```

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

**Code Style:**
- Follow PEP 8
- Add docstrings to classes and methods
- Use type hints
- Use logging instead of print statements

---

## License

MIT License - see LICENSE file for details

---


## Acknowledgments

- Built with Python, Requests, and Jinja2
- Inspired by real-world security research
- Special thanks to [TREM](https://github.com/otavioarj/TREM), which inspired the initial idea and approach for this project.
- Thanks to the security research community

---


## Support

- **Issues**: [GitHub Issues](https://github.com/maycon/TRECO/issues)
- **Documentation**: This README
- **Security**: Report vulnerabilities responsibly

---

## Related Projects & PoCs

- For practical race condition testing, see the [Hack N' Roll Racing Bank](https://github.com/maycon/racing-bank), which can be used as a vulnerable target for TRECO demonstrations and experiments.

---

**⚠️ USE RESPONSIBLY - AUTHORIZED TESTING ONLY ⚠️**