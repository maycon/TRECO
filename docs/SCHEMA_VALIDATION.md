# JSON Schema Validation

TRECO includes JSON Schema validation to catch configuration errors early and provide better IDE support.

## Features

### Layered Validation Architecture

TRECO uses a three-layer validation approach:

1. **Schema Validation (Pre-runtime)** - Validates:
   - YAML syntax correctness
   - Data types and structure
   - Enum values
   - Numeric ranges
   - Pattern matching (e.g., version format, CVE/CWE identifiers)

2. **Semantic Validation (Runtime)** - Validates:
   - Referenced states exist
   - Extractor patterns are valid
   - Transitions reference valid states

3. **Runtime Checks (During execution)** - Validates:
   - Connection to host successful
   - Authentication valid
   - Responses in expected format

### Benefits

- **Early Error Detection**: Catch 80%+ of configuration errors before running
- **IDE Integration**: Real-time error highlighting and autocomplete in VSCode, PyCharm, etc.
- **Inline Documentation**: Schema descriptions appear as tooltips in editors
- **Clear Error Messages**: Specific, actionable error messages with field paths
- **Pre-commit Validation**: Validate configurations before committing to repositories

## Usage

### Command Line Validation

Validate a configuration file without executing it:

```bash
treco --validate-only attack.yaml
```

Example output for valid configuration:
```
⏳ Running schema validation...
✓ Schema validation passed
⏳ Running semantic validation...
✓ Semantic validation passed

✓ Configuration is valid: attack.yaml
```

Example output for invalid configuration:
```
⏳ Running schema validation...
✗ Schema validation failed:
Schema validation failed at 'metadata -> vulnerability': 'INVALID-123' does not match '^(CVE|CWE)-\d+'
  Invalid value: INVALID-123
```

### IDE Setup

#### VSCode

1. Install the [YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)

2. Copy the example settings file:
   ```bash
   cp .vscode/settings.json.example .vscode/settings.json
   ```

3. Or manually add to `.vscode/settings.json`:
   ```json
   {
     "yaml.schemas": {
       "./schema/treco-config.schema.json": "*.yaml"
     }
   }
   ```

Now you'll get:
- ✅ Real-time validation as you type
- 💡 Autocomplete for field names
- 📝 Inline documentation on hover
- 🔴 Red squiggles for errors

#### PyCharm / IntelliJ IDEA

1. Go to **Settings** → **Languages & Frameworks** → **Schemas and DTDs** → **JSON Schema Mappings**

2. Click **+** to add a new mapping:
   - **Name**: `TRECO Config`
   - **Schema file or URL**: `schema/treco-config.schema.json`
   - **Schema version**: `JSON Schema version 7`

3. Add file pattern:
   - Click **+** in the mappings section
   - Add pattern: `*.yaml`

#### Other Editors

Most modern editors support JSON Schema validation for YAML files:
- **Vim/Neovim**: Use [coc-yaml](https://github.com/neoclide/coc-yaml) or [yaml-language-server](https://github.com/redhat-developer/yaml-language-server)
- **Emacs**: Use [lsp-mode](https://emacs-lsp.github.io/lsp-mode/) with yaml-language-server
- **Sublime Text**: Use [LSP](https://github.com/sublimelsp/LSP) with yaml-language-server

## Schema Location

The JSON Schema is located at:
```
schema/treco-config.schema.json
```

You can reference it in your YAML files (though this isn't required for validation):
```yaml
# yaml-language-server: $schema=./schema/treco-config.schema.json

metadata:
  name: "My Attack"
  # ...
```

## Common Validation Errors

### Invalid CVE/CWE Format

**Error:**
```
'metadata -> vulnerability': 'INVALID-123' does not match '^(CVE|CWE)-\d+'
```

**Fix:**
```yaml
vulnerability: "CWE-362"  # ✓ Correct
vulnerability: "CVE-2024-1234"  # ✓ Correct
vulnerability: "INVALID-123"  # ✗ Wrong
```

### Invalid Port Number

**Error:**
```
'target -> port': 70000 is greater than the maximum of 65535
```

**Fix:**
```yaml
port: 443  # ✓ Correct (1-65535)
port: 70000  # ✗ Wrong (exceeds max)
```

### Invalid Enum Value

**Error:**
```
'states -> attack -> race -> sync_mechanism': 'invalid' is not one of ['barrier', 'countdown_latch', 'semaphore']
```

**Fix:**
```yaml
race:
  sync_mechanism: barrier  # ✓ Correct
  sync_mechanism: invalid  # ✗ Wrong
```

### Missing Required Field

**Error:**
```
'metadata': 'version' is a required property
```

**Fix:**
```yaml
metadata:
  name: "Attack"
  version: "1.0"  # ✓ Add required field
  author: "Author"
  vulnerability: "CWE-362"
```

## Disabling Schema Validation

Schema validation is enabled by default. If you need to disable it (not recommended):

```python
from treco.parser.loaders.yaml import YAMLLoader

loader = YAMLLoader(enable_schema_validation=False)
config = loader.load("attack.yaml")
```

## Pre-commit Hook

You can add automatic validation to your git pre-commit hooks:

1. Create `.git/hooks/pre-commit`:
   ```bash
   #!/bin/bash
   
   # Validate all YAML files
   for file in $(git diff --cached --name-only | grep '\.yaml$'); do
       echo "Validating $file..."
       treco --validate-only "$file" || exit 1
   done
   ```

2. Make it executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

## CI/CD Integration

Add validation to your CI/CD pipeline:

### GitHub Actions

```yaml
- name: Validate TRECO configs
  run: |
    pip install treco-framework
    for config in configs/*.yaml; do
      treco --validate-only "$config"
    done
```

### GitLab CI

```yaml
validate-configs:
  script:
    - pip install treco-framework
    - find . -name "*.yaml" -exec treco --validate-only {} \;
```

## Schema Evolution

The schema is versioned alongside TRECO releases. Major schema changes will be documented in the [CHANGELOG](CHANGELOG.md).

If you're using an older version of TRECO, you can reference the schema for that version:
```
schema/treco-config-v1.schema.json  # For TRECO v1.x
schema/treco-config-v2.schema.json  # For TRECO v2.x
```
