"""
TOTP (Time-based One-Time Password) filter.

Generates TOTP tokens compatible with Google Authenticator and similar apps.
"""

import pyotp


def totp_filter(seed: str) -> str:
    """
    Generate a TOTP token from a seed.

    This filter creates a 6-digit TOTP code that changes every 30 seconds,
    compatible with RFC 6238 (TOTP: Time-Based One-Time Password Algorithm).

    Args:
        seed: Base32-encoded secret key (e.g., "JBSWY3DPEHPK3PXP")

    Returns:
        6-digit TOTP token as string (e.g., "123456")

    Example in template:
        # Function syntax
        {{ totp("JBSWY3DPEHPK3PXP") }}

        # With variable
        {{ totp(totp_seed) }}

        # In JSON request body
        {
          "username": "alice",
          "token": "{{ totp(seed) }}"
        }

    Note:
        The seed must be a valid Base32 string. Common seeds are provided
        by 2FA setup screens as QR codes or manual entry codes.
    """
    try:
        totp = pyotp.TOTP(seed)
        return totp.now()
    except Exception as e:
        # Return error placeholder instead of raising
        # This allows template rendering to continue
        return f"[TOTP_ERROR: {str(e)}]"
