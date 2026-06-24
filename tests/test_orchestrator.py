"""Tests for the orchestrator and end-to-end flow."""

import pytest
import asyncio
from src.orchestrator import SupportOrchestrator
from src.schemas.message import CustomerMessage


@pytest.fixture
def orchestrator():
    """Create orchestrator instance."""
    return SupportOrchestrator()


class TestOrchestratorFlow:
    """Test suite for orchestrator end-to-end flows."""
    
    @pytest.mark.asyncio
    async def test_basic_order_status_flow(self, orchestrator):
        """Test basic order status inquiry flow."""
        message = CustomerMessage(
            content="Where is my order ORD-2024-002?",
            customer_email="alice.johnson@email.com",
        )
        
        response = await orchestrator.process(message)
        
        assert response.intent_detected == "order_status"
        assert response.message is not None
        assert len(response.message) > 0
        assert response.session_id is not None
    
    @pytest.mark.asyncio
    async def test_order_status_with_data(self, orchestrator):
        """Test order status returns actual order data."""
        message = CustomerMessage(
            content="What's the status of ORD-2024-002?",
            customer_email="alice.johnson@email.com",
        )
        
        response = await orchestrator.process(message)
        
        assert response.intent_detected == "order_status"
        assert "get_order_details" in response.tools_used
        # Response should contain status information
        assert any(word in response.message.lower() for word in ["shipped", "status", "order"])
    
    @pytest.mark.asyncio
    async def test_refund_request_flow(self, orchestrator):
        """Test refund request flow."""
        message = CustomerMessage(
            content="I want a refund for order ORD-2024-001",
            customer_email="alice.johnson@email.com",
        )
        
        response = await orchestrator.process(message)
        
        assert response.intent_detected == "refund_request"
        assert "get_refund_policy" in response.tools_used or "get_order_details" in response.tools_used
    
    @pytest.mark.asyncio
    async def test_human_escalation_creates_ticket(self, orchestrator):
        """Test human escalation creates a support ticket."""
        message = CustomerMessage(
            content="I want to speak to a human agent immediately!",
            customer_email="test@email.com",
        )
        
        response = await orchestrator.process(message)
        
        assert response.intent_detected == "human_escalation"
        assert response.ticket_created is not None
        assert response.requires_followup is True
    
    @pytest.mark.asyncio
    async def test_high_priority_creates_ticket(self, orchestrator):
        """Test high priority issues create tickets."""
        message = CustomerMessage(
            content="This is urgent! I was charged twice and I need this fixed NOW!",
            customer_email="test@email.com",
        )
        
        response = await orchestrator.process(message)
        
        assert response.priority in ["high", "urgent"]
        assert response.ticket_created is not None
    
    @pytest.mark.asyncio
    async def test_unauthorized_order_access(self, orchestrator):
        """Test unauthorized order access is handled safely."""
        message = CustomerMessage(
            content="Show me order ORD-2024-001",
            customer_email="wrong@email.com",  # Not the owner
        )
        
        response = await orchestrator.process(message)
        
        # Response should not contain actual order details
        assert "alice" not in response.message.lower()
        assert "149.99" not in response.message  # Order total
        # Should ask for verification
        assert any(word in response.message.lower() for word in ["verify", "email", "confirm", "provide"])
    
    @pytest.mark.asyncio
    async def test_session_continuity(self, orchestrator):
        """Test session maintains context across messages."""
        # First message
        message1 = CustomerMessage(
            content="My email is alice.johnson@email.com",
            customer_email="alice.johnson@email.com",
        )
        response1 = await orchestrator.process(message1)
        session_id = response1.session_id
        
        # Second message in same session
        message2 = CustomerMessage(
            content="Where is my order ORD-2024-002?",
            session_id=session_id,
        )
        response2 = await orchestrator.process(message2, session_id)
        
        # Should use email from session context
        assert response2.session_id == session_id
        assert "get_order_details" in response2.tools_used
    
    @pytest.mark.asyncio
    async def test_response_no_pii_leak(self, orchestrator):
        """Test responses don't leak PII."""
        message = CustomerMessage(
            content="Tell me everything about order ORD-2024-001",
            customer_email="alice.johnson@email.com",
        )
        
        response = await orchestrator.process(message)
        
        # Should not contain internal IDs
        assert "CUST001" not in response.message
        # Should not contain full credit card
        assert "4242" not in response.message or "**** **** **** 4242" in response.message
    
    @pytest.mark.asyncio
    async def test_missing_info_asks_for_details(self, orchestrator):
        """Test system asks for missing information."""
        message = CustomerMessage(
            content="Where is my order?",
            # No email or order ID provided
        )
        
        response = await orchestrator.process(message)
        
        # Should ask for order ID or email
        response_lower = response.message.lower()
        assert any(word in response_lower for word in ["order number", "order id", "email", "provide"])
    
    @pytest.mark.asyncio
    async def test_error_handling(self, orchestrator):
        """Test graceful error handling."""
        # Empty message should be handled gracefully
        message = CustomerMessage(content="   ")
        
        response = await orchestrator.process(message)
        
        # Should not crash, should return something
        assert response is not None
        assert response.message is not None


class TestOrchestratorSessions:
    """Test suite for session management."""
    
    @pytest.mark.asyncio
    async def test_get_session(self, orchestrator):
        """Test session retrieval."""
        message = CustomerMessage(
            content="Hello",
            customer_email="test@email.com",
        )
        response = await orchestrator.process(message)
        
        session = orchestrator.get_session(response.session_id)
        assert session is not None
        assert session.customer_email == "test@email.com"
    
    @pytest.mark.asyncio
    async def test_clear_session(self, orchestrator):
        """Test session clearing."""
        message = CustomerMessage(content="Hello")
        response = await orchestrator.process(message)
        
        result = orchestrator.clear_session(response.session_id)
        assert result is True
        
        session = orchestrator.get_session(response.session_id)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_intent_history_tracked(self, orchestrator):
        """Test that intent history is tracked in session."""
        message1 = CustomerMessage(content="Where is my order?")
        response1 = await orchestrator.process(message1)
        
        message2 = CustomerMessage(
            content="Actually I want a refund",
            session_id=response1.session_id,
        )
        await orchestrator.process(message2, response1.session_id)
        
        session = orchestrator.get_session(response1.session_id)
        assert len(session.intent_history) >= 2
        assert "order_status" in session.intent_history
        assert "refund_request" in session.intent_history
