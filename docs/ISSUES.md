# Documentation Issues Found

This file tracks documentation inconsistencies found during automated analysis.
These should be addressed in future updates.

## Critical Issues

### 1. Configuration Section Name Mismatch

**Issue**: Documentation uses `config:` but source code expects `target:`

**Files Affected**:
- `docs/source/configuration.rst` - Uses `config:` throughout
- `docs/source/index.rst` - Uses `config:` in examples
- `README.md` - Uses `config:` in examples

**Source Code Reality**:
- `src/treco/models/config.py` - Defines `target: TargetConfig`
- `src/treco/parser/loaders/yaml.py` - Expects `data["target"]`
- `examples/*.yaml` - Use `target:` correctly

**Priority**: HIGH - This affects all users

**Resolution**: Update all documentation to use `target:` instead of `config:`

### 2. Example Files in Documentation vs Repository

**Issue**: Documentation references example files that may not exist

**Referenced in docs**:
- `examples/double-spending.yaml` (docs/source/examples.rst)
- `examples/coupon-race.yaml` (docs/source/examples.rst)
- `examples/inventory-race.yaml` (docs/source/examples.rst)

**Actual examples**:
- `examples/test.yaml`
- `examples/error-detection.yaml`
- `examples/role-based-routing.yaml`
- `examples/racing-bank/fund-redemption-attack.yaml`
- `examples/when-blocks-demo.yaml`

**Priority**: MEDIUM - Confusing but not blocking

**Resolution**: Either create the referenced examples or update docs to reference existing ones

## Minor Issues

### 3. Version Number in README

**Issue**: README.md shows different version than pyproject.toml in Project Status section

**Location**: README.md "Project Status" section
**Shows**: Previously showed 1.2.0
**Fixed**: Now shows 1.3.1

**Priority**: LOW - Fixed in this PR

**Resolution**: ✓ Completed

---

## How to Help

If you find additional documentation issues:

1. Add them to this file with:
   - Clear description
   - Affected files
   - Priority (HIGH/MEDIUM/LOW)
   - Suggested resolution

2. Or create a GitHub issue with label `documentation`

3. Or fix them directly and submit a PR following `docs/CONTRIBUTING.md`

---

Last Updated: 2024-12-26
