"""Order-related schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status values."""
    
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    RETURN_REQUESTED = "return_requested"
    RETURNED = "returned"


class Order(BaseModel):
    """Order details (internal representation)."""
    
    order_id: str = Field(..., description="Public order identifier")
    customer_id: str = Field(..., description="Internal customer ID")
    customer_email: str = Field(..., description="Customer email")
    status: OrderStatus = Field(..., description="Current order status")
    total_amount: float = Field(..., ge=0, description="Order total in USD")
    items_count: int = Field(..., ge=1, description="Number of items")
    created_at: datetime = Field(..., description="Order creation date")
    shipped_at: Optional[datetime] = Field(default=None, description="Ship date")
    delivered_at: Optional[datetime] = Field(default=None, description="Delivery date")
    tracking_number: Optional[str] = Field(default=None, description="Shipping tracking")
    carrier: Optional[str] = Field(default=None, description="Shipping carrier")
    
    # Sensitive fields - never expose directly
    payment_method_last4: Optional[str] = Field(default=None, description="Last 4 digits")
    internal_notes: Optional[str] = Field(default=None, description="Internal staff notes")
    
    model_config = {"use_enum_values": True, "from_attributes": True}


class OrderSummary(BaseModel):
    """Safe order summary for customer-facing responses."""
    
    order_id: str = Field(..., description="Order identifier")
    status: str = Field(..., description="Human-readable status")
    status_description: str = Field(..., description="Detailed status explanation")
    total_amount: str = Field(..., description="Formatted total (e.g., '$99.99')")
    items_count: int = Field(..., description="Number of items")
    order_date: str = Field(..., description="Formatted order date")
    estimated_delivery: Optional[str] = Field(default=None, description="Expected delivery")
    tracking_url: Optional[str] = Field(default=None, description="Tracking link")
    
    # NOTE: Never include customer_id, payment details, or internal notes


class RefundPolicy(BaseModel):
    """Refund policy information for an order."""
    
    order_id: str = Field(..., description="Order identifier")
    is_eligible: bool = Field(..., description="Whether order is eligible for refund")
    eligibility_reason: str = Field(..., description="Explanation of eligibility")
    refund_window_days: int = Field(default=30, description="Days allowed for refund")
    days_remaining: Optional[int] = Field(default=None, description="Days left to request")
    refund_amount: Optional[float] = Field(default=None, description="Potential refund amount")
    refund_method: str = Field(
        default="original_payment",
        description="How refund would be issued"
    )
    special_conditions: Optional[str] = Field(
        default=None,
        description="Any special conditions that apply"
    )
