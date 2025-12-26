"""
Simple unit tests for condition evaluator.

These tests don't require network access and validate core functionality.
"""

import httpx
from treco.state.conditions import ConditionEvaluator
from treco.template import TemplateEngine
from treco.models import ExecutionContext


def test_status_code_matching():
    """Test basic status code conditions."""
    evaluator = ConditionEvaluator(TemplateEngine())
    context = ExecutionContext()
    
    # Mock response with status 200
    response = httpx.Response(
        status_code=200,
        headers={},
        content=b"test content"
    )
    
    # Test exact status match
    conditions = [{"status": 200}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    # Test status mismatch
    conditions = [{"status": 404}]
    assert evaluator.evaluate_when_block(conditions, response, context) == False
    
    # Test status_in
    conditions = [{"status_in": [200, 201, 202]}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    # Test status_range
    conditions = [{"status_range": [200, 299]}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    print("✓ Status code matching tests passed")


def test_body_content_matching():
    """Test body content conditions."""
    evaluator = ConditionEvaluator(TemplateEngine())
    context = ExecutionContext()
    
    response = httpx.Response(
        status_code=200,
        headers={},
        content=b'{"status": "ok", "role": "admin"}'
    )
    
    # Test body_contains
    conditions = [{"body_contains": "admin"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    conditions = [{"body_contains": "user"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == False
    
    # Test body_not_contains
    conditions = [{"body_not_contains": "error"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    # Test body_matches (regex)
    conditions = [{"body_matches": r'"role":\s*"admin"'}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    print("✓ Body content matching tests passed")


def test_header_conditions():
    """Test header-based conditions."""
    evaluator = ConditionEvaluator(TemplateEngine())
    context = ExecutionContext()
    
    response = httpx.Response(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "X-Rate-Limit-Remaining": "42",
            "X-Custom-Header": "test-value"
        },
        content=b"test"
    )
    
    # Test header_exists
    conditions = [{"header_exists": "Content-Type"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    conditions = [{"header_exists": "X-Missing-Header"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == False
    
    # Test header_equals
    conditions = [{"header_equals": {"name": "Content-Type", "value": "application/json"}}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    # Test header_contains
    conditions = [{"header_contains": {"name": "Content-Type", "value": "json"}}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    # Test header_compare (numeric)
    conditions = [{"header_compare": {"name": "X-Rate-Limit-Remaining", "operator": ">", "value": 10}}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    conditions = [{"header_compare": {"name": "X-Rate-Limit-Remaining", "operator": "<", "value": 10}}]
    assert evaluator.evaluate_when_block(conditions, response, context) == False
    
    print("✓ Header condition tests passed")


def test_jinja2_conditions():
    """Test Jinja2 expression evaluation."""
    evaluator = ConditionEvaluator(TemplateEngine())
    context = ExecutionContext()
    
    # Set up context with variables
    context.set("role", "admin")
    context.set("balance", 1500)
    context.set("age", 25)
    
    response = httpx.Response(status_code=200, headers={}, content=b"")
    
    # Test simple equality
    conditions = [{"condition": "{{ role == 'admin' }}"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    conditions = [{"condition": "{{ role == 'user' }}"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == False
    
    # Test numeric comparison
    conditions = [{"condition": "{{ balance > 1000 }}"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    # Test complex expression
    conditions = [{"condition": "{{ age >= 18 and balance > 1000 }}"}]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    print("✓ Jinja2 condition tests passed")


def test_multiple_conditions_and_logic():
    """Test that multiple conditions use AND logic."""
    evaluator = ConditionEvaluator(TemplateEngine())
    context = ExecutionContext()
    context.set("role", "admin")
    
    response = httpx.Response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        content=b'{"status": "ok"}'
    )
    
    # All conditions true
    conditions = [
        {"status": 200},
        {"condition": "{{ role == 'admin' }}"},
        {"body_contains": "ok"},
        {"header_exists": "Content-Type"}
    ]
    assert evaluator.evaluate_when_block(conditions, response, context) == True
    
    # One condition false
    conditions = [
        {"status": 200},
        {"condition": "{{ role == 'admin' }}"},
        {"body_contains": "error"},  # This will be false
        {"header_exists": "Content-Type"}
    ]
    assert evaluator.evaluate_when_block(conditions, response, context) == False
    
    print("✓ Multiple condition AND logic tests passed")


if __name__ == "__main__":
    test_status_code_matching()
    test_body_content_matching()
    test_header_conditions()
    test_jinja2_conditions()
    test_multiple_conditions_and_logic()
    print("\n✅ All condition evaluator tests passed!")
