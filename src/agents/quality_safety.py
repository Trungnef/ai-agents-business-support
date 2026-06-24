"""Quality and Safety Agent."""

from typing import Any, Optional

from src.agents.base import BaseAgent, AgentConfig
from src.schemas.message import AgentResponse, ConversationContext
from src.security.guardrails import SecurityGuardrail
from src.security.pii_masker import PIIMasker


QUALITY_SAFETY_PROMPT = """You are a quality and safety reviewer for customer support responses.

Review the draft response for:
1. PII leakage (credit cards, full SSN, internal IDs)
2. Accuracy (does the response match the data provided?)
3. Tone (is it professional and empathetic?)
4. Completeness (does it address the customer's concern?)
5. Policy compliance (no promises we can't keep)

If there are issues, respond with:
{
    "approved": false,
    "issues": ["list of issues"],
    "suggested_fix": "what to fix"
}

If the response is good:
{
    "approved": true,
    "issues": []
}
"""


class QualitySafetyAgent(BaseAgent):
    """
    Agent responsible for quality assurance and safety checks.
    
    This is the final agent before response delivery. It:
    - Validates that PII is properly masked
    - Checks tone and professionalism
    - Ensures factual accuracy
    - Verifies policy compliance
    """
    
    def __init__(self):
        config = AgentConfig(
            name="QualitySafety",
            description="Validates response quality and safety before delivery",
            temperature=0.0,  # Deterministic safety checks
            max_tokens=512,
            system_prompt=QUALITY_SAFETY_PROMPT,
        )
        super().__init__(config)
        self.guardrail = SecurityGuardrail()
    
    async def process(
        self,
        input_data: dict,
        context: Optional[ConversationContext] = None,
    ) -> AgentResponse:
        """
        Validate and sanitize the draft response.
        
        Args:
            input_data: Dictionary with:
                - 'draft_response': The response to validate
                - 'customer_email': Customer's email (for context)
            context: Conversation context
            
        Returns:
            AgentResponse with validated/sanitized response
        """
        draft_response = input_data.get("draft_response", "")
        customer_email = input_data.get("customer_email")
        
        issues = []
        
        # 1. PII Safety Check
        sanitize_result = self.guardrail.sanitize_response(
            response_text=draft_response,
            customer_email=customer_email,
        )
        
        sanitized_response = sanitize_result.modified_data or draft_response
        if sanitize_result.warnings:
            issues.extend(sanitize_result.warnings)
        
        # 2. Final Safety Check
        safety_result = self.guardrail.check_response_safety(sanitized_response)
        
        if not safety_result.passed:
            # Response failed safety check - needs human review
            return self._create_response(
                content=self._generate_safe_fallback(),
                confidence=0.5,
                metadata={
                    "original_blocked": True,
                    "block_reason": safety_result.blocked_reason,
                    "issues": safety_result.warnings,
                },
                requires_escalation=True,
            )
        
        # 3. Quality checks
        quality_issues = self._check_quality(sanitized_response)
        issues.extend(quality_issues)
        
        # 4. Ensure response ends appropriately
        final_response = self._ensure_proper_ending(sanitized_response)
        
        return self._create_response(
            content=final_response,
            confidence=1.0 if not issues else 0.85,
            metadata={
                "quality_issues": issues if issues else None,
                "pii_masked": bool(sanitize_result.warnings),
            },
        )
    
    def _check_quality(self, response: str) -> list[str]:
        """Check response quality."""
        issues = []
        
        # Check minimum length
        if len(response) < 50:
            issues.append("Response may be too brief")
        
        # Check for abrupt ending
        if not any(response.rstrip().endswith(c) for c in ".!?"):
            issues.append("Response doesn't end with proper punctuation")
        
        # Check for placeholder text
        placeholders = ["[INSERT", "[PLACEHOLDER", "TODO", "XXX"]
        for ph in placeholders:
            if ph in response.upper():
                issues.append(f"Contains placeholder text: {ph}")
        
        # Check for overly negative language
        negative_phrases = [
            "we can't help",
            "nothing we can do",
            "not our problem",
            "your fault",
        ]
        response_lower = response.lower()
        for phrase in negative_phrases:
            if phrase in response_lower:
                issues.append(f"Contains potentially negative phrase: '{phrase}'")
        
        return issues
    
    def _ensure_proper_ending(self, response: str) -> str:
        """Ensure response ends appropriately."""
        response = response.strip()
        
        # If response doesn't offer follow-up, add one
        follow_up_phrases = [
            "anything else",
            "help you with",
            "further assistance",
            "let me know",
            "questions",
        ]
        
        has_follow_up = any(phrase in response.lower() for phrase in follow_up_phrases)
        
        if not has_follow_up and not response.endswith("?"):
            response += "\n\nIs there anything else I can help you with?"
        
        return response
    
    def _generate_safe_fallback(self) -> str:
        """Generate a safe fallback response when original is blocked."""
        return (
            "Thank you for your message. I want to make sure I provide you with "
            "accurate information, so I'm going to have one of our support specialists "
            "review your request.\n\n"
            "They will reach out to you within 24 hours. In the meantime, if you have "
            "any other questions, please don't hesitate to ask!"
        )
