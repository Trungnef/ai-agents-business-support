"""Customer profile tools."""

from datetime import datetime
from typing import Optional

from src.tools.data_loader import DataLoader
from src.schemas.customer import CustomerProfile
from src.security.pii_masker import PIIMasker


def get_customer_profile(email: str) -> Optional[CustomerProfile]:
    """
    Retrieve customer profile by email.
    
    Returns a safe CustomerProfile with masked PII. Never returns
    internal customer ID or sensitive account details.
    
    Args:
        email: Customer email address
        
    Returns:
        CustomerProfile with safe information, or None if not found
    """
    customers_df = DataLoader.get_customers()
    orders_df = DataLoader.get_orders()
    
    # Find customer by email (case-insensitive)
    customer_row = customers_df[
        customers_df["email"].str.lower() == email.lower()
    ]
    
    if customer_row.empty:
        return None
    
    customer_data = customer_row.iloc[0]
    
    # Count total orders for this customer
    total_orders = len(
        orders_df[orders_df["customer_email"].str.lower() == email.lower()]
    )
    
    # Format member since date
    try:
        created_at = datetime.fromisoformat(
            customer_data["created_at"].replace("Z", "+00:00")
        )
        member_since = created_at.strftime("%B %Y")
    except (ValueError, AttributeError):
        member_since = "Unknown"
    
    return CustomerProfile(
        email_masked=PIIMasker.mask_email(email),
        name=customer_data["name"],
        account_status=customer_data.get("account_status", "active"),
        member_since=member_since,
        total_orders=total_orders,
        loyalty_tier=customer_data.get("loyalty_tier"),
    )


def verify_customer_exists(email: str) -> bool:
    """
    Check if a customer exists with the given email.
    
    Args:
        email: Email to check
        
    Returns:
        True if customer exists, False otherwise
    """
    customers_df = DataLoader.get_customers()
    return any(customers_df["email"].str.lower() == email.lower())


def get_customer_status(email: str) -> Optional[str]:
    """
    Get account status for a customer.
    
    Args:
        email: Customer email
        
    Returns:
        Account status string or None if not found
    """
    customers_df = DataLoader.get_customers()
    customer_row = customers_df[
        customers_df["email"].str.lower() == email.lower()
    ]
    
    if customer_row.empty:
        return None
    
    return customer_row.iloc[0].get("account_status", "active")
