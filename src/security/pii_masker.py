"""PII detection and masking utilities."""

import re
from typing import Optional


class PIIMasker:
    """
    Utility class for detecting and masking Personally Identifiable Information.
    
    Masks:
    - Credit card numbers
    - Email addresses  
    - Phone numbers
    - Social Security Numbers
    - Internal customer IDs
    """
    
    # Patterns for PII detection
    CREDIT_CARD_PATTERN = re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{15,16}\b'
    )
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    PHONE_PATTERN = re.compile(
        r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}|\+?1?[-.\s]?\d{3}[-.\s]?\d{4}'
    )
    SSN_PATTERN = re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    )
    INTERNAL_ID_PATTERN = re.compile(
        r'\bCUST\d{3}\b'
    )
    
    @classmethod
    def mask_credit_card(cls, text: str) -> str:
        """
        Mask credit card numbers, preserving last 4 digits.
        
        Example: "4242424242424242" -> "**** **** **** 4242"
        """
        def replacer(match):
            card = re.sub(r'[-\s]', '', match.group())
            if len(card) >= 4:
                return f"**** **** **** {card[-4:]}"
            return "****"
        
        return cls.CREDIT_CARD_PATTERN.sub(replacer, text)
    
    @classmethod
    def mask_email(cls, email: str) -> str:
        """
        Mask an email address, showing first char and domain.
        
        Example: "alice.johnson@email.com" -> "a****@email.com"
        """
        if not email or "@" not in email:
            return email
        
        local, domain = email.rsplit("@", 1)
        if len(local) > 0:
            masked_local = local[0] + "****"
        else:
            masked_local = "****"
        
        return f"{masked_local}@{domain}"
    
    @classmethod
    def mask_emails_in_text(cls, text: str) -> str:
        """Mask all email addresses in a text string."""
        def replacer(match):
            return cls.mask_email(match.group())
        
        return cls.EMAIL_PATTERN.sub(replacer, text)
    
    @classmethod
    def mask_phone(cls, phone: str) -> str:
        """
        Mask a phone number, showing last 4 digits.
        
        Example: "+1-555-0101" -> "***-***-0101"
        """
        # Extract just the digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 4:
            return f"***-***-{digits[-4:]}"
        return "***-***-****"
    
    @classmethod
    def mask_phones_in_text(cls, text: str) -> str:
        """Mask all phone numbers in a text string."""
        def replacer(match):
            return cls.mask_phone(match.group())
        
        return cls.PHONE_PATTERN.sub(replacer, text)
    
    @classmethod
    def mask_ssn(cls, text: str) -> str:
        """Mask Social Security Numbers."""
        return cls.SSN_PATTERN.sub("***-**-****", text)
    
    @classmethod
    def mask_internal_ids(cls, text: str) -> str:
        """Mask internal customer IDs."""
        return cls.INTERNAL_ID_PATTERN.sub("[INTERNAL]", text)
    
    @classmethod
    def mask_all(cls, text: str) -> str:
        """
        Apply all masking rules to a text string.
        
        Order matters - more specific patterns first.
        """
        if not text:
            return text
        
        result = text
        result = cls.mask_credit_card(result)
        result = cls.mask_ssn(result)
        result = cls.mask_internal_ids(result)
        result = cls.mask_phones_in_text(result)
        result = cls.mask_emails_in_text(result)
        
        return result
    
    @classmethod
    def _has_credit_card(cls, text: str) -> bool:
        """Check if text contains an unmasked credit card."""
        # First check if there's a pattern match
        match = cls.CREDIT_CARD_PATTERN.search(text)
        if not match:
            return False
        
        # If match found, check it's not already masked
        matched_text = match.group()
        if "****" in matched_text:
            return False
        
        return True
    
    @classmethod
    def contains_pii(cls, text: str) -> dict:
        """
        Check what types of PII are present in text.
        
        Returns:
            Dictionary with PII types and whether they were detected
        """
        return {
            "credit_card": bool(cls.CREDIT_CARD_PATTERN.search(text)),
            "email": bool(cls.EMAIL_PATTERN.search(text)),
            "phone": bool(cls.PHONE_PATTERN.search(text)),
            "ssn": bool(cls.SSN_PATTERN.search(text)),
            "internal_id": bool(cls.INTERNAL_ID_PATTERN.search(text)),
        }
