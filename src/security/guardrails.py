"""Security guardrails for the agent system."""

from typing import Any, Optional
from dataclasses import dataclass

from src.security.pii_masker import PIIMasker
from src.security.validators import validate_customer_access
from src.schemas.message import ConversationContext


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""
    
    passed: bool
    blocked_reason: Optional[str] = None
    modified_data: Optional[Any] = None
    warnings: list[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class SecurityGuardrail:
    """
    Security guardrail that validates data access and masks PII.
    
    This is the central security checkpoint for all data flowing
    through the agent system.
    """
    
    def __init__(self):
        self.masker = PIIMasker
    
    def check_data_access(
        self,
        resource_type: str,
        resource_id: str,
        requesting_email: Optional[str],
        context: Optional[ConversationContext] = None,
    ) -> GuardrailResult:
        """
        Validate that a data access request is authorized.
        
        Args:
            resource_type: Type of resource ("order", "customer", etc.)
            resource_id: ID of the resource being accessed
            requesting_email: Email of the requesting customer
            context: Current conversation context
            
        Returns:
            GuardrailResult indicating if access is allowed
        """
        # Check if session is locked
        if context and context.is_locked:
            return GuardrailResult(
                passed=False,
                blocked_reason="Session is locked due to security concerns. Please contact support directly."
            )
        
        # Check verification attempts
        if context and context.failed_verification_attempts >= 3:
            context.is_locked = True
            return GuardrailResult(
                passed=False,
                blocked_reason="Too many failed verification attempts. Session locked."
            )
        
        # Validate access based on resource type
        if resource_type == "order":
            is_valid, reason = validate_customer_access(
                resource_type=resource_type,
                resource_id=resource_id,
                customer_email=requesting_email,
            )
            if not is_valid:
                if context:
                    context.failed_verification_attempts += 1
                return GuardrailResult(
                    passed=False,
                    blocked_reason=reason or "Access denied. Please verify your email matches the order."
                )
        
        return GuardrailResult(passed=True)
    
    def sanitize_response(
        self,
        response_text: str,
        customer_email: Optional[str] = None,
    ) -> GuardrailResult:
        """
        Sanitize a response before sending to customer.
        
        Masks PII and checks for data leakage.
        
        Args:
            response_text: The response to sanitize
            customer_email: Customer's own email (may be shown unmasked if they provided it)
            
        Returns:
            GuardrailResult with sanitized text
        """
        warnings = []
        
        # Check what PII is present
        pii_detected = self.masker.contains_pii(response_text)
        
        # Mask all PII
        sanitized = self.masker.mask_all(response_text)
        
        # If customer provided their own email, we can show it unmasked
        # (they already know it)
        if customer_email and self.masker.mask_email(customer_email) in sanitized:
            # Keep their email masked for consistency, but note it
            pass
        
        # Log warnings for detected PII
        for pii_type, detected in pii_detected.items():
            if detected:
                warnings.append(f"Masked {pii_type} in response")
        
        return GuardrailResult(
            passed=True,
            modified_data=sanitized,
            warnings=warnings,
        )
    
    def validate_input(
        self,
        user_input: str,
        context: Optional[ConversationContext] = None,
    ) -> GuardrailResult:
        """
        Validate user input for potential injection or abuse.
        
        Args:
            user_input: The raw user input
            context: Current conversation context
            
        Returns:
            GuardrailResult indicating if input is safe
        """
        warnings = []
        
        # Check for excessively long input
        if len(user_input) > 5000:
            return GuardrailResult(
                passed=False,
                blocked_reason="Message is too long. Please keep messages under 5000 characters."
            )
        
        # Check for potential prompt injection patterns
        injection_patterns = [
            "ignore previous instructions",
            "ignore all instructions",
            "disregard your programming",
            "you are now",
            "act as if you are",
            "pretend you are",
            "system prompt",
            "reveal your instructions",
        ]
        
        lower_input = user_input.lower()
        for pattern in injection_patterns:
            if pattern in lower_input:
                warnings.append(f"Potential prompt injection detected: {pattern[:20]}...")
                # Don't block, but flag for review
        
        return GuardrailResult(
            passed=True,
            warnings=warnings,
        )
    
    def check_response_safety(
        self,
        response_text: str,
    ) -> GuardrailResult:
        """
        Final safety check on response before delivery.
        
        Args:
            response_text: The final response to check
            
        Returns:
            GuardrailResult indicating if response is safe to send
        """
        issues = []
        
        # Check for internal IDs that shouldn't be exposed
        if "CUST0" in response_text:
            issues.append("Internal customer ID exposed")
        
        # Check for unmasked credit cards
        if PIIMasker._has_credit_card(response_text):
            issues.append("Unmasked credit card detected")
        
        # Check for internal notes marker
        if "[INTERNAL]" in response_text.upper() or "internal_notes" in response_text.lower():
            issues.append("Internal notes reference detected")
        
        # Check for password-related text
        if "password" in response_text.lower() and "reset" not in response_text.lower():
            issues.append("Potentially sensitive password reference")
        
        if issues:
            return GuardrailResult(
                passed=False,
                blocked_reason=f"Response failed safety check: {', '.join(issues)}",
                warnings=issues,
            )
        
        return GuardrailResult(passed=True)
