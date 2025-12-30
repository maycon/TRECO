# Multi-Endpoint Race Condition

> **PortSwigger Lab:** [Multi-endpoint race conditions](https://portswigger.net/web-security/race-conditions/lab-race-conditions-multi-endpoint)  
> **Difficulty:** Practitioner  
> **Objective:** Purchase the $1337 Lightweight L33t Leather Jacket with only $100 store credit

![Lab Screenshot](screenshot.png)

---

## 📋 Overview

This lab demonstrates a **Time-of-check Time-of-use (TOCTOU)** vulnerability in an e-commerce checkout flow. By racing requests to two different endpoints that operate on shared cart state, we can purchase an expensive item for a fraction of its price.

### The Vulnerability

The checkout process has a critical flaw:

```python
def checkout(session):
    cart = get_cart(session)           # 1️⃣ Read cart state
    total = calculate_price(cart)      # 2️⃣ Calculate from snapshot
    validate_payment(balance, total)   # 3️⃣ Check if affordable
    # [RACE WINDOW] ⚡ Cart can be modified here!
    finalize_order(cart)               # 4️⃣ Process CURRENT cart (not snapshot!)
```

**The Problem:** Steps 1-3 use a snapshot, but step 4 uses the current cart state. If the cart is modified between validation and finalization, we can bypass the price check.

---

## 🎯 Attack Strategy

### High-Level Flow

```
1. Login as wiener (credentials: wiener:peter)
2. Add $10 gift card to cart (bait item)
3. Extract CSRF token from cart page
4. Race two requests simultaneously:
   ├─ Thread 1: POST /cart → Add $1337 jacket
   └─ Thread 2: POST /cart/checkout → Process order
5. Result: Purchase both items for $10! 🎉
```

### Attack Timeline

```
┌──────────────────────────────────────────────────────┐
│ T=0ms                                                │
│ ├─ Cart state: [$10 gift card]                       │
│ └─ Balance: $100                                     │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│ T=0ms: Barrier releases both threads                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                      │
│  Thread 1                   Thread 2                 │
│  POST /cart                 POST /cart/checkout      │
│  ↓                          ↓                        │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│ T=1ms: Checkout reads cart                           │
│        Cart: [$10 gift card]                         │
│        Price: $10 ✓                                  │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│ T=2ms: Checkout validates payment                    │
│        $10 ≤ $100 balance ✓                          │
│        [RACE WINDOW OPEN] ⚡                          │
└──────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────┐
│ T=2ms: POST /cart adds jacket                        │
│        Cart: [$10 gift card, $1337 jacket]           │
└──────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│ T=3ms: Checkout finalizes order                      │
│        Processes CURRENT cart: [$10 + $1337]         │
│        But only deducts validated $10! ✓             │
└──────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Final State                                                 │
│ ├─ Cart: Empty                                              │
│ ├─ Balance: $90                                             │
│ └─ Orders: [$10 gift card, $1337 jacket] ← Both purchased!  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- TRECO installed
- PortSwigger Academy account
- Lab started and URL obtained

### Usage

```bash
# 1. Set your lab URL
export LAB_HOST="YOUR-LAB-ID.web-security-academy.net"

# 2. Run the attack
treco attack.yaml

# 3. If first attempt fails, try again (timing sensitive)
for i in {1..5}; do 
  treco attack.yaml && break
  sleep 1
done
```

### Expected Output

```
🔐 Session: 3x7YzK2mP5qR8w...
🎫 CSRF: eF7vT4nM6jL9sD...
✅ Logged in as wiener
🎁 Gift card added to cart ($10)
🎫 Checkout CSRF: ghi789rst345...
🎯 Ready to race: Add jacket + Checkout simultaneously

🚀 [Thread 1] POST /cart
🚀 [Thread 2] POST /cart/checkout

✅ [Thread 1] Success: /cart (45ms)
✅ [Thread 2] Success: /cart/checkout (48ms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Multi-Endpoint Race Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ EXPLOITED! Cart is empty - jacket was purchased!
   → Check "My Account" for order confirmation
   → Lab should be solved! 🏆
```

---

## 📊 Real-World Impact

### Where This Vulnerability Exists

**E-commerce Platforms** ⚠️ (Common)
- Cart modification during checkout
- Price changes after validation
- Inventory deduction races
- Discount/coupon application bugs

**Booking Systems** ⚠️ (Common)
- Seat/room availability during reservation
- Double-booking vulnerabilities
- Price lock bypasses
- Capacity limit overruns

**Financial Systems** 🔴 (Critical)
- Balance verification during transfers
- Concurrent withdrawal races
- Payment processing gaps
- Credit limit bypasses

---

## 🔗 Related Labs

### PortSwigger Race Conditions Series

1. ✅ [Limit overrun](../limit-overrun/) - Basic single-endpoint race
2. ✅ [Rate limit bypass](../rate-limit-bypass/) - Bypassing rate limiters
3. ✅ [Time-sensitive vulnerabilities](../time-sensitive/) - Sub-microsecond timing
4. ✅ **Multi-endpoint race** ← You are here
5. ⬜ [Single-endpoint race](../single-endpoint-race/) - Session state races
6. ⬜ [Partial construction](../partial-construction/) - Hidden multi-step



---

## 📖 Additional Resources

### PortSwigger
- [Lab URL](https://portswigger.net/web-security/race-conditions/lab-race-conditions-multi-endpoint)
- [Race Conditions Guide](https://portswigger.net/web-security/race-conditions)
- [Research Paper](https://portswigger.net/research/smashing-the-state-machine)

### TRECO Documentation
- [Configuration Reference](../../../docs/source/configuration.rst)
- [Race Synchronization](../../../docs/source/synchronization.rst)
- [Input Distribution](../../../docs/source/input-sources.rst)
- [Multi-Endpoint Guide](../../../docs/source/multi-endpoint.rst)

### Security Resources
- [TOCTOU on Wikipedia](https://en.wikipedia.org/wiki/Time-of-check_to_time-of-use)
- [OWASP: Race Conditions](https://owasp.org/www-community/vulnerabilities/Race_Conditions)
- [CWE-367: TOCTOU](https://cwe.mitre.org/data/definitions/367.html)
- [Database Isolation Levels](https://en.wikipedia.org/wiki/Isolation_(database_systems))

---

## 🤝 Contributing

Found a better approach? Improved the attack? Submit a PR!

```bash
# 1. Fork the repository
# 2. Create feature branch
git checkout -b improve/multi-endpoint-lab

# 3. Make your changes
# 4. Test against the lab
export LAB_HOST="..."
treco attack.yaml

# 5. Submit PR
gh pr create --title "Improve multi-endpoint lab" --fill
```

---

## 📄 License

This example is part of the TRECO project and is licensed under the MIT License.

---

## ⚠️ Legal Disclaimer

**Use these techniques ethically and responsibly.**

- ✅ Test on PortSwigger Academy labs
- ✅ Test on systems you own or have permission to test
- ✅ Use for security research and education
- ❌ Never attack systems without authorization
- ❌ Don't use for financial gain through exploitation

**Remember:** Unauthorized access to computer systems is illegal in most jurisdictions.

---

**Happy Hacking! 🎯**

*Last updated: 2025-12-30*