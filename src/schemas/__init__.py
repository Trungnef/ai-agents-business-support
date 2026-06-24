"""Pydantic schemas for the customer support system."""

from .customer import Customer, CustomerProfile
from .order import Order, OrderStatus, RefundPolicy
from .intent import Intent, IntentType, Priority, ClassificationResult
from .ticket import SupportTicket, TicketStatus
from .message import CustomerMessage, AgentResponse, ConversationContext

__all__ = [
    # Customer
    "Customer",
    "CustomerProfile",
    # Order
    "Order",
    "OrderStatus",
    "RefundPolicy",
    # Intent
    "Intent",
    "IntentType",
    "Priority",
    "ClassificationResult",
    # Ticket
    "SupportTicket",
    "TicketStatus",
    # Message
    "CustomerMessage",
    "AgentResponse",
    "ConversationContext",
]
