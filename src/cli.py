"""CLI entrypoint for the Multi-Agent Customer Support Assistant."""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from src.orchestrator import SupportOrchestrator
from src.schemas.message import CustomerMessage
from src.tools.data_loader import DataLoader


console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║     Multi-Agent Customer Support Assistant for SMBs              ║
║     ─────────────────────────────────────────────────            ║
║     Powered by ADK-style agents + MCP tools                      ║
╚══════════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold blue")


def print_help_commands():
    """Print available commands."""
    table = Table(title="Available Commands", show_header=True)
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    
    table.add_row("/help", "Show this help message")
    table.add_row("/email <email>", "Set your email for verification")
    table.add_row("/order <id>", "Set order ID for context")
    table.add_row("/session", "Show current session info")
    table.add_row("/clear", "Clear session and start fresh")
    table.add_row("/data", "Show sample data available")
    table.add_row("/quit or /exit", "Exit the chat")
    
    console.print(table)


def print_sample_data():
    """Print available sample data for testing."""
    console.print("\n[bold]Sample Customers:[/bold]")
    customers = DataLoader.get_customers()
    for _, row in customers.head(5).iterrows():
        console.print(f"  • {row['name']} - {row['email']}")
    
    console.print("\n[bold]Sample Orders:[/bold]")
    orders = DataLoader.get_orders()
    for _, row in orders.head(5).iterrows():
        console.print(f"  • {row['order_id']} ({row['status']}) - {row['customer_email']}")
    
    console.print("\n[dim]Use these for testing. Example:[/dim]")
    console.print('[dim]"Where is my order ORD-2024-002?" with /email alice.johnson@email.com[/dim]')


@click.group()
def cli():
    """Multi-Agent Customer Support Assistant CLI."""
    pass


@cli.command()
@click.option("--email", "-e", default=None, help="Your email address for verification")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed processing info")
def chat(email: Optional[str], verbose: bool):
    """Start an interactive chat session."""
    print_banner()
    
    orchestrator = SupportOrchestrator()
    session_id = None
    current_email = email
    current_order = None
    
    console.print("\n[green]Welcome! I'm your AI support assistant.[/green]")
    console.print("Type your question or /help for commands.\n")
    
    if current_email:
        console.print(f"[dim]Email set to: {current_email}[/dim]")
    
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
            
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]
                args = user_input.split()[1:] if len(user_input.split()) > 1 else []
                
                if cmd in ["/quit", "/exit", "/q"]:
                    console.print("\n[yellow]Goodbye! Have a great day![/yellow]")
                    break
                elif cmd == "/help":
                    print_help_commands()
                    continue
                elif cmd == "/email":
                    if args:
                        current_email = args[0]
                        console.print(f"[green]Email set to: {current_email}[/green]")
                    else:
                        console.print("[red]Usage: /email your@email.com[/red]")
                    continue
                elif cmd == "/order":
                    if args:
                        current_order = args[0].upper()
                        console.print(f"[green]Order ID set to: {current_order}[/green]")
                    else:
                        console.print("[red]Usage: /order ORD-2024-001[/red]")
                    continue
                elif cmd == "/session":
                    if session_id:
                        ctx = orchestrator.get_session(session_id)
                        if ctx:
                            console.print(f"\n[bold]Session Info:[/bold]")
                            console.print(f"  Session ID: {ctx.session_id[:8]}...")
                            console.print(f"  Email: {ctx.customer_email or 'Not set'}")
                            console.print(f"  Message count: {len(ctx.messages)}")
                            console.print(f"  Intent history: {ctx.intent_history}")
                    else:
                        console.print("[dim]No active session yet[/dim]")
                    continue
                elif cmd == "/clear":
                    if session_id:
                        orchestrator.clear_session(session_id)
                    session_id = None
                    console.print("[green]Session cleared[/green]")
                    continue
                elif cmd == "/data":
                    print_sample_data()
                    continue
                else:
                    console.print(f"[red]Unknown command: {cmd}. Type /help for available commands.[/red]")
                    continue
            
            # Process the message
            message = CustomerMessage(
                content=user_input,
                customer_email=current_email,
                order_id=current_order,
                session_id=session_id,
            )
            
            with console.status("[bold green]Processing...[/bold green]"):
                response = asyncio.run(orchestrator.process(message, session_id))
            
            # Update session ID
            session_id = response.session_id
            
            # Display response
            console.print()
            console.print(Panel(
                Markdown(response.message),
                title="[bold blue]Assistant[/bold blue]",
                border_style="blue",
            ))
            
            # Show metadata if verbose
            if verbose:
                console.print(f"\n[dim]Intent: {response.intent_detected} | Priority: {response.priority}[/dim]")
                if response.tools_used:
                    console.print(f"[dim]Tools used: {', '.join(response.tools_used)}[/dim]")
                if response.ticket_created:
                    console.print(f"[dim]Ticket created: {response.ticket_created}[/dim]")
                console.print(f"[dim]Processing time: {response.processing_time_ms}ms[/dim]")
            
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())


