# Advanced Features

This document covers advanced TRECO features that provide additional flexibility and control for specialized testing scenarios.

## Table of Contents

- [mTLS (Mutual TLS) Support](#mtls-mutual-tls-support)
- [Proxy Support](#proxy-support)
- [HTTP/2 Support](#http2-support)
- [Connection Reuse](#connection-reuse)
- [Redirect Handling](#redirect-handling)
- [Advanced Timeout Configuration](#advanced-timeout-configuration)
- [All Available Extractors](#all-available-extractors)
- [All Template Filters](#all-template-filters)

---

## mTLS (Mutual TLS) Support

TRECO supports mutual TLS (mTLS) authentication, allowing you to present client certificates when connecting to servers that require certificate-based authentication.

### Why mTLS?

Many enterprise applications and secure APIs require mutual TLS for authentication:

- **Financial Services**: Banking APIs, payment processors
- **Healthcare Systems**: HIPAA-compliant endpoints
- **Government & Military**: Classified systems
- **Zero-Trust Architecture**: Internal microservices
- **IoT Devices**: Device-to-server authentication

Without mTLS support, TRECO cannot test race conditions on these protected endpoints.

### Configuration Options

TRECO supports three formats for client certificates:

#### Option 1: Separate Certificate and Key Files

The most common format - separate files for certificate and private key:

```yaml
target:
  host: secure-api.internal
  port: 443
  tls:
    enabled: true
    verify_cert: true
    client_cert: "./certs/client.crt"
    client_key: "./certs/client.key"
    client_key_password: "{{ env('CLIENT_KEY_PASSWORD') }}"  # Optional
```

**Fields:**
- `client_cert`: Path to X.509 client certificate file (PEM format)
- `client_key`: Path to private key file (PEM format)
- `client_key_password`: Password for encrypted private key (optional)

#### Option 2: Combined PEM File

Some systems provide a single PEM file containing both certificate and key:

```yaml
target:
  host: secure-api.internal
  port: 443
  tls:
    enabled: true
    verify_cert: true
    client_pem: "./certs/client.pem"
```

**Field:**
- `client_pem`: Path to combined PEM file containing certificate and private key

#### Option 3: PKCS12 Format (.pfx/.p12)

**Note:** PKCS12 format is not directly supported by httpx. You must convert to PEM format first.

**Conversion command:**
```bash
# Convert PKCS12 to PEM format
openssl pkcs12 -in client.pfx -out client.pem -nodes

# Or convert to separate cert and key files
openssl pkcs12 -in client.pfx -clcerts -nokeys -out client.crt
openssl pkcs12 -in client.pfx -nocerts -nodes -out client.key
```

After conversion, use Option 1 or Option 2 above.

### Template Support

All certificate paths and passwords support Jinja2 template expressions:

```yaml
target:
  tls:
    enabled: true
    # Load paths from environment variables
    client_cert: "{{ env('CLIENT_CERT_PATH') }}"
    client_key: "{{ env('CLIENT_KEY_PATH') }}"
    client_key_password: "{{ env('CLIENT_KEY_PASSWORD') }}"
    
    # Or use command-line arguments
    # client_cert: "{{ argv(1) }}"
    # client_key: "{{ argv(2) }}"
```

**Available template filters:**
- `env('VAR_NAME')`: Load from environment variable
- `argv(index)`: Load from command-line argument
- See [All Template Filters](#all-template-filters) for complete list

### Usage with Connection Strategies

mTLS works with all connection strategies:

#### Preconnect Strategy
```yaml
states:
  race_transfer:
    race:
      threads: 10
      sync_mechanism: barrier
      connection_strategy: preconnect  # Each thread gets own connection
```

#### Multiplexed Strategy (HTTP/2)
```yaml
states:
  race_transfer:
    race:
      threads: 10
      sync_mechanism: barrier
      connection_strategy: multiplexed  # Single HTTP/2 connection shared
```

#### Lazy and Pooled Strategies
```yaml
states:
  race_transfer:
    race:
      threads: 10
      connection_strategy: lazy  # Or pooled
```

### Usage with Proxy Bypass

mTLS works seamlessly with proxy bypass:

```yaml
target:
  tls:
    enabled: true
    client_cert: "./certs/client.crt"
    client_key: "./certs/client.key"
  proxy:
    host: "proxy.company.com"
    port: 8080

states:
  direct_connection:
    description: "Bypass proxy for this state"
    options:
      proxy_bypass: true  # Direct connection with mTLS
```

### Validation Rules

TRECO enforces these validation rules:

1. **Mutual Exclusivity**: Only ONE certificate format can be specified:
   - ✅ Valid: `client_cert` + `client_key`
   - ✅ Valid: `client_pem`
   - ❌ Invalid: `client_cert` + `client_key` + `client_pem`

2. **Complete Pairs**: When using separate files, both must be provided:
   - ✅ Valid: `client_cert` + `client_key`
   - ❌ Invalid: `client_cert` only
   - ❌ Invalid: `client_key` only

3. **File Existence**: Certificate files are validated at runtime
   - Templates (`env()`, `argv()`) are resolved before validation
   - Clear error messages if files don't exist

### Complete Example

See `examples/mtls-example.yaml` for a complete working example:

```yaml
metadata:
  name: "mTLS Protected API - Race Condition Test"
  version: "1.0"
  author: "Security Team"
  vulnerability: "CWE-362"

target:
  host: secure-api.internal
  port: 443
  tls:
    enabled: true
    verify_cert: true
    client_cert: "./certs/client.crt"
    client_key: "./certs/client.key"
    client_key_password: "{{ env('CLIENT_KEY_PASSWORD') }}"

entrypoint:
  state: race_transfer
  input:
    amount: 1000

states:
  race_transfer:
    description: "Race condition on certificate-authenticated endpoint"
    race:
      threads: 10
      sync_mechanism: barrier
      connection_strategy: multiplexed
    request: |
      POST /api/v1/transfer HTTP/1.1
      Host: {{ target.host }}
      Content-Type: application/json
      
      {"amount": {{ amount }}}
    next:
      - when:
          - status: 200
        goto: end
```

### Running with mTLS

```bash
# Set password via environment variable
export CLIENT_KEY_PASSWORD="my-secure-password"

# Run the attack
treco examples/mtls-example.yaml

# Or specify cert paths via environment
export CLIENT_CERT_PATH="./certs/client.crt"
export CLIENT_KEY_PATH="./certs/client.key"
treco examples/mtls-example.yaml
```

### Troubleshooting

#### Certificate Not Found
```
FileNotFoundError: Client certificate file not found: ./certs/client.crt
```
**Solution:** Ensure the certificate file exists at the specified path.

#### Invalid Certificate Format
```
httpx.SSLError: [SSL: WRONG_VERSION_NUMBER] wrong version number
```
**Solution:** Ensure certificate is in PEM format. Convert if needed:
```bash
openssl x509 -inform DER -in client.der -out client.crt
```

#### Password-Protected Key
```
httpx.SSLError: [SSL: BAD_DECRYPT] bad decrypt
```
**Solution:** Provide `client_key_password` or remove password:
```bash
openssl rsa -in client.key -out client_unencrypted.key
```

#### PKCS12 Not Supported
```
ValueError: PKCS12 (.pfx/.p12) format is not directly supported by httpx
```
**Solution:** Convert to PEM format (see Option 3 above).

---

## Proxy Support

TRECO supports routing requests through HTTP, HTTPS, and SOCKS5 proxies, with optional authentication.

### Basic Proxy Configuration

```yaml
config:
  host: "api.example.com"
  port: 443
  tls:
    enabled: true
  proxy:
    host: "proxy.company.com"
    port: 8080
    type: "http"  # Options: http, https, socks5
```

### Proxy with Authentication

```yaml
config:
  proxy:
    host: "proxy.company.com"
    port: 8080
    type: "http"
    auth:
      username: "{{ env('PROXY_USER') }}"
      password: "{{ env('PROXY_PASS') }}"
```

### Supported Proxy Types

#### HTTP Proxy

```yaml
config:
  proxy:
    host: "proxy.example.com"
    port: 8080
    type: "http"
```

**Use cases:**
- Corporate proxy servers
- Web filtering proxies
- Basic anonymization

#### HTTPS Proxy

```yaml
config:
  proxy:
    host: "secure-proxy.example.com"
    port: 8443
    type: "https"
```

**Use cases:**
- Encrypted proxy connections
- Secure corporate networks
- Enhanced privacy

#### SOCKS5 Proxy

```yaml
config:
  proxy:
    host: "127.0.0.1"
    port: 9050  # Tor default port
    type: "socks5"
```

**Use cases:**
- Tor network routing
- Advanced anonymization
- Protocol-agnostic proxying

### Proxy Authentication

For proxies requiring authentication:

```yaml
config:
  proxy:
    host: "auth-proxy.example.com"
    port: 8080
    type: "http"
    auth:
      username: "proxyuser"
      password: "proxypass"
```

**Best practice**: Use environment variables for credentials:

```yaml
config:
  proxy:
    auth:
      username: "{{ env('PROXY_USER') }}"
      password: "{{ env('PROXY_PASS') }}"
```

```bash
export PROXY_USER="your-username"
export PROXY_PASS="your-password"
treco attack.yaml
```

### Proxy Performance Impact

⚠️ **Important**: Proxies add latency that affects race window timing:

| Connection Type | Typical Latency | Race Window Impact |
|----------------|----------------|-------------------|
| Direct | < 1ms | < 1μs (optimal) |
| HTTP Proxy | 10-50ms | 50-100ms |
| HTTPS Proxy | 20-80ms | 80-150ms |
| SOCKS5 Proxy | 20-100ms | 100-200ms |
| Tor Network | 200-1000ms | Not suitable for races |

**Recommendations:**

✅ **DO:**
- Use proxies for access control and anonymity
- Test race window with proxy before main attack
- Use preconnect strategy to minimize overhead
- Consider proxy location (closer = better)

❌ **DON'T:**
- Use Tor for race condition testing
- Expect sub-10ms race windows with proxies
- Chain multiple proxies for timing-critical attacks
- Use unstable or slow proxies

### Example Configurations

#### Corporate Network Testing

```yaml
metadata:
  name: "Corporate API Test"
  version: "1.0"

config:
  host: "internal-api.company.com"
  port: 443
  tls:
    enabled: true
    verify_cert: true
  proxy:
    host: "proxy.company.com"
    port: 8080
    type: "http"
    auth:
      username: "{{ env('CORP_USER') }}"
      password: "{{ env('CORP_PASS') }}"

entrypoint:
  state: test
  input: {}

states:
  test:
    description: "Test through corporate proxy"
    request: |
      GET /api/health HTTP/1.1
      Host: {{ config.host }}
      User-Agent: TRECO/1.2.0
    
    extract:
      status:
        type: jpath
        pattern: "$.status"
    
    logger:
      on_state_leave: |
        API Status: {{ status }}
        ✓ Successfully accessed through corporate proxy
    
    next:
      - on_status: 200
        goto: end

  end:
    description: "Test completed"
```

#### Anonymous Testing via SOCKS5

```yaml
metadata:
  name: "Anonymous Security Test"
  version: "1.0"

config:
  host: "target-api.example.com"
  port: 443
  tls:
    enabled: true
  proxy:
    host: "127.0.0.1"
    port: 9050  # Tor
    type: "socks5"

states:
  anonymous_test:
    description: "Test via Tor for anonymity"
    request: |
      GET /api/endpoint HTTP/1.1
      Host: {{ config.host }}
    
    logger:
      on_state_leave: |
        ✓ Request completed anonymously through Tor
        ⚠ Note: High latency, not suitable for race conditions
    
    next:
      - on_status: 200
        goto: end
```

#### Multiple Proxy Strategy (Sequential)

For testing from different sources:

```yaml
# proxy1.yaml
config:
  proxy:
    host: "proxy1.example.com"
    port: 8080

# proxy2.yaml  
config:
  proxy:
    host: "proxy2.example.com"
    port: 8080
```

Run sequentially:

```bash
treco proxy1.yaml
treco proxy2.yaml
```

---

## HTTP/2 Support

TRECO supports HTTP/2 protocol for testing modern web applications and APIs.

### Enabling HTTP/2

HTTP/2 is automatically used with the `multiplexed` connection strategy:

```yaml
config:
  host: "http2-api.example.com"
  port: 443
  tls:
    enabled: true  # Required for HTTP/2

states:
  test_http2:
    request: |
      POST /api/resource HTTP/2
      Host: {{ config.host }}
      Content-Type: application/json
      
      {"data": "test"}
    
    race:
      threads: 10
      sync_mechanism: barrier
      connection_strategy: multiplexed  # Uses HTTP/2
```

### HTTP/2 Features

**Multiplexing**
- Multiple requests over single TCP connection
- Parallel stream processing
- Reduced connection overhead

**Header Compression**
- HPACK compression for headers
- Reduced bandwidth usage
- Faster request processing

**Server Push**
- Server can proactively send resources
- Reduced round trips
- Improved performance

### HTTP/2 vs HTTP/1.1 for Race Conditions

| Aspect | HTTP/1.1 (Preconnect) | HTTP/2 (Multiplexed) |
|--------|----------------------|---------------------|
| **Connections** | Multiple (one per thread) | Single shared |
| **Race Window** | < 1-10μs | 10-50ms |
| **Precision** | Excellent | Moderate |
| **Use Case** | True race conditions | HTTP/2-specific testing |

**Recommendation:** Use HTTP/1.1 with preconnect for race conditions, HTTP/2 only when specifically testing HTTP/2 features.

### Example: HTTP/2 Stream Race

```yaml
metadata:
  name: "HTTP/2 Concurrent Streams Test"
  version: "1.0"

config:
  host: "http2-enabled.example.com"
  port: 443
  tls:
    enabled: true

states:
  http2_race:
    description: "Test concurrent HTTP/2 streams"
    request: |
      POST /api/process HTTP/2
      Host: {{ config.host }}
      Content-Type: application/json
      
      {"action": "process", "thread": {{ thread.id }}}
    
    race:
      threads: 20
      sync_mechanism: barrier
      connection_strategy: multiplexed  # HTTP/2
    
    extract:
      stream_id:
        type: header
        pattern: "X-Stream-ID"
    
    logger:
      on_thread_leave: |
        [Thread {{ thread.id }}] Stream ID: {{ stream_id }}
    
    next:
      - on_status: 200
        goto: end
```

### HTTP/2 Limitations

- Not suitable for traditional race condition testing
- Requires server HTTP/2 support
- Single connection may serialize requests
- Stream ordering controlled by server

---

## Connection Reuse

Control whether TCP connections are reused across requests.

### Global Connection Reuse

```yaml
config:
  host: "api.example.com"
  port: 443
  reuse_connection: true  # Reuse connections globally
```

### Per-Race Connection Reuse

```yaml
states:
  test:
    race:
      threads: 10
      reuse_connections: true  # Reuse within this race
```

### When to Use Connection Reuse

**Enable (`true`) when:**
- Testing keep-alive behavior
- Simulating persistent client connections
- Reducing server load during testing
- Testing connection pooling vulnerabilities

**Disable (`false`) when:**
- Testing race conditions (default and recommended)
- Need fresh connections for each request
- Testing connection-level security
- Measuring true cold-start performance

### Example: Testing Keep-Alive

```yaml
metadata:
  name: "Keep-Alive Connection Test"

config:
  host: "api.example.com"
  port: 443
  reuse_connection: true

states:
  test_keepalive:
    description: "Test multiple requests on same connection"
    request: |
      GET /api/data HTTP/1.1
      Host: {{ config.host }}
      Connection: keep-alive
    
    race:
      threads: 10
      reuse_connections: true
      sync_mechanism: semaphore
      permits: 5
    
    logger:
      on_state_leave: |
        ✓ Tested {{ threads }} requests with connection reuse
```

---

## Redirect Handling

Control how HTTP redirects (3xx responses) are handled.

### Configuration

```yaml
config:
  host: "api.example.com"
  port: 443
  http:
    follow_redirects: true  # Default: true
```

### Follow Redirects (Default)

```yaml
config:
  http:
    follow_redirects: true

states:
  test:
    request: |
      GET /api/redirect-endpoint HTTP/1.1
      Host: {{ config.host }}
    # Automatically follows 301, 302, 303, 307, 308 redirects
```

### Don't Follow Redirects

```yaml
config:
  http:
    follow_redirects: false

states:
  test:
    request: |
      GET /api/redirect-endpoint HTTP/1.1
      Host: {{ config.host }}
    
    extract:
      redirect_location:
        type: header
        pattern: "Location"
    
    next:
      - on_status: 302
        goto: handle_redirect
```

### Use Cases

**Follow redirects when:**
- Testing final destination behavior
- Normal API interaction flow
- Don't care about intermediate redirects

**Don't follow redirects when:**
- Testing redirect logic itself
- Need to inspect redirect chains
- Testing open redirect vulnerabilities
- Manually handling redirect logic

### Example: Testing Open Redirect

```yaml
metadata:
  name: "Open Redirect Test"
  vulnerability: "CWE-601"

config:
  host: "vulnerable-app.example.com"
  port: 443
  tls:
    enabled: true
  http:
    follow_redirects: false  # Don't auto-follow

states:
  test_redirect:
    description: "Test for open redirect vulnerability"
    request: |
      GET /redirect?url=https://evil.com HTTP/1.1
      Host: {{ config.host }}
    
    extract:
      location:
        type: header
        pattern: "Location"
    
    logger:
      on_state_leave: |
        Redirect location: {{ location }}
        {% if 'evil.com' in location %}
        🚨 VULNERABLE: Open redirect to {{ location }}
        {% else %}
        ✓ Safe redirect handling
        {% endif %}
    
    next:
      - on_status: 302
        goto: end
```

---

## Advanced Timeout Configuration

Control request timeout at global and per-state levels.

### Global Timeout

```yaml
config:
  host: "api.example.com"
  port: 443
  timeout: 60  # Seconds (default: 30)
```

### Use Cases by Timeout Value

**Short timeout (5-15s):**
- Quick API endpoints
- Health checks
- Fast-failing scenarios

**Medium timeout (30-60s):**
- Standard API requests (default)
- Most race condition tests
- Normal operation

**Long timeout (120-300s):**
- Slow backend processing
- Large data transfers
- Complex calculations

### Example: Slow Endpoint Testing

```yaml
metadata:
  name: "Slow Processing Test"

config:
  host: "api.example.com"
  port: 443
  timeout: 120  # 2 minutes for slow endpoints

states:
  slow_process:
    description: "Test slow processing endpoint"
    request: |
      POST /api/heavy-computation HTTP/1.1
      Host: {{ config.host }}
      Content-Type: application/json
      
      {"operation": "complex_calculation"}
    
    logger:
      on_state_leave: |
        ✓ Completed in {{ response_time }}ms
        (Timeout set to {{ timeout }}s)
```

---

## All Available Extractors

TRECO provides 8 different extractors for parsing HTTP responses.

### 1. JSONPath Extractor (`jpath`)

Extract data from JSON responses using JSONPath expressions.

```yaml
extract:
  token:
    type: jpath
    pattern: "$.access_token"
  
  user_id:
    type: jpath
    pattern: "$.user.id"
  
  items:
    type: jpath
    pattern: "$.data[*].name"
  
  active_users:
    type: jpath
    pattern: "$.users[?(@.active==true)].username"
```

### 2. XPath Extractor (`xpath`)

Extract data from XML/HTML responses using XPath expressions.

```yaml
extract:
  csrf_token:
    type: xpath
    pattern: '//input[@name="csrf_token"]/@value'
  
  title:
    type: xpath
    pattern: '//h1[@class="title"]/text()'
  
  api_version:
    type: xpath
    pattern: '/response/version/text()'
```

### 3. Regex Extractor (`regex`)

Extract data using regular expressions.

```yaml
extract:
  session_id:
    type: regex
    pattern: "SESSION=([A-Z0-9]+)"
  
  email:
    type: regex
    pattern: "([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})"
  
  amount:
    type: regex
    pattern: "\\$([0-9,]+\\.[0-9]{2})"
```

### 4. Boundary Extractor (`boundary`)

Extract text between delimiters.

```yaml
extract:
  content:
    type: boundary
    pattern: "START:END"
  
  json_data:
    type: boundary
    pattern: "```json:```"
  
  script:
    type: boundary
    pattern: "<script>:</script>"
```

### 5. Header Extractor (`header`)

Extract HTTP response headers.

```yaml
extract:
  rate_limit:
    type: header
    pattern: "X-RateLimit-Remaining"
  
  content_type:
    type: header
    pattern: "Content-Type"
  
  request_id:
    type: header
    pattern: "X-Request-ID"
```

### 6. Cookie Extractor (`cookie`)

Extract cookie values from Set-Cookie headers.

```yaml
extract:
  session:
    type: cookie
    pattern: "session"
  
  auth_token:
    type: cookie
    pattern: "auth_token"
  
  tracking:
    type: cookie
    pattern: "_ga"
```

### 7. JWT Extractor (`jwt`)

Decode and extract data from JSON Web Tokens (JWT). Perfect for extracting user information, checking token expiration, and validating JWT structure in API security testing.

**Extract Specific Claims:**

```yaml
extract:
  user_id:
    type: jwt
    source: "{{ access_token }}"
    claim: sub
  
  user_role:
    type: jwt
    source: "{{ access_token }}"
    claim: role
  
  email:
    type: jwt
    source: "{{ access_token }}"
    claim: email
```

**Extract JWT Parts:**

```yaml
extract:
  # Get entire payload
  jwt_payload:
    type: jwt
    source: "{{ token }}"
    part: payload
  
  # Get header (algorithm, type, etc.)
  jwt_header:
    type: jwt
    source: "{{ token }}"
    part: header
  
  # Get signature
  jwt_signature:
    type: jwt
    source: "{{ token }}"
    part: signature
```

**Validation Checks:**

```yaml
extract:
  # Check if token has expired
  is_expired:
    type: jwt
    source: "{{ token }}"
    check: expired
  
  # Get algorithm (HS256, RS256, etc.)
  algorithm:
    type: jwt
    source: "{{ token }}"
    check: algorithm
  
  # Check if structure is valid
  is_valid:
    type: jwt
    source: "{{ token }}"
    check: valid
```

**With Signature Verification:**

```yaml
extract:
  verified_payload:
    type: jwt
    source: "{{ token }}"
    part: payload
    verify: true
    secret: "{{ jwt_secret }}"
    algorithms: ["HS256", "HS512"]
```

**Common JWT Claims:**
- `sub` - Subject (usually user ID)
- `iss` - Issuer
- `aud` - Audience
- `exp` - Expiration timestamp
- `nbf` - Not Before timestamp
- `iat` - Issued At timestamp
- `jti` - JWT ID
- `role`, `roles` - User role(s)
- `permissions` - User permissions
- `email`, `username` - User identity

**Security Testing Example:**

```yaml
states:
  analyze_jwt:
    request: |
      GET /api/protected HTTP/1.1
      Authorization: Bearer {{ token }}
    
    extract:
      algorithm:
        type: jwt
        source: "{{ token }}"
        check: algorithm
      
      is_expired:
        type: jwt
        source: "{{ token }}"
        check: expired
      
      user_role:
        type: jwt
        source: "{{ token }}"
        claim: role
    
    logger:
      on_state_leave: |
        {% if algorithm == 'none' %}
          🚨 CRITICAL: JWT uses 'none' algorithm!
        {% elif algorithm == 'HS256' %}
          ⚠ WARNING: JWT uses symmetric algorithm
        {% endif %}
        {% if is_expired %}
          🚨 Token is expired but still accepted!
        {% endif %}
```

### 8. Default Values

All extractors support default values:

```yaml
extract:
  optional_field:
    type: jpath
    pattern: "$.optional.field"
    default: "not_found"  # Used if extraction fails
  
  optional_claim:
    type: jwt
    source: "{{ token }}"
    claim: optional_claim
    default: "no_claim"  # Used if claim not found
```

---

## All Template Filters

TRECO provides 7 custom Jinja2 filters for dynamic request generation.

### 1. TOTP Filter (`totp`)

Generate Time-Based One-Time Password codes.

```yaml
# Generate TOTP code
{{ totp('JBSWY3DPEHPK3PXP') }}

# Use in request
request: |
  POST /api/verify HTTP/1.1
  Content-Type: application/json
  
  {"code": "{{ totp(totp_secret) }}"}
```

**Algorithm:** RFC 6238 TOTP (30-second intervals)

### 2. MD5 Filter (`md5`)

Generate MD5 hash of string.

```yaml
{{ password | md5 }}

# Example
request: |
  POST /api/login HTTP/1.1
  
  {"password_hash": "{{ password | md5 }}"}
```

### 3. SHA1 Filter (`sha1`)

Generate SHA1 hash of string.

```yaml
{{ data | sha1 }}

# Example
request: |
  POST /api/authenticate HTTP/1.1
  
  {"signature": "{{ api_key | sha1 }}"}
```

### 4. SHA256 Filter (`sha256`)

Generate SHA256 hash of string.

```yaml
{{ sensitive_data | sha256 }}

# Example
request: |
  POST /api/secure HTTP/1.1
  
  {"hash": "{{ password | sha256 }}"}
```

### 5. Environment Variable Filter (`env`)

Get environment variable value.

```yaml
# Get environment variable
{{ env('API_KEY') }}

# With default value
{{ env('API_KEY', 'default-key') }}

# Example
request: |
  GET /api/data HTTP/1.1
  X-API-Key: {{ env('API_KEY') }}
```

### 6. CLI Argument Filter (`argv`)

Get command-line argument value.

```yaml
# Get CLI argument
{{ argv('user') }}

# With default value
{{ argv('user', 'guest') }}

# Example
request: |
  POST /api/login HTTP/1.1
  
  {"username": "{{ argv('user', 'testuser') }}"}
```

Use with:

```bash
treco attack.yaml --user alice --password secret
```

### 7. Average Filter (`average`)

Calculate average of numeric list.

```yaml
{{ [10, 20, 30, 40] | average }}  # Returns: 25

# Example
logger:
  on_state_leave: |
    Average response time: {{ response_times | average }}ms
```

### Chaining Filters

Filters can be chained:

```yaml
# Hash password with SHA256, then get first 16 chars
{{ password | sha256 | truncate(16) }}

# Get env var and hash it
{{ env('SECRET') | md5 }}

# Average then format
{{ values | average | round(2) }}
```

---

## Complete Configuration Example

Here's a complete example using multiple advanced features:

```yaml
metadata:
  name: "Advanced Security Test"
  version: "2.0"
  author: "Security Team"
  vulnerability: "CWE-362"

config:
  host: "api.example.com"
  port: 443
  timeout: 90
  reuse_connection: false
  tls:
    enabled: true
    verify_cert: true
  http:
    follow_redirects: false
  proxy:
    host: "proxy.company.com"
    port: 8080
    type: "http"
    auth:
      username: "{{ env('PROXY_USER') }}"
      password: "{{ env('PROXY_PASS') }}"

entrypoint:
  state: authenticate
  input:
    username: "{{ argv('user', 'testuser') }}"
    password: "{{ argv('pass', 'testpass') }}"

states:
  authenticate:
    description: "Authenticate with TOTP"
    request: |
      POST /api/auth HTTP/1.1
      Host: {{ config.host }}
      Content-Type: application/json
      
      {
        "username": "{{ username }}",
        "password": "{{ password | sha256 }}",
        "totp": "{{ totp(env('TOTP_SECRET')) }}"
      }
    
    extract:
      token:
        type: jpath
        pattern: "$.access_token"
      rate_limit:
        type: header
        pattern: "X-RateLimit-Remaining"
      session:
        type: cookie
        pattern: "session"
    
    logger:
      on_state_leave: |
        ✓ Authenticated successfully
        Token: {{ token[:20] }}...
        Rate limit: {{ rate_limit }}
        Session: {{ session }}
    
    next:
      - on_status: 200
        goto: race_attack
      - on_status: 401
        goto: end

  race_attack:
    description: "Race condition attack"
    request: |
      POST /api/redeem HTTP/1.1
      Host: {{ config.host }}
      Authorization: Bearer {{ authenticate.token }}
      Content-Type: application/json
      
      {"code": "PROMO100"}
    
    race:
      threads: 20
      sync_mechanism: barrier
      connection_strategy: preconnect
      reuse_connections: false
    
    extract:
      balance:
        type: jpath
        pattern: "$.balance"
        default: 0
    
    logger:
      on_state_leave: |
        Race completed
        Successful: {{ successful_requests }}
        Final balance: ${{ balance }}
    
    next:
      - on_status: 200
        goto: end

  end:
    description: "Test completed"
```

Run with:

```bash
export PROXY_USER="proxyuser"
export PROXY_PASS="proxypass"
export TOTP_SECRET="JBSWY3DPEHPK3PXP"

treco advanced-test.yaml --user alice --pass secret123
```

---

## Performance Considerations

When using advanced features, keep these performance impacts in mind:

| Feature | Performance Impact | Race Window Impact |
|---------|-------------------|-------------------|
| **Proxy** | High (+50-200ms) | Significant |
| **HTTP/2** | Medium (+10-50ms) | Moderate |
| **Connection Reuse** | Low (-5-10ms) | Minimal |
| **Follow Redirects** | Medium (+10-100ms per redirect) | Moderate |
| **Long Timeouts** | None (unless triggered) | None |
| **Complex Extractors** | Low (+1-5ms) | Minimal |
| **Template Filters** | Very Low (<1ms) | Negligible |

**Optimization priorities for race conditions:**

1. Disable proxy if possible
2. Use HTTP/1.1 with preconnect
3. Disable redirect following if not needed
4. Use simple extractors
5. Keep timeout reasonable (30-60s)

---

## Troubleshooting Advanced Features

### Proxy Connection Failed

**Problem:** Cannot connect through proxy

**Solution:**
```yaml
# Verify proxy settings
config:
  proxy:
    host: "correct-proxy.com"  # Check hostname
    port: 8080                 # Check port
    type: "http"               # Verify type
    auth:                      # Check credentials
      username: "{{ env('PROXY_USER') }}"
      password: "{{ env('PROXY_PASS') }}"
```

```bash
# Test proxy connectivity
curl -x http://proxy.example.com:8080 https://api.example.com

# Verify environment variables
echo $PROXY_USER
echo $PROXY_PASS
```

### HTTP/2 Not Working

**Problem:** HTTP/2 connection fails

**Solution:**
- Verify server supports HTTP/2
- Enable TLS (required for HTTP/2)
- Use multiplexed strategy

```yaml
config:
  tls:
    enabled: true  # Required!

race:
  connection_strategy: multiplexed  # Uses HTTP/2
```

### Extractor Not Working

**Problem:** Extractor returns no value

**Solution:**
```yaml
# Add default value
extract:
  field:
    type: jpath
    pattern: "$.field"
    default: "not_found"

# Debug with logger
logger:
  on_state_leave: |
    Response: {{ response_body }}
    Extracted: {{ field }}
```

### TOTP Always Invalid

**Problem:** TOTP codes don't work

**Solution:**
- Verify TOTP secret is correct (base32 encoded)
- Check system time is synchronized
- Verify 30-second interval alignment

```bash
# Check system time
date
timedatectl

# Synchronize time
sudo ntpdate pool.ntp.org
```

---

## See Also

- [README.md](README.md) - Main documentation
- [Configuration Reference](docs/source/configuration.rst) - Complete YAML reference
- [Examples](docs/source/examples.rst) - Working examples
- [Best Practices](docs/source/best-practices.rst) - Performance optimization