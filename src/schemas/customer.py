"""Customer-related schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Customer(BaseModel):
    """Core customer data."""
    
    customer_id: str = Field(..., description="Internal customer identifier")
    email: str = Field(..., description="Customer email address")
    name: str = Field(..., description="Customer full name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    created_at: datetime = Field(..., description="Account creation date")
    
    model_config = {"from_attributes": True}


class CustomerProfile(BaseModel):
    """Customer profile with account details (safe for external response)."""
    
    email_masked: str = Field(..., description="Partially masked email")
    name: str = Field(..., description="Customer name")
    account_status: str = Field(default="active", description="Account status")
    member_since: str = Field(..., description="Formatted membership date")
    total_orders: int = Field(default=0, description="Total orders placed")
    loyalty_tier: Optional[str] = Field(default=None, description="Loyalty program tier")
    
    # NOTE: Never include customer_id, full email, or payment info in this schema