@cli.command()
@click.argument("message")
@click.option("--email", "-e", default=None, help="Your email address")
@click.option("--order", "-o", default=None, help="Order ID")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def ask(message: str, email: Optional[str], order: Optional[str], verbose: bool):
    """Send a single message and get a response."""
    orchestrator = SupportOrchestrator()
    
    msg = CustomerMessage(
        content=message,
        customer_email=email,
        order_id=order,
    )
    
    response = asyncio.run(orchestrator.process(msg))
    
    if verbose:
        console.print(f"\n[bold]Intent:[/bold] {response.intent_detected}")
        console.print(f"[bold]Priority:[/bold] {response.priority}")
        if response.tools_used:
            console.print(f"[bold]Tools:[/bold] {', '.join(response.tools_used)}")
        console.print()
    
    console.print(Panel(
        Markdown(response.message),
        title="Response",
        border_style="green",
    ))
    
    if response.ticket_created:
        console.print(f"\n[yellow]Ticket created: {response.ticket_created}[/yellow]")


@cli.command()
def tools():
    """List available MCP tools."""
    from src.mcp_server.server import MCPToolServer
    
    server = MCPToolServer()
    tool_list = server.list_tools()
    
    console.print("\n[bold]Available MCP Tools:[/bold]\n")
    
    for tool in tool_list:
        console.print(f"[cyan]{tool['name']}[/cyan]")
        console.print(f"  {tool['description']}")
        params = tool.get("parameters", {}).get("properties", {})
        if params:
            console.print("  [dim]Parameters:[/dim]")
            for name, info in params.items():
                console.print(f"    - {name}: {info.get('description', '')}")
        console.print()


@cli.command()
@click.argument("test_type", type=click.Choice(["intent", "pii", "order", "all"]))
def test(test_type: str):
    """Run quick validation tests."""
    console.print(f"\n[bold]Running {test_type} tests...[/bold]\n")
    
    if test_type in ["intent", "all"]:
        _test_intent_classification()
    
    if test_type in ["pii", "all"]:
        _test_pii_masking()
    
    if test_type in ["order", "all"]:
        _test_order_lookup()


def _test_intent_classification():
    """Test intent classification."""
    from src.agents.intent_classifier import IntentClassifierAgent
    
    agent = IntentClassifierAgent()
    
    test_cases = [
        ("Where is my order ORD-2024-001?", "order_status"),
        ("I want a refund", "refund_request"),
        ("I was charged twice!", "billing_issue"),
        ("I can't log into my account", "account_access"),
        ("Let me speak to a manager", "human_escalation"),
    ]
    
    console.print("[bold]Intent Classification Tests:[/bold]")
    
    for message, expected in test_cases:
        response = asyncio.run(agent.process(message))
        classification = response.metadata.get("classification", {})
        actual = classification.get("primary_intent", {}).get("type", "unknown")
        
        status = "✓" if actual == expected else "✗"
        color = "green" if actual == expected else "red"
        console.print(f"  [{color}]{status}[/{color}] '{message[:40]}...' → {actual} (expected: {expected})")


def _test_pii_masking():
    """Test PII masking."""
    from src.security.pii_masker import PIIMasker
    
    test_cases = [
        ("Card: 4242424242424242", "Card: **** **** **** 4242"),
        ("Email: alice@example.com", "Email: a****@example.com"),
        ("Phone: +1-555-0101", "Phone: ***-***-0101"),
        ("Customer CUST001", "Customer [INTERNAL]"),
    ]
    
    console.print("[bold]PII Masking Tests:[/bold]")
    
    for original, expected in test_cases:
        masked = PIIMasker.mask_all(original)
        status = "✓" if masked == expected else "✗"
        color = "green" if masked == expected else "red"
        console.print(f"  [{color}]{status}[/{color}] '{original}' → '{masked}'")


def _test_order_lookup():
    """Test order lookup with authorization."""
    from src.tools.order_tools import get_order_details
    
    test_cases = [
        # (order_id, email, should_succeed)
        ("ORD-2024-001", "alice.johnson@email.com", True),
        ("ORD-2024-001", "wrong@email.com", False),
        ("INVALID-ORDER", "alice.johnson@email.com", False),
    ]
    
    console.print("[bold]Order Lookup Authorization Tests:[/bold]")
    
    for order_id, email, should_succeed in test_cases:
        result = get_order_details(order_id, email)
        success = result is not None
        
        status = "✓" if success == should_succeed else "✗"
        color = "green" if success == should_succeed else "red"
        outcome = "found" if success else "denied"
        expected = "should succeed" if should_succeed else "should deny"
        console.print(f"  [{color}]{status}[/{color}] {order_id} + {email[:15]}... → {outcome} ({expected})")


if __name__ == "__main__":
    cli()
