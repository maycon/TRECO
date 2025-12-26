# Changelog

All notable changes to TRECO will be documented in this file.

## [Unreleased]

### Added
- Dynamic input sources for race attacks with multiple distribution modes:
  - `distribute` mode: Round-robin distribution of values across threads
  - `product` mode: Cartesian product for combination testing
  - `random` mode: Random value selection per thread
  - `same` mode: All threads use same value (default, backward compatible)
- Support for multiple input source types:
  - Inline lists: Direct values in YAML
  - File source: Load from external files or built-in wordlists
  - Generator source: Dynamic generation using Jinja2 expressions
  - Range source: Numeric sequences
- Built-in wordlists:
  - `builtin:passwords-top-100` - Top 100 common passwords
  - `builtin:usernames-common` - Common usernames
- State-level input override capability
- `input.*` namespace available in request templates and loggers
- Comprehensive examples in `examples/input-sources/`
- Full test coverage for input functionality (24 tests)
- Initial release
