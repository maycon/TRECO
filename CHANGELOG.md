# Changelog

All notable changes to TRECO will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation automation workflow for keeping docs synchronized with code changes
- Automated API change detection in pull requests
- Documentation validation in CI/CD pipeline

### Changed

### Deprecated

### Removed

### Fixed

### Security

---

## [1.3.1] - 2024-12-26

### Added
- Initial stable release
- Sub-microsecond race condition testing framework
- Support for Python 3.10+ and Python 3.14t (GIL-free)
- Multiple synchronization mechanisms (barrier, countdown latch, semaphore)
- Connection strategies (preconnect, lazy, pooled, multiplexed)
- Jinja2 template engine with custom filters (TOTP, hashing, env vars, CLI args)
- Multiple data extractors (JSONPath, XPath, Regex, Boundary, Header, Cookie)
- Automatic race window calculation and vulnerability assessment
- Comprehensive documentation with ReadTheDocs integration
- JSON Schema validation for configurations
- State machine architecture for complex attack flows
- Full HTTP/HTTPS support with proxy capabilities
- Thread propagation strategies for multi-stage attacks

### Documentation
- Complete user guide and API reference
- Real-world examples for common vulnerabilities
- Configuration reference with all options
- Best practices and troubleshooting guide
- Installation guide for multiple platforms

---

## Versioning Policy

- **Major version (X.0.0)**: Breaking API changes, major architectural changes
- **Minor version (0.X.0)**: New features, non-breaking API additions
- **Patch version (0.0.X)**: Bug fixes, documentation updates, minor improvements

## How to Contribute

When making changes, please update this CHANGELOG:

1. Add your changes under `[Unreleased]` section
2. Use these categories:
   - **Added**: New features
   - **Changed**: Changes in existing functionality
   - **Deprecated**: Soon-to-be removed features
   - **Removed**: Removed features
   - **Fixed**: Bug fixes
   - **Security**: Security fixes or improvements
3. Reference issue/PR numbers: `- Fixed race window calculation (#123)`
4. Be concise but descriptive

[Unreleased]: https://github.com/maycon/TRECO/compare/v1.3.1...HEAD
[1.3.1]: https://github.com/maycon/TRECO/releases/tag/v1.3.1
