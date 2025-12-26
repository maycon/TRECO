# Multi-Condition When Blocks

This document explains how to use multi-condition when blocks for advanced state transitions in TRECO.

## Overview

Multi-condition when blocks replace simple status-based transitions with rich, complex boolean expressions. They support:

- HTTP status code matching
- Response body content matching
- Header checks and comparisons
- Extracted variable conditions using Jinja2
- Response time analysis
- AND/OR logic for complex routing

## Quick Example

```yaml
states:
  check_authentication:
    request: |
      GET /api/user/profile
    
    extract:
      role:
        type: jpath
        pattern: "$.user.role"
      balance:
        type: jpath
        pattern: "$.user.balance"
    
    next:
      # Route to admin panel if user is admin with 200 status
      - when:
          - status: 200
          - condition: "{{ role == 'admin' }}"
        goto: admin_panel
      
      # Route to high-value if balance > 1000
      - when:
          - status: 200
          - condition: "{{ balance > 1000 }}"
        goto: high_value_target
      
      # Default fallback
      - otherwise:
        goto: normal_flow
```

## Condition Types

### 1. Status Code Matching

```yaml
when:
  - status: 200                    # Exact match
  - status_in: [200, 201, 202]     # Multiple statuses
  - status_range: [200, 299]       # Range (inclusive)
```

### 2. Jinja2 Expressions

Evaluate complex boolean expressions using extracted variables:

```yaml
when:
  - condition: "{{ role == 'admin' }}"
  - condition: "{{ balance > 1000 }}"
  - condition: "{{ age >= 18 and age <= 65 }}"
  - condition: "{{ 'premium' in user.features }}"
```

**Supported operators:**
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Membership: `in`, `not in`
- Boolean: `and`, `or`, `not`
- String operations via Jinja2 filters

### 3. Body Content Matching

```yaml
when:
  - body_contains: "success"           # Substring match
  - body_not_contains: "error"         # Negative match
  - body_matches: "^HTTP/1\\.1 200"    # Regex match
  - body_equals: '{"status": "ok"}'    # Exact match
```

### 4. Header Checks

```yaml
when:
  # Simple existence check
  - header_exists: "X-Auth-Token"
  - header_not_exists: "X-Debug"
  
  # Value matching
  - header_equals:
      name: "Content-Type"
      value: "application/json"
  
  # Substring matching
  - header_contains:
      name: "Set-Cookie"
      value: "session="
  
  # Regex matching
  - header_matches:
      name: "X-Request-ID"
      pattern: "^req-[0-9a-f]{8}$"
```

### 5. Numeric Header Comparisons

```yaml
when:
  - header_compare:
      name: "X-Rate-Limit-Remaining"
      operator: "<"
      value: 10
  
  - header_compare:
      name: "Content-Length"
      operator: ">"
      value: 1048576  # > 1MB
```

**Valid operators:** `<`, `<=`, `>`, `>=`, `==`, `!=`

### 6. Response Time Checks

```yaml
when:
  - response_time_ms:
      operator: ">"
      value: 5000  # Slow response (> 5 seconds)
```

## Logic

### AND Logic (within a when block)

All conditions in a when block must be true:

```yaml
when:
  - status: 200              # AND
  - condition: "{{ x > 10 }}"    # AND
  - body_contains: "success"     # All must be true
goto: success
```

### OR Logic (across multiple when blocks)

The first matching when block is used:

```yaml
next:
  - when: [condition1]    # Try this first
    goto: state1
  
  - when: [condition2]    # OR try this
    goto: state2
  
  - when: [condition3]    # OR this
    goto: state3
  
  - otherwise:            # Default fallback
    goto: default_state
```

## Complete Examples

### Role-Based Routing

```yaml
states:
  check_permissions:
    request: GET /api/user
    extract:
      role: {type: jpath, pattern: "$.role"}
    
    next:
      - when:
          - status: 200
          - condition: "{{ role == 'admin' }}"
        goto: admin_vulnerabilities
      
      - when:
          - status: 200
          - condition: "{{ role == 'user' }}"
        goto: user_vulnerabilities
      
      - otherwise:
        goto: no_access
```

### Rate Limit Detection

```yaml
states:
  api_request:
    request: GET /api/data
    
    next:
      - when:
          - status: 429
        goto: rate_limited
      
      - when:
          - status: 200
          - header_compare:
              name: "X-Rate-Limit-Remaining"
              operator: "<"
              value: 10
        goto: approaching_limit
      
      - when:
          - status: 200
        goto: continue_attack
```

### Error Detection

```yaml
states:
  exploit_attempt:
    request: POST /api/admin
    
    next:
      # Successful exploit
      - when:
          - status: 200
          - body_not_contains: "error"
          - body_not_contains: "exception"
        goto: exploit_successful
      
      # SQL injection detected
      - when:
          - body_matches: ".*SQL.*syntax.*"
        goto: sql_injection_detected
      
      # Debug mode enabled
      - when:
          - body_contains: "stack trace"
        goto: debug_mode_enabled
      
      - otherwise:
        goto: exploit_failed
```

## Backward Compatibility

The old `on_status` syntax continues to work:

```yaml
# Old syntax (still supported)
next:
  - on_status: 200
    goto: success
  - on_status: [404, 500]
    goto: error

# New syntax (equivalent)
next:
  - when:
      - status: 200
    goto: success
  - when:
      - status_in: [404, 500]
    goto: error
```

## Best Practices

1. **Order matters**: When blocks are evaluated in order. Put most specific conditions first.

2. **Use otherwise**: Always include an `otherwise` block as a safety net:
   ```yaml
   next:
     - when: [specific_conditions]
       goto: specific_state
     - otherwise:
       goto: error
   ```

3. **Keep conditions simple**: Break complex logic into multiple states if needed.

4. **Test extracted variables**: Check if extracted variables exist before using them:
   ```yaml
   when:
     - condition: "{{ role is defined and role == 'admin' }}"
   ```

5. **Combine wisely**: Use AND logic within when blocks for related conditions, OR logic across blocks for alternatives.

## Performance

- Condition evaluation adds < 1ms overhead per transition
- Regex matching is optimized but can be slower for complex patterns
- Jinja2 expressions are cached by the template engine

## Troubleshooting

### Condition never matches
- Check that extracted variables are available (add logging in state)
- Verify Jinja2 syntax is correct
- Ensure response content is what you expect

### Otherwise always triggers
- Previous when blocks may have conditions that are too strict
- Check response status codes match your expectations
- Add logging to see which conditions fail

### Unexpected state transitions
- Review condition evaluation order
- Check for overlapping conditions in multiple when blocks
- Verify extracted variable values

## See Also

- Full examples in `examples/` directory
- Issue #3 for implementation details
- ADVANCED_FEATURES.md for other TRECO features
