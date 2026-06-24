"""Tests for intent classification."""

import pytest
import asyncio
from src.agents.intent_classifier import IntentClassifierAgent
from src.schemas.intent import IntentType


@pytest.fixture
def intent_agent():
    """Create intent classifier agent."""
    return IntentClassifierAgent()


class TestIntentClassification:
    """Test suite for intent classification."""
    
    @pytest.mark.asyncio
    async def test_order_status_intent(self, intent_agent):
        """Test classification of order status inquiries."""
        messages = [
            "Where is my order?",
            "Can you track my package?",
            "What's the status of ORD-2024-001?",
            "When will my order arrive?",
        ]
        
        for msg in messages:
            response = await intent_agent.process(msg)
            classification = response.metadata.get("classification", {})
            intent = classification.get("primary_intent", {}).get("type")
            assert intent == "order_status", f"Failed for: {msg}"
    
    @pytest.mark.asyncio
    async def test_refund_request_intent(self, intent_agent):
        """Test classification of refund requests."""
        messages = [
            "I want a refund",
            "Can I get my money back?",
            "I'd like to return this item",
            "Please refund my order",
        ]
        
        for msg in messages:
            response = await intent_agent.process(msg)
            classification = response.metadata.get("classification", {})
            intent = classification.get("primary_intent", {}).get("type")
            assert intent == "refund_request", f"Failed for: {msg}"
    
    @pytest.mark.asyncio
    async def test_billing_issue_intent(self, intent_agent):
        """Test classification of billing issues."""
        messages = [
            "I was charged twice",
            "There's a problem with my payment",
            "Wrong amount on my invoice",
            "Billing error on my account",
        ]
        
        for msg in messages:
            response = await intent_agent.process(msg)
            classification = response.metadata.get("classification", {})
            intent = classification.get("primary_intent", {}).get("type")
            assert intent == "billing_issue", f"Failed for: {msg}"
    
    @pytest.mark.asyncio
    async def test_account_access_intent(self, intent_agent):
        """Test classification of account access issues."""
        messages = [
            "I can't log in",
            "My account is locked",
            "I forgot my password",
            "Can't access my account",
        ]
        
        for msg in messages:
            response = await intent_agent.process(msg)
            classification = response.metadata.get("classification", {})
            intent = classification.get("primary_intent", {}).get("type")
            assert intent == "account_access", f"Failed for: {msg}"
    
    @pytest.mark.asyncio
    async def test_human_escalation_intent(self, intent_agent):
        """Test classification of human escalation requests."""
        messages = [
            "Let me speak to a human",
            "I want to talk to a manager",
            "Connect me with a real person",
            "Get me a supervisor",
        ]
        
        for msg in messages:
            response = await intent_agent.process(msg)
            classification = response.metadata.get("classification", {})
            intent = classification.get("primary_intent", {}).get("type")
            assert intent == "human_escalation", f"Failed for: {msg}"
    
    @pytest.mark.asyncio
    async def test_urgent_priority_detection(self, intent_agent):
        """Test detection of urgent priority."""
        messages = [
            "This is urgent! I need help immediately!",
            "I'll contact my lawyer if this isn't resolved!",
            "This is completely unacceptable and I'm furious!",
        ]
        
        for msg in messages:
            response = await intent_agent.process(msg)
            classification = response.metadata.get("classification", {})
            priority = classification.get("priority")
            assert priority in ["urgent", "high"], f"Failed for: {msg}, got {priority}"
    
    @pytest.mark.asyncio
    async def test_entity_extraction_order_id(self, intent_agent):
        """Test extraction of order ID from message."""
        msg = "Where is my order ORD-2024-001?"
        response = await intent_agent.process(msg)
        classification = response.metadata.get("classification", {})
        entities = classification.get("extracted_entities", {})
        
        assert entities.get("order_id") == "ORD-2024-001"
    
    @pytest.mark.asyncio
    async def test_entity_extraction_email(self, intent_agent):
        """Test extraction of email from message."""
        msg = "My email is alice@example.com, can you help?"
        response = await intent_agent.process(msg)
        classification = response.metadata.get("classification", {})
        entities = classification.get("extracted_entities", {})
        
        assert entities.get("email") == "alice@example.com"
    
    @pytest.mark.asyncio
    async def test_classification_schema_valid(self, intent_agent):
        """Test that classification result follows expected schema."""
        response = await intent_agent.process("Where is my order?")
        classification = response.metadata.get("classification", {})
        
        # Check required fields exist
        assert "primary_intent" in classification
        assert "priority" in classification
        assert "extracted_entities" in classification
        
        # Check primary_intent structure
        primary = classification["primary_intent"]
        assert "type" in primary
        assert "confidence" in primary
        
        # Check confidence is valid
        assert 0 <= primary["confidence"] <= 1
        
        # Check priority is valid
        assert classification["priority"] in ["low", "medium", "high", "urgent"]
