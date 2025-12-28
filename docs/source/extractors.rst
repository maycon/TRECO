Data Extractors
===============

TRECO provides a powerful, plugin-based extraction system for parsing HTTP responses and extracting data into variables.

Overview
--------

Extractors allow you to capture data from HTTP responses for use in subsequent requests. The extraction system supports multiple formats and uses a plugin architecture for extensibility.

Basic Syntax
~~~~~~~~~~~~

.. code-block:: yaml

   extract:
     variable_name:
       type: extractor_type
       pattern: "extraction_pattern"

All extracted variables are stored in the execution context and can be accessed in later states using the format ``{{ state_name.variable_name }}``.

Available Extractors
--------------------

JSONPath (jpath)
~~~~~~~~~~~~~~~~

Extract data from JSON responses using JSONPath expressions.

**Type names:** ``jpath``, ``jsonpath``, ``json_path``

**Syntax:**

.. code-block:: yaml

   extract:
     token:
       type: jpath
       pattern: "$.access_token"

**Common Patterns:**

.. code-block:: yaml

   # Root level field
   pattern: "$.field_name"
   
   # Nested field
   pattern: "$.user.profile.email"
   
   # Array element
   pattern: "$.items[0].id"
   
   # All elements in array
   pattern: "$.items[*].id"
   
   # Filter by condition
   pattern: "$.users[?(@.active==true)].name"

**Example:**

.. code-block:: yaml

   states:
     login:
       request: |
         POST /api/login HTTP/1.1
         Content-Type: application/json
         
         {"username": "user", "password": "pass"}
       
       extract:
         access_token:
           type: jpath
           pattern: "$.access_token"
         refresh_token:
           type: jpath
           pattern: "$.refresh_token"
         user_id:
           type: jpath
           pattern: "$.user.id"

XPath (xpath)
~~~~~~~~~~~~~

Extract data from XML/HTML responses using XPath expressions.

**Type names:** ``xpath``, ``xml_path``, ``html_path``

**Syntax:**

.. code-block:: yaml

   extract:
     csrf_token:
       type: xpath
       pattern: '//input[@name="csrf"]/@value'

**Common Patterns:**

.. code-block:: yaml

   # Element by ID
   pattern: '//*[@id="element-id"]'
   
   # Input value by name
   pattern: '//input[@name="field_name"]/@value'
   
   # Link href
   pattern: '//a[@class="link"]/@href'
   
   # Text content
   pattern: '//div[@class="message"]/text()'
   
   # Meta tag content
   pattern: '//meta[@name="csrf-token"]/@content'

**Example:**

.. code-block:: yaml

   states:
     get_form:
       request: |
         GET /form HTTP/1.1
         Host: {{ config.host }}
       
       extract:
         csrf_token:
           type: xpath
           pattern: '//input[@name="csrf_token"]/@value'
         form_action:
           type: html_path
           pattern: '//form/@action'

Regex (regex)
~~~~~~~~~~~~~

Extract data using regular expressions with capture groups.

**Type names:** ``regex``, ``re``, ``regexp``

**Syntax:**

.. code-block:: yaml

   extract:
     session_id:
       type: regex
       pattern: "SESSION=([A-Z0-9]+)"

The first capture group ``()`` is returned as the extracted value.

**Common Patterns:**

.. code-block:: yaml

   # Cookie value
   pattern: "SESSIONID=([a-zA-Z0-9]+)"
   
   # Bearer token
   pattern: 'Bearer ([a-zA-Z0-9._-]+)'
   
   # UUID
   pattern: '([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
   
   # Number
   pattern: 'balance["\s:]+(\d+\.?\d*)'
   
   # Between quotes
   pattern: '"token":"([^"]+)"'

**Example:**

.. code-block:: yaml

   states:
     get_session:
       request: |
         GET /api/session HTTP/1.1
         Host: {{ config.host }}
       
       extract:
         session_id:
           type: regex
           pattern: 'session_id=([a-f0-9]{32})'
         auth_code:
           type: re
           pattern: 'code=([A-Z0-9]+)'

Boundary (boundary)
~~~~~~~~~~~~~~~~~~~

Extract data between left and right delimiters. Simpler alternative to regex for common patterns.

**Type names:** ``boundary``, ``between``, ``delimited``

**Syntax:**

.. code-block:: yaml

   extract:
     token:
       type: boundary
       pattern: '"token":"|||"'

The pattern uses ``|||`` as a separator between the left and right boundaries.

**Special Markers:**

* ``^`` - Beginning of line (for left boundary)
* ``$`` - End of line (for right boundary)

**Common Patterns:**

.. code-block:: yaml

   # Between delimiters
   pattern: '"token":"|||"'
   
   # Until end of line
   pattern: 'Authorization: |||$'
   
   # From beginning of line
   pattern: '^|||: value'
   
   # HTML attribute value
   pattern: 'value="|||"'
   
   # JSON field value
   pattern: '"balance":|||,'

**Example:**

.. code-block:: yaml

   states:
     parse_response:
       request: |
         GET /api/data HTTP/1.1
         Host: {{ config.host }}
       
       extract:
         api_key:
           type: boundary
           pattern: '"api_key":"|||"'
         auth_header:
           type: between
           pattern: 'X-Auth-Token: |||$'

Header (header)
~~~~~~~~~~~~~~~

Extract values from HTTP response headers (case-insensitive).

**Type names:** ``header``, ``headers``, ``http_header``

**Syntax:**

.. code-block:: yaml

   extract:
     request_id:
       type: header
       pattern: "X-Request-Id"

**Common Headers:**

.. code-block:: yaml

   # Custom auth header
   pattern: "X-Auth-Token"
   
   # Request ID
   pattern: "X-Request-Id"
   
   # Content type
   pattern: "Content-Type"
   
   # Location (for redirects)
   pattern: "Location"
   
   # Rate limit info
   pattern: "X-RateLimit-Remaining"

