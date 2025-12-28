"""
JWT (JSON Web Token) extractor module.

Extracts and decodes JWT tokens, supporting claim extraction,
token validation, and signature verification.
"""

import jwt
import json
import base64
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone

from treco.http.extractor.base import BaseExtractor, ResponseProtocol, register_extractor

logger = logging.getLogger(__name__)


@register_extractor('jwt', aliases=['json_web_token'])
class JWTExtractor(BaseExtractor):
    """
    Extractor implementation for JWT (JSON Web Token) decoding and validation.
    
    Supports:
    - Extracting specific claims from JWT payload
    - Extracting header, payload, or signature parts
    - Validation checks (expired, algorithm, valid structure)
    - Signature verification with secrets (HMAC) or public keys (RSA)
    
    Registered as 'jwt' with alias 'json_web_token'.
    
    Example:
        # Extract a specific claim
        extract:
          user_id:
            type: jwt
            source: "{{ access_token }}"
            claim: sub
        
        # Extract entire payload
        extract:
          payload:
            type: jwt
            source: "{{ token }}"
            part: payload
        
        # Check if token is expired
        extract:
          is_expired:
            type: jwt
            source: "{{ token }}"
            check: expired
    """

    def extract(self, response: ResponseProtocol, pattern: Union[str, Dict[str, Any]], context: Optional[Dict] = None) -> Optional[Any]:
        """
        Extract data from a JWT token.
        
        Args:
            response: HTTP response object (not used for JWT extraction)
            pattern: Configuration dict with JWT extraction parameters
            context: Execution context containing variables (including the JWT token)
        
        Returns:
            Extracted value or None
            
        Raises:
            ValueError: If configuration is invalid or JWT is malformed
        """
        # Ensure pattern is a dict
        if isinstance(pattern, str):
            raise ValueError("JWT extractor requires a configuration dict, not a string pattern")
        
        if not isinstance(pattern, dict):
            raise ValueError(f"JWT extractor pattern must be a dict, got {type(pattern)}")
        
        # Validate configuration
        if not pattern.get('source'):
            raise ValueError("JWT extractor requires 'source' parameter")
        
        # Get token from context
        token = self._resolve_source(pattern.get('source'), context or {})
        
        if not token:
            default = pattern.get('default')
            logger.warning("[JWTExtractor] Token source not found or empty")
            return default
        
        try:
            # Determine what operation to perform
            claim = pattern.get('claim')
            part = pattern.get('part')
            check = pattern.get('check')
            verify = pattern.get('verify', False)
            
            # Decode the token
            if verify:
                # Verify signature
                secret = pattern.get('secret')
                if not secret:
                    raise ValueError("JWT verification requires 'secret' parameter")
                
                # Resolve secret from context if it's a template variable
                secret = self._resolve_source(secret, context or {})
                
                algorithms = pattern.get('algorithms', ['HS256'])
                decoded = jwt.decode(
                    token,
                    secret,
                    algorithms=algorithms
                )
            else:
                # Decode without verification
                decoded = jwt.decode(
                    token,
                    options={"verify_signature": False}
                )
            
            # Extract based on request type
            if check:
                return self._perform_check(token, decoded, check)
            elif claim:
                return decoded.get(claim, pattern.get('default'))
            elif part:
                return self._get_part(token, part)
            else:
                # Return full payload by default
                return decoded
                
        except jwt.ExpiredSignatureError:
            if check == 'expired':
                return True
            logger.error("[JWTExtractor] JWT token has expired")
            return self._get_default_value(pattern)
        except jwt.InvalidTokenError as e:
            if check == 'valid':
                return False
            logger.error(f"[JWTExtractor] Invalid JWT: {e}")
            return self._get_default_value(pattern)
    
    def _get_default_value(self, pattern: Dict[str, Any]) -> Any:
        """
        Get the default value from pattern configuration.
        
        Args:
            pattern: Pattern configuration dict
            
        Returns:
            Default value if specified, None otherwise
        """
        if 'default' in pattern:
            return pattern['default']
        return None
    
    def _resolve_source(self, source: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Resolve token source from context.
        
        Supports template variable syntax: {{ variable_name }}
        
        Args:
            source: Source string (may contain template variable)
            context: Execution context
            
        Returns:
            Resolved value or None
        """
        if not source:
            return None
        
        source = source.strip()
        
        # Check if it's a template variable
        if source.startswith('{{') and source.endswith('}}'):
            var_name = source[2:-2].strip()
            
            # Try direct lookup
            if var_name in context:
                return context[var_name]
            
            # Try nested lookup (e.g., "state.variable")
            parts = var_name.split('.')
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        break
                else:
                    value = None
                    break
            
            if value is not None:
                return str(value)
            
            logger.warning(f"[JWTExtractor] Variable '{var_name}' not found in context")
            return None
        
        # Not a template variable, return as-is (literal token)
        return source
    
    def _get_part(self, token: str, part: str) -> Any:
        """
        Get specific part of JWT (header, payload, or signature).
        
        Args:
            token: JWT token string
            part: Part to extract ('header', 'payload', or 'signature')
            
        Returns:
            Decoded part (dict for header/payload, string for signature)
            
        Raises:
            ValueError: If JWT structure is invalid or part is unknown
        """
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT structure: expected 3 parts separated by dots")
        
        if part == 'header':
            return json.loads(self._base64_decode(parts[0]))
        elif part == 'payload':
            return json.loads(self._base64_decode(parts[1]))
        elif part == 'signature':
            return parts[2]
        else:
            raise ValueError(f"Unknown JWT part: '{part}'. Expected 'header', 'payload', or 'signature'")
    
    def _base64_decode(self, data: str) -> str:
        """
        Decode base64url without padding.
        
        JWT uses base64url encoding (RFC 4648) which may omit padding.
        
        Args:
            data: Base64url-encoded string
            
        Returns:
            Decoded string
        """
        # Add padding if needed
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.urlsafe_b64decode(data).decode('utf-8')
    
    def _perform_check(self, token: str, decoded: Dict[str, Any], check: str) -> Any:
        """
        Perform validation checks on JWT.
        
        Args:
            token: JWT token string
            decoded: Decoded JWT payload
            check: Type of check ('expired', 'algorithm', 'valid')
            
        Returns:
            Check result (type varies by check type)
            
        Raises:
            ValueError: If check type is unknown
        """
        if check == 'expired':
            # Check if token has expired
            exp = decoded.get('exp')
            if not exp:
                # No expiration claim, token doesn't expire
                return False
            try:
                # exp is a Unix timestamp
                exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                return exp_datetime < now
            except (ValueError, OSError) as e:
                logger.warning(f"[JWTExtractor] Invalid exp timestamp: {e}")
                return False
        
        elif check == 'algorithm':
            # Get algorithm from header
            header = self._get_part(token, 'header')
            return header.get('alg')
        
        elif check == 'valid':
            # Token decoded successfully if we got here
            return True
        
        else:
            raise ValueError(f"Unknown check type: '{check}'. Expected 'expired', 'algorithm', or 'valid'")
