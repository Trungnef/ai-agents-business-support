"""Security-related tools for masking and audit logging."""

from datetime import datetime
import json
from typing import Any, Optional
import structlog

from src.security.pii_masker import PIIMasker


# Configure structured logger
logger = structlog.get_logger(__name__)


def mask_sensitive_data(text: str) -> str:
    """
    Mask all sensitive PII in the given text.
    
    Detects and masks:
    - Credit card numbers
    - Email addresses
    - Phone numbers
    - SSN patterns
    - Internal IDs
    
    Args:
        text: Text potentially containing PII
        
    Returns:
        Text with PII masked
    """
    return PIIMasker.mask_all(text)


def audit_log_event(
    event_type: str,
    payload: dict,
    session_id: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> dict:
    """
    Log an audit event for compliance tracking.
    
    Events are logged with structured data for later analysis.
    Sensitive data in the payload is automatically masked.
    
    Args:
        event_type: Type of event (e.g., "tool_call", "data_access", "response_sent")
        payload: Event-specific data
        session_id: Optional session identifier
        customer_email: Optional customer email (will be masked in logs)
        
    Returns:
        The logged event record
    """
    # Mask any PII in the payload
    safe_payload = _mask_payload(payload)
    
    # Create audit record
    audit_record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "session_id": session_id,
        "customer_email_masked": PIIMasker.mask_email(customer_email) if customer_email else None,
        "payload": safe_payload,
    }
    
    # Log the event
    logger.info(
        "audit_event",
        event_type=event_type,
        session_id=session_id,
        **safe_payload
    )
    
    return audit_record


def _mask_payload(payload: dict) -> dict:
    """Recursively mask sensitive data in a payload dictionary."""
    if not isinstance(payload, dict):
        return payload
    
    safe = {}
    sensitive_keys = {
        "email", "phone", "card_number", "ssn", "password",
        "credit_card", "customer_id", "internal_id", "api_key"
    }
    
    for key, value in payload.items():
        if key.lower() in sensitive_keys:
            if isinstance(value, str):
                safe[key] = PIIMasker.mask_all(value)
            else:
                safe[key] = "[REDACTED]"
        elif isinstance(value, dict):
            safe[key] = _mask_payload(value)
        elif isinstance(value, str):
            # Check if value looks like it contains PII
            safe[key] = PIIMasker.mask_all(value)
        else:
            safe[key] = value
    
    return safe


def validate_no_pii_leak(response_text: str) -> tuple[bool, list[str]]:
    """
    Validate that a response doesn't contain leaked PII.
    
    Args:
        response_text: The text to validate
        
    Returns:
        Tuple of (is_safe, list of detected issues)
    """
    issues = []
    
    # Check for unmasked credit cards
    if PIIMasker._has_credit_card(response_text):
        issues.append("Unmasked credit card number detected")
    
    # Check for internal IDs
    if "CUST0" in response_text:  # Our internal ID pattern
        issues.append("Internal customer ID exposed")
    
    # Check for obvious SSN patterns
    import re
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', response_text):
        issues.append("Possible SSN detected")
    
    # Check for full phone numbers (not masked)
    phone_pattern = r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    if re.search(phone_pattern, response_text):
        # Verify it's not already masked
        if "***-***-" not in response_text:
            issues.append("Unmasked phone number detected")
    
    return len(issues) == 0, issues
