# TRECO

<div align="center">
<img src="static/treco.png" alt="TRECO Logo" width="220" />

**T**actical **R**ace **E**xploitation & **C**oncurrency **O**rchestrator

*A specialized framework for identifying and exploiting race condition vulnerabilities in HTTP APIs with sub-microsecond precision.*

[![Python 3.14t](https://img.shields.io/badge/python-3.14t-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Free-Threaded](https://img.shields.io/badge/GIL-Free-green.svg)](https://peps.python.org/pep-0703/)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue.svg)](https://treco.readthedocs.io)

[Documentation](https://treco.readthedocs.io) | [PyPI Package](https://pypi.org/project/treco-framework/) | [Quick Start](#quick-start) | [Examples](#examples)

<a href="https://buymeacoffee.com/maycon" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>
<a href="https://github.com/sponsors/maycon" target="_blank"><img src="https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?style=for-the-badge&logo=github" alt="GitHub Sponsor" style="height: 40px !important;"></a>

</div>

---

## 🎯 Overview

TRECO enables security researchers to orchestrate highly precise concurrent HTTP attacks with **sub-microsecond timing accuracy**, making it possible to reliably trigger race conditions in web applications. Built for both Python 3.10+ (with GIL) and Python 3.14t (GIL-free), TRECO achieves unprecedented timing precision for race condition exploitation.

### Common Vulnerabilities Tested

- 💰 **Double-spending attacks** - Payment processing vulnerabilities
- 🎁 **Fund redemption exploits** - Gift cards and coupon abuse
- 📦 **Inventory manipulation** - Limited stock bypasses
- 🔐 **Privilege escalation** - Authentication/authorization flaws
- ⚡ **Rate limiting bypasses** - API quota exhaustion
- 🎟️ **Voucher abuse** - Single-use code reuse
- 🏦 **TOCTOU vulnerabilities** - Time-of-Check to Time-of-Use exploits

---

## ✨ Key Features

- **⚡ Sub-Microsecond Precision**: Race windows < 1μs with barrier synchronization
- **🔓 GIL-Free Option**: Python 3.14t for true parallel execution
- **🔄 Flexible Synchronization**: Barrier, countdown latch, and semaphore mechanisms
- **🌐 Full HTTP/HTTPS Support**: HTTP/1.1 and HTTP/2 with TLS/SSL
- **🎨 Powerful Templates**: Jinja2-based with TOTP, hashing, env vars, and more
- **🎯 Dynamic Input Sources**: Brute-force, enumeration, and combination attacks
- **📊 Automatic Analysis**: Race window calculation and vulnerability detection
- **🔌 Extensible Architecture**: Plugin-based extractors and connection strategies
- **✅ JSON Schema Validation**: IDE integration and real-time validation

---

## 📦 Quick Start

### Installation

```bash
# Install from PyPI
pip install treco-framework

# Or with uv (faster)
uv pip install treco-framework

# Verify installation
treco --version
```

### Your First Test

Create a file `test.yaml`:

```yaml
metadata:
  name: "Race Condition Test"
  version: "1.0"
  author: "Security Researcher"
  vulnerability: "CWE-362"

target:
  host: "api.example.com"
  port: 443
  tls:
    enabled: true

entrypoint:
  state: race_attack
  input:
    voucher_code: "DISCOUNT50"

states:
  race_attack:
    description: "Test voucher race condition"
    race:
      threads: 20
      sync_mechanism: barrier
      connection_strategy: preconnect
    
    request: |
      POST /api/vouchers/redeem HTTP/1.1
      Host: {{ target.host }}
      Content-Type: application/json
      
      {"code": "{{ voucher_code }}"}
    
    next:
      - on_status: 200
        goto: end
  
  end:
    description: "Attack completed"
```

Run the test:

```bash
treco test.yaml
```

---

## 📖 Documentation

For detailed documentation, please visit [treco.readthedocs.io](https://treco.readthedocs.io):

- **[Installation Guide](https://treco.readthedocs.io/en/latest/installation.html)** - Complete installation instructions for all platforms
- **[Quick Start Tutorial](https://treco.readthedocs.io/en/latest/quickstart.html)** - Your first race condition test in 5 minutes
- **[Configuration Reference](https://treco.readthedocs.io/en/latest/configuration.html)** - Complete YAML configuration guide
- **[Synchronization Mechanisms](https://treco.readthedocs.io/en/latest/synchronization.html)** - Barrier, latch, and semaphore patterns
- **[Connection Strategies](https://treco.readthedocs.io/en/latest/connection-strategies.html)** - Preconnect, pooled, lazy, and multiplexed
- **[Data Extractors](https://treco.readthedocs.io/en/latest/extractors.html)** - JSONPath, XPath, Regex, and more
- **[Template Engine](https://treco.readthedocs.io/en/latest/templates.html)** - Jinja2 syntax and custom filters
- **[Examples](https://treco.readthedocs.io/en/latest/examples.html)** - Real-world attack scenarios
- **[CLI Reference](https://treco.readthedocs.io/en/latest/cli.html)** - Command-line options
- **[API Documentation](https://treco.readthedocs.io/en/latest/api.html)** - Python API for programmatic use
- **[Troubleshooting](https://treco.readthedocs.io/en/latest/troubleshooting.html)** - Common issues and solutions
- **[Best Practices](https://treco.readthedocs.io/en/latest/best-practices.html)** - Performance optimization and security

---

## 💡 Examples

Check out the [examples/](examples/) directory for real-world attack scenarios:

- **[PortSwigger Labs](examples/portswigger/)** - Solutions for Web Security Academy challenges
- **[Racing Bank](examples/racing-bank/)** - Fund redemption attack demonstration
- **[Input Sources](examples/input-sources/)** - Brute-force and enumeration examples
- **[JWT Analysis](examples/jwt-analysis.yaml)** - JWT vulnerability testing
- **[Rate Limit Detection](examples/rate-limit-detection.yaml)** - API rate limiting bypass
- **[Error Detection](examples/error-detection.yaml)** - Error-based race conditions

---

## 🚀 Why Python 3.14t?

Python 3.14t removes the Global Interpreter Lock (GIL) for true parallelism:

| Feature | Python 3.10-3.13 (GIL) | Python 3.14t (GIL-Free) |
|---------|------------------------|-------------------------|
| **True Parallelism** | ❌ Single thread at a time | ✅ Multiple threads simultaneously |
| **Race Window** | ~10-100μs | **< 1μs** (sub-microsecond) |
| **CPU Utilization** | Limited by GIL | Full multi-core usage |
| **Consistency** | Variable timing | Highly consistent |
| **Best for TRECO** | Good | **Excellent** |

> **Note**: TRECO works with both Python 3.10+ and 3.14t, but achieves optimal performance with 3.14t's free-threaded build.

Install Python 3.14t:

```bash
uv python install 3.14t
uv pip install treco-framework --python 3.14t
```

---

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](https://treco.readthedocs.io/en/latest/contributing.html) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 💖 Support the Project

If you find TRECO useful, please consider supporting its development:

<a href="https://buymeacoffee.com/maycon" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

<a href="https://github.com/sponsors/maycon" target="_blank"><img src="https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Sponsor"></a>

Your support helps maintain and improve TRECO for the security research community.

---

## 📄 License

TRECO is released under the **MIT License**. See [LICENSE](LICENSE) for details.

### Responsible Use

⚠️ **AUTHORIZED TESTING ONLY** ⚠️

TRECO is designed for **authorized security testing**. You must:

- ✅ Obtain written authorization before testing
- ✅ Test only within agreed scope and boundaries
- ✅ Comply with all applicable laws and regulations
- ✅ Report vulnerabilities responsibly

**Unauthorized testing may result in criminal prosecution and civil liability.**

Users are solely responsible for ensuring their use complies with applicable laws, regulations, and agreements.

---

## 🙏 Acknowledgments

- **[TREM](https://github.com/otavioarj/TREM)** - The project that inspired TRECO
- **Python Community** - For Python 3.14t free-threaded build
- **httpx**, **Jinja2**, **PyYAML**, **PyOTP** - Essential libraries
- **Security Community** - Researchers and contributors who make this possible

---

## 📞 Support

- 📖 **Documentation**: [treco.readthedocs.io](https://treco.readthedocs.io)
- 💬 **GitHub Discussions**: [github.com/maycon/TRECO/discussions](https://github.com/maycon/TRECO/discussions)
- 🐛 **GitHub Issues**: [github.com/maycon/TRECO/issues](https://github.com/maycon/TRECO/issues)

---

<div align="center">

**⚠️ USE RESPONSIBLY - AUTHORIZED TESTING ONLY ⚠️**

Made with ❤️ by security researchers, for security researchers

[⭐ Star on GitHub](https://github.com/maycon/TRECO) | [📖 Documentation](https://treco.readthedocs.io) | [🐛 Report Bug](https://github.com/maycon/TRECO/issues) | [💡 Request Feature](https://github.com/maycon/TRECO/issues)

</div>