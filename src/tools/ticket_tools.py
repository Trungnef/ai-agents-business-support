"""Support ticket management tools."""

from datetime import datetime
import uuid
from typing import Optional

from src.tools.data_loader import DataLoader
from src.schemas.ticket import (
    SupportTicket,
    TicketStatus,
    TicketCreateRequest,
    TicketCreateResponse,
)


def create_support_ticket(
    customer_email: str,
    intent: str,
    priority: str,
    summary: str,
    original_message: Optional[str] = None,
) -> TicketCreateResponse:
    """
    Create a new support ticket for tracking.
    
    Args:
        customer_email: Customer's email address
        intent: Classified intent type
        priority: Priority level (low, medium, high, urgent)
        summary: Brief summary of the issue
        original_message: Original customer message (optional)
        
    Returns:
        TicketCreateResponse with ticket ID and confirmation
    """
    # Generate unique ticket ID
    ticket_id = f"TKT-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    
    # Create ticket data
    now = datetime.utcnow().isoformat() + "Z"
    ticket_data = {
        "ticket_id": ticket_id,
        "customer_email": customer_email,
        "intent": intent,
        "priority": priority,
        "summary": summary[:500] if summary else "",  # Truncate to max length
        "status": TicketStatus.OPEN.value,
        "created_at": now,
        "updated_at": now,
        "assigned_to": _get_assignment(intent, priority),
        "resolution_notes": "",
    }
    
    # Save to CSV
    DataLoader.save_ticket(ticket_data)
    
    # Determine estimated response time based on priority
    response_times = {
        "urgent": "within 1 hour",
        "high": "within 4 hours",
        "medium": "within 24 hours",
        "low": "within 48 hours",
    }
    
    return TicketCreateResponse(
        ticket_id=ticket_id,
        status=TicketStatus.OPEN.value,
        message=f"Your support ticket {ticket_id} has been created. We'll be in touch soon!",
        estimated_response_time=response_times.get(priority.lower(), "within 48 hours"),
    )


def get_ticket_status(ticket_id: str) -> Optional[SupportTicket]:
    """
    Get the status of an existing support ticket.
    
    Args:
        ticket_id: The ticket identifier
        
    Returns:
        SupportTicket with current status, or None if not found
    """
    tickets_df = DataLoader.get_tickets()
    
    ticket_row = tickets_df[tickets_df["ticket_id"] == ticket_id]
    
    if ticket_row.empty:
        return None
    
    ticket_data = ticket_row.iloc[0]
    
    return SupportTicket(
        ticket_id=ticket_data["ticket_id"],
        customer_email=ticket_data["customer_email"],
        intent=ticket_data["intent"],
        priority=ticket_data["priority"],
        summary=ticket_data["summary"],
        status=TicketStatus(ticket_data["status"]),
        created_at=datetime.fromisoformat(ticket_data["created_at"].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(ticket_data["updated_at"].replace("Z", "+00:00")),
        assigned_to=ticket_data.get("assigned_to"),
        resolution_notes=ticket_data.get("resolution_notes"),
    )


def _get_assignment(intent: str, priority: str) -> str:
    """Determine initial assignment based on intent and priority."""
    # Urgent and high priority go to human teams
    if priority.lower() in ["urgent", "high"]:
        if intent == "account_access":
            return "security_team"
        elif intent == "billing_issue":
            return "billing_team"
        else:
            return "support_team_1"
    
    # Lower priority can be handled by bot initially
    return "bot"
