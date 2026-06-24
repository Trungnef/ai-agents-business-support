"""Access validation utilities."""

from typing import Optional, Tuple

from src.tools.data_loader import DataLoader


def validate_customer_access(
    resource_type: str,
    resource_id: str,
    customer_email: Optional[str],
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a customer has access to a resource.
    
    Args:
        resource_type: Type of resource ("order", "customer", "ticket")
        resource_id: ID of the resource
        customer_email: Email claiming access
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not customer_email:
        return False, "Email verification required to access this information."
    
    if resource_type == "order":
        return _validate_order_access(resource_id, customer_email)
    elif resource_type == "customer":
        return _validate_customer_access(resource_id, customer_email)
    elif resource_type == "ticket":
        return _validate_ticket_access(resource_id, customer_email)
    else:
        return False, f"Unknown resource type: {resource_type}"


def _validate_order_access(order_id: str, email: str) -> Tuple[bool, Optional[str]]:
    """Validate access to an order."""
    orders_df = DataLoader.get_orders()
    
    # Find the order
    order_row = orders_df[orders_df["order_id"] == order_id]
    
    if order_row.empty:
        # Don't reveal whether order exists
        return False, "Unable to verify access to this order."
    
    order_email = order_row.iloc[0]["customer_email"]
    
    if order_email.lower() != email.lower():
        # Don't reveal that order exists but belongs to someone else
        return False, "Unable to verify access to this order."
    
    return True, None


def _validate_customer_access(customer_id: str, email: str) -> Tuple[bool, Optional[str]]:
    """Validate access to customer data."""
    customers_df = DataLoader.get_customers()
    
    # Find customer by ID
    customer_row = customers_df[customers_df["customer_id"] == customer_id]
    
    if customer_row.empty:
        return False, "Customer not found."
    
    customer_email = customer_row.iloc[0]["email"]
    
    if customer_email.lower() != email.lower():
        return False, "Email does not match customer record."
    
    return True, None


def _validate_ticket_access(ticket_id: str, email: str) -> Tuple[bool, Optional[str]]:
    """Validate access to a support ticket."""
    tickets_df = DataLoader.get_tickets()
    
    # Find the ticket
    ticket_row = tickets_df[tickets_df["ticket_id"] == ticket_id]
    
    if ticket_row.empty:
        return False, "Ticket not found."
    
    ticket_email = ticket_row.iloc[0]["customer_email"]
    
    if ticket_email.lower() != email.lower():
        return False, "Unable to verify access to this ticket."
    
    return True, None


def validate_email_format(email: str) -> Tuple[bool, Optional[str]]:
    """
    Basic email format validation.
    
    Args:
        email: Email to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    
    if not email:
        return False, "Email is required."
    
    # Basic pattern check
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format."
    
    return True, None


def check_account_status(email: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a customer account is in good standing.
    
    Args:
        email: Customer email
        
    Returns:
        Tuple of (is_active, status_message)
    """
    customers_df = DataLoader.get_customers()
    
    customer_row = customers_df[customers_df["email"].str.lower() == email.lower()]
    
    if customer_row.empty:
        return False, "Account not found."
    
    status = customer_row.iloc[0].get("account_status", "active")
    
    if status == "suspended":
        return False, "Account is suspended. Please contact support for assistance."
    elif status == "inactive":
        return False, "Account is inactive. Please reactivate your account."
    
    return True, None