**Example:**

.. code-block:: yaml

   states:
     get_auth:
       request: |
         POST /api/auth HTTP/1.1
         Host: {{ config.host }}
       
       extract:
         auth_token:
           type: header
           pattern: "X-Auth-Token"
         rate_limit:
           type: headers
           pattern: "X-RateLimit-Remaining"

Cookie (cookie)
~~~~~~~~~~~~~~~

Extract cookie values from Set-Cookie response headers.

**Type names:** ``cookie``, ``cookies``, ``set_cookie``, ``set-cookie``

**Syntax:**

.. code-block:: yaml

   extract:
     session:
       type: cookie
       pattern: "session_id"

**Example:**

.. code-block:: yaml

   states:
     login:
       request: |
         POST /login HTTP/1.1
         Host: {{ config.host }}
         Content-Type: application/json
         
         {"username": "user", "password": "pass"}
       
       extract:
         session_id:
           type: cookie
           pattern: "SESSIONID"
         csrf_cookie:
           type: set-cookie
           pattern: "csrf_token"
         tracking_id:
           type: cookies
           pattern: "_tracking"

JWT (jwt)
~~~~~~~~~

Decode and extract data from JSON Web Tokens (JWT). Perfect for extracting user information, checking token expiration, and validating JWT structure in API security testing.

**Type names:** ``jwt``

**Extract Specific Claims:**

.. code-block:: yaml

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

**Extract JWT Parts:**

.. code-block:: yaml

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

**Validation Checks:**

.. code-block:: yaml

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

**With Signature Verification:**

.. code-block:: yaml

   extract:
     verified_payload:
       type: jwt
       source: "{{ token }}"
       part: payload
       verify: true
       secret: "{{ jwt_secret }}"
       algorithms: ["HS256", "HS512"]

**Common JWT Claims:**

- ``sub`` - Subject (usually user ID)
- ``iss`` - Issuer  
- ``aud`` - Audience
- ``exp`` - Expiration timestamp
- ``nbf`` - Not Before timestamp
- ``iat`` - Issued At timestamp
- ``jti`` - JWT ID
- ``role``, ``roles`` - User role(s)
- ``permissions`` - User permissions
- ``email``, ``username`` - User identity

**Security Testing Example:**

.. code-block:: yaml

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

Extractor Summary
-----------------

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Type
     - Aliases
     - Best For
   * - ``jpath``
     - ``jsonpath``, ``json_path``
     - JSON API responses
   * - ``xpath``
     - ``xml_path``, ``html_path``
     - HTML forms, XML responses
   * - ``regex``
     - ``re``, ``regexp``
     - Complex patterns, mixed content
   * - ``boundary``
     - ``between``, ``delimited``
     - Simple text extraction
   * - ``header``
     - ``headers``, ``http_header``
     - Response headers
   * - ``cookie``
     - ``cookies``, ``set_cookie``, ``set-cookie``
     - Session cookies, tokens
   * - ``jwt``
     - 
     - JWT token analysis, claims extraction

Using Extracted Variables
-------------------------

Extracted variables are stored in the context and can be accessed in templates:

.. code-block:: yaml

   states:
     login:
       extract:
         token:
           type: jpath
           pattern: "$.token"
     
     use_token:
       request: |
         GET /api/data HTTP/1.1
         Authorization: Bearer {{ login.token }}

Variable Naming
~~~~~~~~~~~~~~~

* Use lowercase with underscores: ``user_id``, ``auth_token``
* Avoid reserved words: ``config``, ``thread``, ``context``
* Be descriptive: ``access_token`` not ``t``

Accessing Variables
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # From previous state
   {{ state_name.variable_name }}
   
   # From current state (in logger)
   {{ variable_name }}
   
   # From config
   {{ config.host }}
   
   # Thread info (in race states)
   {{ thread.id }}
   {{ thread.count }}

Creating Custom Extractors
--------------------------

You can create custom extractors by implementing the ``BaseExtractor`` interface:

.. code-block:: python

   from treco.http.extractor.base import BaseExtractor, register_extractor
   
   @register_extractor('custom', aliases=['my_extractor'])
   class CustomExtractor(BaseExtractor):
       """Custom extractor for specific data formats."""
       
       def extract(self, response, pattern):
           """
           Extract data from response.
           
           Args:
               response: ResponseProtocol object
               pattern: Extraction pattern string
           
           Returns:
               Extracted value or None if not found
           """
           # Your extraction logic here
           content = response.text
           # ... process content using pattern ...
           return extracted_value

The ``@register_extractor`` decorator automatically registers your extractor with the specified type name and aliases.

Best Practices
--------------

1. **Choose the right extractor**: Use JSONPath for JSON, XPath for HTML, regex for complex patterns
2. **Be specific with patterns**: Avoid overly broad patterns that might match wrong data
3. **Handle missing data**: Extractors return ``None`` if pattern doesn't match
4. **Test patterns**: Verify patterns work with actual response data
5. **Use aliases**: Different teams may prefer different naming conventions

Troubleshooting
---------------

**Pattern not matching:**

1. Check the response content type
2. Verify the pattern syntax
3. Use verbose mode to see actual response
4. Test pattern with sample data

**Wrong data extracted:**

1. Make patterns more specific
2. Use capture groups correctly in regex
3. Check for multiple matches (first match is used)

**Extractor type not found:**

1. Check spelling and aliases
2. Ensure you're using a valid type name
3. Custom extractors must be imported before use

See Also
--------

* :doc:`configuration` - YAML configuration reference
* :doc:`templates` - Template syntax and filters
* :doc:`examples` - Real-world attack examples
