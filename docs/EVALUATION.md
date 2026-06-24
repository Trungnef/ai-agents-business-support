# Evaluation Documentation

## Overview

This document describes the evaluation framework for the Multi-Agent Customer Support Assistant, including test cases, metrics, and results.

## Evaluation Framework

### Test Categories

1. **Intent Classification** - Accuracy of customer intent detection
2. **Priority Assignment** - Correct urgency level assignment
3. **Tool Selection** - Appropriate MCP tool usage
4. **Ticket Creation** - Proper escalation decisions
5. **Security Compliance** - PII protection and access control

### Test Cases (12 total)

| ID | Description | Intent | Priority | Security Test |
|----|-------------|--------|----------|---------------|
| TC001 | Basic order status inquiry | order_status | medium | - |
| TC002 | Refund request - eligible | refund_request | medium | - |
| TC003 | Damaged item - high priority | refund_request | high | - |
| TC004 | Double charge complaint | billing_issue | high | - |
| TC005 | Account access issue | account_access | medium | - |
| TC006 | Human escalation request | human_escalation | high | - |
| TC007 | Package not received | shipping_issue | high | - |
| TC008 | Unauthorized order access | order_status | medium | ✓ |
| TC009 | Legal threat - urgent | refund_request | urgent | - |
| TC010 | General inquiry | other | low | - |
| TC011 | Suspended account | order_status | medium | ✓ |
| TC012 | PII in customer message | billing_issue | high | ✓ |

### Running Evaluations

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_intent.py -v
pytest tests/test_security.py -v
pytest tests/test_orchestrator.py -v

# Run quick validation via CLI
python -m src.cli test all

# Run full evaluation suite
python -c "
import asyncio
from src.eval.evaluator import AgentEvaluator

evaluator = AgentEvaluator()
report = asyncio.run(evaluator.run_evaluation())
evaluator.print_report(report)
"
```

## Metrics

### Intent Classification Accuracy

Measures how accurately the system identifies customer intent.

**Target:** ≥85%

**Methodology:**
- Compare classified intent against expected intent for each test case
- Use both LLM-based and rule-based classification
- Rule-based fallback ensures baseline accuracy

### Priority Assignment Accuracy

Measures correct urgency level assignment.

**Target:** ≥80%

**Priority Levels:**
- `urgent` - Immediate attention required (legal threats, security issues)
- `high` - Time-sensitive, customer frustrated
- `medium` - Standard request
- `low` - General inquiry

### Tool Selection Accuracy

Measures whether the correct MCP tools are invoked.

**Target:** ≥90%

**Expected Tool Mapping:**
| Intent | Expected Tools |
|--------|----------------|
| order_status | get_order_details |
| refund_request | get_order_details, get_refund_policy |
| billing_issue | get_order_details, get_customer_profile |
| account_access | get_customer_profile |
| shipping_issue | get_order_details |
| human_escalation | (none - direct ticket) |

### Ticket Creation Accuracy

Measures appropriate escalation decisions.

**Target:** ≥95%

**Ticket Triggers:**
- All `urgent` and `high` priority requests
- All `human_escalation` intents
- All `billing_issue` and `account_access` intents

### Security Compliance

Measures enforcement of security constraints.

**Target:** 100% (zero tolerance for failures)

**Security Tests:**
1. Unauthorized order access → Denied
2. PII in responses → Masked
3. Internal IDs → Never exposed
4. Session lockout → After 3 failed verifications

## Security Test Details

### PII Masking Tests

```python
# Test cases for PII masking
test_cases = [
    ("4242424242424242", "**** **** **** 4242"),  # Credit card
    ("alice@example.com", "a****@example.com"),   # Email
    ("+1-555-0101", "***-***-0101"),              # Phone
    ("123-45-6789", "***-**-****"),               # SSN
    ("CUST001", "[INTERNAL]"),                    # Internal ID
]
```

### Access Control Tests

```python
# Test unauthorized access is denied
result = get_order_details("ORD-2024-001", "wrong@email.com")
assert result is None  # Should return nothing, not reveal order exists

# Test session lockout
context.failed_verification_attempts = 3
result = guardrail.check_data_access(...)
assert result.passed is False
assert context.is_locked is True
```

## Sample Test Results

```
=============================== test session starts ================================
platform win32 -- Python 3.11.0, pytest-8.0.0
collected 32 items

tests/test_intent.py::TestIntentClassification::test_order_status_intent PASSED
tests/test_intent.py::TestIntentClassification::test_refund_request_intent PASSED
tests/test_intent.py::TestIntentClassification::test_billing_issue_intent PASSED
tests/test_intent.py::TestIntentClassification::test_account_access_intent PASSED
tests/test_intent.py::TestIntentClassification::test_human_escalation_intent PASSED
tests/test_intent.py::TestIntentClassification::test_urgent_priority_detection PASSED
tests/test_intent.py::TestIntentClassification::test_entity_extraction_order_id PASSED
tests/test_intent.py::TestIntentClassification::test_entity_extraction_email PASSED
tests/test_intent.py::TestIntentClassification::test_classification_schema_valid PASSED

tests/test_security.py::TestPIIMasking::test_mask_credit_card_16_digit PASSED
tests/test_security.py::TestPIIMasking::test_mask_email PASSED
tests/test_security.py::TestPIIMasking::test_mask_phone_number PASSED
tests/test_security.py::TestAccessValidation::test_order_access_valid PASSED
tests/test_security.py::TestAccessValidation::test_order_access_wrong_email PASSED
tests/test_security.py::TestSecurityGuardrail::test_session_lockout PASSED
tests/test_security.py::TestOrderToolSecurity::test_order_details_unauthorized PASSED

tests/test_orchestrator.py::TestOrchestratorFlow::test_basic_order_status_flow PASSED
tests/test_orchestrator.py::TestOrchestratorFlow::test_unauthorized_order_access PASSED
tests/test_orchestrator.py::TestOrchestratorFlow::test_response_no_pii_leak PASSED

================================ 32 passed in 4.23s ================================
```

## Evaluation Report Format

```json
{
  "summary": {
    "total_tests": 12,
    "passed": 11,
    "failed": 1,
    "pass_rate": "91.7%"
  },
  "accuracy": {
    "intent": "91.7%",
    "priority": "83.3%",
    "tool_selection": "100.0%",
    "ticket_creation": "91.7%",
    "security": "100.0%"
  },
  "performance": {
    "avg_processing_time_ms": "450"
  }
}
```

## Known Limitations

1. **LLM Dependency** - Without GOOGLE_API_KEY, falls back to rule-based classification
2. **Priority Detection** - Subtle frustration may not always trigger `high` priority
3. **Entity Extraction** - Complex messages may miss some entities

## Continuous Improvement

To improve accuracy:
1. Add more test cases for edge cases
2. Fine-tune classification prompts
3. Expand rule-based patterns
4. Add customer feedback loop
