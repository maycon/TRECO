"""
Condition evaluator for multi-condition when blocks.

Evaluates complex boolean conditions for state transitions including:
- HTTP status code matching
- Jinja2 expressions
- Body content matching
- Header checks
- Response time analysis
"""

import re
import logging
from typing import Any, Dict, List, Optional

import httpx

from treco.template import TemplateEngine
from treco.models import ExecutionContext

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """
    Evaluates conditions in when blocks for state transitions.
    
    Supports multiple condition types:
    - status: Exact HTTP status code match
    - status_in: Match any of multiple status codes
    - status_range: Match status code within range (inclusive)
    - condition: Jinja2 expression evaluation
    - body_contains: Substring match in response body
    - body_not_contains: Negative substring match
    - body_matches: Regex match in response body
    - body_equals: Exact body match
    - header_exists: Check if header is present
    - header_not_exists: Check if header is absent
    - header_equals: Check header value matches exactly
    - header_contains: Check header value contains substring
    - header_matches: Check header value matches regex
    - header_compare: Numeric comparison on header value
    - response_time_ms: Response time comparison
    
    Example:
        evaluator = ConditionEvaluator(template_engine)
        
        when_conditions = [
            {"status": 200},
            {"condition": "{{ role == 'admin' }}"}
        ]
        
        if evaluator.evaluate_when_block(when_conditions, response, context):
            goto_state = "admin_panel"
    """
    
    def __init__(self, template_engine: TemplateEngine):
        """
        Initialize the condition evaluator.
        
        Args:
            template_engine: Template engine for Jinja2 expression evaluation
        """
        self.template_engine = template_engine
    
    def evaluate_when_block(
        self, 
        when_conditions: List[Dict[str, Any]], 
        response: httpx.Response,
        context: ExecutionContext,
        response_time_ms: Optional[float] = None
    ) -> bool:
        """
        Evaluate all conditions in a when block (AND logic).
        
        All conditions must be true for the block to match.
        
        Args:
            when_conditions: List of condition dictionaries
            response: HTTP response object
            context: Execution context with variables
            response_time_ms: Optional response time in milliseconds
            
        Returns:
            True if all conditions are satisfied, False otherwise
        """
        for condition in when_conditions:
            if not self.evaluate_single_condition(condition, response, context, response_time_ms):
                return False
        return True
    
    def evaluate_single_condition(
        self,
        condition: Dict[str, Any],
        response: httpx.Response,
        context: ExecutionContext,
        response_time_ms: Optional[float] = None
    ) -> bool:
        """
        Evaluate a single condition.
        
        Args:
            condition: Condition dictionary with one condition type
            response: HTTP response object
            context: Execution context
            response_time_ms: Optional response time in milliseconds
            
        Returns:
            True if condition is satisfied, False otherwise
        """
        # Status code conditions
        if "status" in condition:
            return self._check_status(condition["status"], response.status_code)
        
        if "status_in" in condition:
            return self._check_status_in(condition["status_in"], response.status_code)
        
        if "status_range" in condition:
            return self._check_status_range(condition["status_range"], response.status_code)
        
        # Jinja2 expression conditions
        if "condition" in condition:
            return self._evaluate_jinja_condition(condition["condition"], context)
        
        # Body content conditions
        if "body_contains" in condition:
            return self._check_body_contains(condition["body_contains"], response)
        
        if "body_not_contains" in condition:
            return not self._check_body_contains(condition["body_not_contains"], response)
        
        if "body_matches" in condition:
            return self._check_body_matches(condition["body_matches"], response)
        
        if "body_equals" in condition:
            return self._check_body_equals(condition["body_equals"], response)
        
        # Header conditions
        if "header_exists" in condition:
            return self._check_header_exists(condition["header_exists"], response)
        
        if "header_not_exists" in condition:
            return not self._check_header_exists(condition["header_not_exists"], response)
        
        if "header_equals" in condition:
            return self._check_header_equals(condition["header_equals"], response)
        
        if "header_contains" in condition:
            return self._check_header_contains(condition["header_contains"], response)
        
        if "header_matches" in condition:
            return self._check_header_matches(condition["header_matches"], response)
        
        if "header_compare" in condition:
            return self._check_header_compare(condition["header_compare"], response)
        
        # Response time conditions
        if "response_time_ms" in condition:
            if response_time_ms is None:
                logger.warning("response_time_ms condition used but no timing data available")
                return False
            return self._check_response_time(condition["response_time_ms"], response_time_ms)
        
        # Unknown condition type
        logger.warning(f"Unknown condition type: {condition}")
        return False
    
    def _check_status(self, expected: int, actual: int) -> bool:
        """Check if status code matches exactly."""
        return actual == expected
    
    def _check_status_in(self, expected_list: List[int], actual: int) -> bool:
        """Check if status code is in list."""
        return actual in expected_list
    
    def _check_status_range(self, range_spec: List[int], actual: int) -> bool:
        """Check if status code is within range (inclusive)."""
        if len(range_spec) != 2:
            logger.warning(f"Invalid status_range: {range_spec}, expected [low, high]")
            return False
        low, high = range_spec
        return low <= actual <= high
    
    def _evaluate_jinja_condition(self, expression: str, context: ExecutionContext) -> bool:
        """
        Evaluate a Jinja2 boolean expression.
        
        Args:
            expression: Jinja2 expression string (e.g., "{{ role == 'admin' }}")
            context: Execution context with variables
            
        Returns:
            Boolean result of expression evaluation
        """
        try:
            # Render the expression with context
            result = self.template_engine.render(expression, context.to_dict(), context)
            
            # Convert result to boolean
            # Handle string results like "True", "False", "true", "false"
            if isinstance(result, str):
                result = result.strip()
                if result.lower() == "true":
                    return True
                elif result.lower() == "false":
                    return False
                # Non-empty strings are truthy
                return bool(result)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error evaluating Jinja2 condition '{expression}': {e}")
            return False
    
    def _check_body_contains(self, substring: str, response: httpx.Response) -> bool:
        """Check if response body contains substring."""
        try:
            return substring in response.text
        except Exception as e:
            logger.error(f"Error checking body_contains: {e}")
            return False
    
    def _check_body_matches(self, pattern: str, response: httpx.Response) -> bool:
        """Check if response body matches regex pattern."""
        try:
            return re.search(pattern, response.text) is not None
        except Exception as e:
            logger.error(f"Error checking body_matches with pattern '{pattern}': {e}")
            return False
    
    def _check_body_equals(self, expected: str, response: httpx.Response) -> bool:
        """Check if response body equals expected value exactly."""
        try:
            return response.text == expected
        except Exception as e:
            logger.error(f"Error checking body_equals: {e}")
            return False
    
    def _check_header_exists(self, header_name: str, response: httpx.Response) -> bool:
        """Check if header exists in response."""
        return header_name.lower() in [h.lower() for h in response.headers.keys()]
    
    def _check_header_equals(self, header_spec: Dict[str, str], response: httpx.Response) -> bool:
        """
        Check if header value matches exactly.
        
        Args:
            header_spec: Dict with "name" and "value" keys
            response: HTTP response
            
        Returns:
            True if header exists and value matches
        """
        name = header_spec.get("name", "")
        expected_value = header_spec.get("value", "")
        
        actual_value = response.headers.get(name)
        if actual_value is None:
            return False
        
        return actual_value == expected_value
    
    def _check_header_contains(self, header_spec: Dict[str, str], response: httpx.Response) -> bool:
        """
        Check if header value contains substring.
        
        Args:
            header_spec: Dict with "name" and "value" keys
            response: HTTP response
            
        Returns:
            True if header exists and value contains substring
        """
        name = header_spec.get("name", "")
        substring = header_spec.get("value", "")
        
        actual_value = response.headers.get(name)
        if actual_value is None:
            return False
        
        return substring in actual_value
    
    def _check_header_matches(self, header_spec: Dict[str, str], response: httpx.Response) -> bool:
        """
        Check if header value matches regex pattern.
        
        Args:
            header_spec: Dict with "name" and "pattern" keys
            response: HTTP response
            
        Returns:
            True if header exists and value matches pattern
        """
        name = header_spec.get("name", "")
        pattern = header_spec.get("pattern", "")
        
        actual_value = response.headers.get(name)
        if actual_value is None:
            return False
        
        try:
            return re.search(pattern, actual_value) is not None
        except Exception as e:
            logger.error(f"Error checking header_matches with pattern '{pattern}': {e}")
            return False
    
    def _check_header_compare(self, header_spec: Dict[str, Any], response: httpx.Response) -> bool:
        """
        Perform numeric comparison on header value.
        
        Args:
            header_spec: Dict with "name", "operator", and "value" keys
            response: HTTP response
            
        Returns:
            True if header exists, is numeric, and comparison passes
        """
        name = header_spec.get("name", "")
        operator = header_spec.get("operator", "")
        expected_value = header_spec.get("value", 0)
        
        actual_value_str = response.headers.get(name)
        if actual_value_str is None:
            return False
        
        try:
            actual_value = float(actual_value_str)
            expected_value = float(expected_value)
            
            if operator == "<":
                return actual_value < expected_value
            elif operator == "<=":
                return actual_value <= expected_value
            elif operator == ">":
                return actual_value > expected_value
            elif operator == ">=":
                return actual_value >= expected_value
            elif operator == "==":
                return actual_value == expected_value
            elif operator == "!=":
                return actual_value != expected_value
            else:
                logger.warning(f"Unknown comparison operator: {operator}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Error comparing header '{name}' value: {e}")
            return False
    
    def _check_response_time(self, time_spec: Dict[str, Any], actual_time_ms: float) -> bool:
        """
        Check response time condition.
        
        Args:
            time_spec: Dict with "operator" and "value" keys
            actual_time_ms: Actual response time in milliseconds
            
        Returns:
            True if time comparison passes
        """
        operator = time_spec.get("operator", "")
        expected_ms = time_spec.get("value", 0)
        
        try:
            expected_ms = float(expected_ms)
            
            if operator == "<":
                return actual_time_ms < expected_ms
            elif operator == "<=":
                return actual_time_ms <= expected_ms
            elif operator == ">":
                return actual_time_ms > expected_ms
            elif operator == ">=":
                return actual_time_ms >= expected_ms
            elif operator == "==":
                return actual_time_ms == expected_ms
            elif operator == "!=":
                return actual_time_ms != expected_ms
            else:
                logger.warning(f"Unknown comparison operator: {operator}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Error comparing response time: {e}")
            return False
