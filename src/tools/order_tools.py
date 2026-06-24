"""Order-related business tools."""

from datetime import datetime
from typing import Optional

from src.tools.data_loader import DataLoader
from src.schemas.order import Order, OrderSummary, RefundPolicy, OrderStatus


def get_order_details(order_id: str, email: str) -> Optional[OrderSummary]:
    """
    Retrieve order details for a given order ID and customer email.
    
    Security: Validates that the order belongs to the provided email before
    returning any data. Returns None if order not found or email mismatch.
    
    Args:
        order_id: The order identifier (e.g., "ORD-2024-001")
        email: Customer email for verification
        
    Returns:
        OrderSummary with safe customer-facing order information, or None
    """
    orders_df = DataLoader.get_orders()
    
    # Find order by ID
    order_row = orders_df[orders_df["order_id"] == order_id]
    
    if order_row.empty:
        return None
    
    order_data = order_row.iloc[0]
    
    # Security check: verify email matches
    if order_data["customer_email"].lower() != email.lower():
        return None  # Do not reveal that order exists but belongs to someone else
    
    # Format status for customer
    status = order_data["status"]
    status_descriptions = {
        "pending": "Your order is being processed and will ship soon.",
        "confirmed": "Your order has been confirmed and is being prepared.",
        "processing": "Your order is being prepared in our warehouse.",
        "shipped": "Your order has been shipped and is on its way!",
        "out_for_delivery": "Great news! Your order is out for delivery today.",
        "delivered": "Your order has been delivered.",
        "cancelled": "This order has been cancelled.",
        "refunded": "This order has been refunded.",
        "return_requested": "A return has been requested for this order.",
        "returned": "This order has been returned and refunded.",
    }
    
    # Calculate estimated delivery for shipped orders
    estimated_delivery = None
    if status in ["shipped", "out_for_delivery"] and order_data.get("shipped_at"):
        # Simple estimation: 3-5 business days from ship date
        estimated_delivery = "Within 3-5 business days from shipment"
    
    # Build tracking URL if available
    tracking_url = None
    if order_data.get("tracking_number") and order_data.get("carrier"):
        carrier = order_data["carrier"]
        tracking = order_data["tracking_number"]
        carrier_urls = {
            "UPS": f"https://www.ups.com/track?tracknum={tracking}",
            "USPS": f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking}",
            "FedEx": f"https://www.fedex.com/fedextrack/?trknbr={tracking}",
        }
        tracking_url = carrier_urls.get(carrier)
    
    return OrderSummary(
        order_id=order_data["order_id"],
        status=status,
        status_description=status_descriptions.get(status, "Status update pending."),
        total_amount=f"${order_data['total_amount']:.2f}",
        items_count=int(order_data["items_count"]),
        order_date=_format_date(order_data["created_at"]),
        estimated_delivery=estimated_delivery,
        tracking_url=tracking_url,
    )


def get_refund_policy(order_id: str) -> Optional[RefundPolicy]:
    """
    Get refund eligibility information for an order.
    
    Note: This does not require email verification as it returns
    policy information, not personal data. However, actual refund
    processing would require verification.
    
    Args:
        order_id: The order identifier
        
    Returns:
        RefundPolicy with eligibility details, or None if order not found
    """
    orders_df = DataLoader.get_orders()
    policies = DataLoader.get_refund_policies()
    
    # Find order
    order_row = orders_df[orders_df["order_id"] == order_id]
    if order_row.empty:
        return None
    
    order_data = order_row.iloc[0]
    status = order_data["status"]
    
    # Get status-based eligibility
    status_policy = policies["status_eligibility"].get(status, {})
    is_eligible = status_policy.get("eligible", False)
    eligibility_reason = status_policy.get("reason", "Please contact support for details.")
    
    # Calculate days remaining in refund window
    days_remaining = None
    if is_eligible and status == "delivered" and order_data.get("delivered_at"):
        delivered_date = datetime.fromisoformat(order_data["delivered_at"].replace("Z", "+00:00"))
        days_since = (datetime.now(delivered_date.tzinfo) - delivered_date).days
        window = policies["default_policy"]["refund_window_days"]
        days_remaining = max(0, window - days_since)
        if days_remaining == 0:
            is_eligible = False
            eligibility_reason = "The refund window has expired for this order."
    
    # Determine refund amount
    refund_amount = None
    if is_eligible:
        refund_amount = float(order_data["total_amount"])
    
    return RefundPolicy(
        order_id=order_id,
        is_eligible=is_eligible,
        eligibility_reason=eligibility_reason,
        refund_window_days=policies["default_policy"]["refund_window_days"],
        days_remaining=days_remaining,
        refund_amount=refund_amount,
        refund_method=policies["default_policy"]["refund_method"],
        special_conditions=None,  # Would check for damaged items, loyalty tier, etc.
    )


def _format_date(date_str: str) -> str:
    """Format ISO date string to human-readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y")
    except (ValueError, AttributeError):
        return "Unknown"
