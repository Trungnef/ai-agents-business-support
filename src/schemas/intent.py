"""Intent classification schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Customer support intent types."""
    
    REFUND_REQUEST = "refund_request"
    ORDER_STATUS = "order_status"
    BILLING_ISSUE = "billing_issue"
    ACCOUNT_ACCESS = "account_access"
    SHIPPING_ISSUE = "shipping_issue"
    HUMAN_ESCALATION = "human_escalation"
    OTHER = "other"


class Priority(str, Enum):
    """Support request priority levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Intent(BaseModel):
    """Parsed customer intent."""
    
    type: IntentType = Field(..., description="The classified intent type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    
    model_config = {"use_enum_values": True}


class ClassificationResult(BaseModel):
    """Result of intent classification."""
    
    primary_intent: Intent = Field(..., description="Primary detected intent")
    secondary_intents: list[Intent] = Field(
        default_factory=list,
        description="Additional intents detected"
    )
    priority: Priority = Field(..., description="Assigned priority level")
    requires_human: bool = Field(
        default=False,
        description="Whether human escalation is recommended"
    )
    extracted_entities: dict = Field(
        default_factory=dict,
        description="Extracted entities like order_id, email, etc."
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Explanation of classification decision"
    )
    
    model_config = {"use_enum_values": True}
