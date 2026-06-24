"""Support ticket schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    """Support ticket status values."""
    
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicket(BaseModel):
    """Support ticket record."""
    
    ticket_id: str = Field(..., description="Unique ticket identifier")
    customer_email: str = Field(..., description="Customer email")
    intent: str = Field(..., description="Classified intent type")
    priority: str = Field(..., description="Ticket priority")
    summary: str = Field(..., description="Issue summary")
    status: TicketStatus = Field(default=TicketStatus.OPEN, description="Ticket status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = Field(default=None, description="Assigned agent/team")
    resolution_notes: Optional[str] = Field(default=None, description="Resolution details")
    
    model_config = {"use_enum_values": True}


class TicketCreateRequest(BaseModel):
    """Request to create a support ticket."""
    
    customer_email: str = Field(..., description="Customer email address")
    intent: str = Field(..., description="Intent type from classification")
    priority: str = Field(..., description="Priority level")
    summary: str = Field(..., max_length=500, description="Issue summary")
    original_message: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Original customer message"
    )


class TicketCreateResponse(BaseModel):
    """Response after creating a ticket."""
    
    ticket_id: str = Field(..., description="Created ticket ID")
    status: str = Field(..., description="Initial status")
    message: str = Field(..., description="Confirmation message")
    estimated_response_time: Optional[str] = Field(
        default=None,
        description="Expected response timeframe"
    )
