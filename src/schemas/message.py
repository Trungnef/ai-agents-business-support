"""Message and conversation schemas."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class CustomerMessage(BaseModel):
    """Incoming customer message."""
    
    content: str = Field(..., min_length=1, max_length=5000, description="Message text")
    customer_email: Optional[str] = Field(default=None, description="Customer email if known")
    order_id: Optional[str] = Field(default=None, description="Order ID if provided")
    session_id: Optional[str] = Field(default=None, description="Conversation session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict, description="Additional context")


class AgentResponse(BaseModel):
    """Response from an agent in the pipeline."""
    
    agent_name: str = Field(..., description="Name of the responding agent")
    content: str = Field(..., description="Response content")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    tools_used: list[str] = Field(default_factory=list, description="Tools invoked")
    metadata: dict = Field(default_factory=dict, description="Additional data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # For chaining
    next_action: Optional[str] = Field(default=None, description="Suggested next action")
    requires_escalation: bool = Field(default=False, description="Needs human review")


class ConversationContext(BaseModel):
    """Context maintained across a conversation session."""
    
    session_id: str = Field(..., description="Unique session identifier")
    customer_email: Optional[str] = Field(default=None, description="Verified customer email")
    verified_order_ids: list[str] = Field(
        default_factory=list,
        description="Order IDs verified for this customer"
    )
    intent_history: list[str] = Field(
        default_factory=list,
        description="Previously detected intents"
    )
    messages: list[dict] = Field(
        default_factory=list,
        description="Conversation history"
    )
    tools_called: list[dict] = Field(
        default_factory=list,
        description="Tools invoked in this session"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Security context
    failed_verification_attempts: int = Field(
        default=0,
        description="Number of failed identity verifications"
    )
    is_locked: bool = Field(
        default=False,
        description="Whether session is locked due to security"
    )


class FinalResponse(BaseModel):
    """Final response to send to the customer."""
    
    message: str = Field(..., description="Customer-facing response text")
    intent_detected: str = Field(..., description="Primary intent that was handled")
    priority: str = Field(..., description="Request priority level")
    ticket_created: Optional[str] = Field(default=None, description="Ticket ID if created")
    tools_used: list[str] = Field(default_factory=list, description="Tools that were used")
    session_id: str = Field(..., description="Session ID for context")
    requires_followup: bool = Field(default=False, description="Whether followup is needed")
    
    # Audit trail (not sent to customer)
    internal_notes: Optional[str] = Field(default=None, description="Internal processing notes")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing duration")
