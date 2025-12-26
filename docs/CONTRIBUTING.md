# Contributing to TRECO Documentation

This guide explains how to keep TRECO's documentation updated and consistent with the source code.

## Table of Contents

- [Documentation Structure](#documentation-structure)
- [When to Update Documentation](#when-to-update-documentation)
- [Documentation Workflow](#documentation-workflow)
- [Writing Guidelines](#writing-guidelines)
- [Building Documentation Locally](#building-documentation-locally)
- [Automated Checks](#automated-checks)

---

## Documentation Structure

TRECO documentation is organized as follows:

```
TRECO/
├── README.md                    # Main project README (keep in sync with docs/source/index.rst)
├── CHANGELOG.md                 # Version history (update with every change)
├── ADVANCED_FEATURES.md         # Advanced features documentation
├── docs/
│   ├── source/
│   │   ├── index.rst           # Main documentation page
│   │   ├── installation.rst    # Installation guide
│   │   ├── quickstart.rst      # Quick start guide
│   │   ├── configuration.rst   # Complete config reference
│   │   ├── api.rst             # Python API documentation
│   │   ├── cli.rst             # CLI reference
│   │   ├── examples.rst        # Real-world examples
│   │   ├── extractors.rst      # Data extractors guide
│   │   ├── templates.rst       # Template syntax and filters
│   │   ├── synchronization.rst # Sync mechanisms
│   │   ├── connection-strategies.rst  # Connection strategies
│   │   ├── best-practices.rst  # Performance and security tips
│   │   └── troubleshooting.rst # Common issues
│   ├── requirements.txt        # Documentation build dependencies
│   └── SCHEMA_VALIDATION.md    # JSON Schema info
└── examples/                    # Example configurations (must work!)
```

---

## When to Update Documentation

### Always Update

✅ **API Changes**
- New public classes, functions, or methods in `src/treco/__init__.py`
- Changes to function signatures (parameters, return types)
- New modules or packages

Update: `docs/source/api.rst`

✅ **Configuration Changes**
- New configuration options in YAML
- Changes to existing config structure
- New state machine features

Update: `docs/source/configuration.rst`

✅ **New Features**
- New extractors, filters, or strategies
- New CLI commands or options
- New synchronization mechanisms

Update: Relevant documentation files + `README.md` + `CHANGELOG.md`

✅ **Breaking Changes**
- Removed or changed functionality
- Modified behavior of existing features

Update: `CHANGELOG.md` (under "Changed" or "Removed") + affected docs

### Consider Updating

⚠️ **Internal Refactors**
- If user-visible behavior changes
- If error messages change
- If performance characteristics change significantly

Update: `docs/source/troubleshooting.rst` or relevant sections

⚠️ **Bug Fixes**
- If the bug fix changes documented behavior
- If it affects documented examples

Update: `CHANGELOG.md` (under "Fixed") + affected examples

### No Update Needed

⏭️ **Internal Changes**
- Code refactoring with no external impact
- Test changes
- Internal helper functions
- Comment updates

---

## Documentation Workflow

### 1. Check Automated Alerts

When you create a PR with source code changes, the GitHub Actions workflow will:
- ✅ Detect API changes
- ✅ Check if documentation was updated
- ✅ Validate documentation builds
- ✅ Post a reminder comment if docs weren't updated

### 2. Update Documentation Files

**For API Changes:**

```bash
# Edit the API documentation
vim docs/source/api.rst

# Add or update function/class documentation
# Follow existing format and style
```

**For Configuration Changes:**

```bash
# Update configuration reference
vim docs/source/configuration.rst

# Add examples showing new options
```

**For New Features:**

```bash
# Update multiple files as needed
vim docs/source/examples.rst        # Add usage example
vim docs/source/quickstart.rst      # Update if affects getting started
vim README.md                        # Add to feature list
vim CHANGELOG.md                     # Document under [Unreleased] -> Added
```

### 3. Update Examples

If you add features, create working examples:

```bash
# Create example configuration
vim examples/my-new-feature.yaml

# Test that it works
python -m treco examples/my-new-feature.yaml

# Document it
vim docs/source/examples.rst
```

### 4. Update CHANGELOG

Always update `CHANGELOG.md` under the `[Unreleased]` section:

```markdown
## [Unreleased]

### Added
- New TOTP secret rotation feature (#123)
- Support for custom authentication headers

### Changed
- Improved race window calculation for GIL-free Python

### Fixed
- Fixed cookie extraction with multiple Set-Cookie headers (#124)
```

### 5. Build and Test Documentation

```bash
# Build documentation locally
cd docs
pip install -r requirements.txt
sphinx-build -W -b html source _build/html

# Open in browser
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
```

### 6. Submit PR

Include in your PR description:

```markdown
## Changes
- Added new XYZ feature
- Updated ABC configuration

## Documentation Updates
- [x] Updated API reference (api.rst)
- [x] Added example to examples.rst
- [x] Updated CHANGELOG.md
- [x] Tested documentation builds locally
```

---

## Writing Guidelines

### Style

1. **Be Clear and Concise**
   - Use simple language
   - Avoid jargon unless necessary
   - Define technical terms when first used

2. **Use Examples**
   ```rst
   # Good - with example
   The ``threads`` option controls concurrency:
   
   .. code-block:: yaml
   
      race:
        threads: 20  # 20 concurrent threads
   
   # Less helpful - no example
   The threads option controls how many threads are used.
   ```

3. **Show Before/After for Changes**
   ```rst
   **Before (v1.2):**
   
   .. code-block:: yaml
   
      sync: barrier
   
   **After (v1.3):**
   
   .. code-block:: yaml
   
      race:
        sync_mechanism: barrier
   ```

### Format

1. **Use reStructuredText (RST) for docs/source/**
   ```rst
   Title
   =====
   
   Section
   -------
   
   Subsection
   ~~~~~~~~~~
   
   **Bold text**
   *Italic text*
   ``code``
   
   .. code-block:: python
   
      from treco import RaceCoordinator
   ```

2. **Use Markdown for root-level files**
   ```markdown
   # Title
   
   ## Section
   
   ### Subsection
   
   **Bold**, *italic*, `code`
   
   ```python
   from treco import RaceCoordinator
   ```
   ```

3. **Code Examples Must Work**
   - Test all code examples
   - Use realistic but safe values
   - Include necessary imports
   - Show expected output

### Cross-References

Link between documentation pages:

```rst
See :doc:`installation` for setup instructions.
See :doc:`api` for the Python API reference.
See :ref:`configuration-tls` for TLS options.
```

---

## Building Documentation Locally

### Prerequisites

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Install TRECO in development mode
pip install -e .
```

### Build HTML Documentation

```bash
cd docs

# Clean previous build
rm -rf _build/

# Build (warnings as errors)
sphinx-build -W -b html source _build/html

# Build without warnings-as-errors (for debugging)
sphinx-build -b html source _build/html
```

### Build PDF Documentation

```bash
cd docs
sphinx-build -b latex source _build/latex
cd _build/latex
make
```

### Live Preview with Auto-Reload

```bash
pip install sphinx-autobuild
cd docs
sphinx-autobuild source _build/html
# Open http://127.0.0.1:8000 in browser
```

---

## Automated Checks

The documentation workflow (`.github/workflows/docs.yaml`) automatically:

### On Pull Requests

1. **Detects Changes**
   - Identifies source code modifications
   - Checks if documentation was updated
   - Analyzes new/changed functions and classes

2. **Validates Documentation**
   - Builds documentation (fails on errors)
   - Checks for broken internal links
   - Validates Python code examples
   - Verifies imports work

3. **Checks Coverage**
   - Ensures public APIs are documented
   - Verifies CLI documentation matches implementation

4. **Posts Reminders**
   - Comments on PR if docs need updating
   - Lists specific files to consider updating

### On Push to Main

1. **All PR checks** +
2. **Triggers ReadTheDocs build**
3. **Generates documentation summary**

### Manual Workflow Trigger

You can manually trigger the workflow from GitHub Actions tab:
- Go to Actions → Documentation → Run workflow

---

## Tips for Maintainers

### Reviewing Documentation PRs

✅ Checklist:
- [ ] Documentation builds without errors
- [ ] Examples actually work (test them!)
- [ ] CHANGELOG.md updated appropriately
- [ ] Version numbers consistent
- [ ] No broken links
- [ ] Code examples include all necessary imports
- [ ] New features explained clearly

### Keeping Examples Current

Periodically run all examples to ensure they still work:

```bash
# Test all YAML examples
for file in examples/**/*.yaml; do
  echo "Testing $file..."
  python -m treco "$file" --validate-only || echo "❌ $file failed"
done
```

### Updating for New Versions

When releasing a new version:

1. Update version in:
   - `pyproject.toml`
   - `src/treco/__init__.py`
   - `docs/source/conf.py`

2. Move `[Unreleased]` section in CHANGELOG to new version:
   ```markdown
   ## [1.4.0] - 2024-12-27
   
   ### Added
   - Feature X
   - Feature Y
   ```

3. Create new empty `[Unreleased]` section

4. Update version comparison links at bottom of CHANGELOG

### ReadTheDocs Integration

TRECO uses ReadTheDocs for documentation hosting.

**Configuration:** `.readthedocs.yaml`

**Preview builds:**
- Every PR gets a preview: `https://treco--XXX.readthedocs.build/`
- Check preview before merging

**Published docs:**
- Latest: `https://treco.readthedocs.io/en/latest/`
- Stable: `https://treco.readthedocs.io/en/stable/`
- Specific version: `https://treco.readthedocs.io/en/v1.3.1/`

---

## Questions?

- **Documentation issues:** Open an issue with label `documentation`
- **General questions:** Use GitHub Discussions
- **Urgent doc bugs:** Tag issue as `priority` + `documentation`

---

## Summary

**Remember:**
1. 📝 Update docs when changing user-facing code
2. ✅ Test documentation builds locally
3. 📋 Always update CHANGELOG.md
4. 🔍 Review automated workflow feedback
5. 💡 Use examples liberally
6. 🔗 Verify links and imports work

**The goal:** Keep documentation accurate, helpful, and synchronized with the code so users can rely on it!
