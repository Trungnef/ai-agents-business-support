"""
MCP Tool Server Implementation.

This module implements a Model Context Protocol (MCP) compatible server
that exposes business tools for the agent system.

If the official MCP SDK is not available, this provides a compatible
abstraction layer that follows MCP conventions.
"""

from typing import Any, Callable, Optional
from dataclasses import dataclass, field
import json
import structlog

from src.tools.order_tools import get_order_details, get_refund_policy
from src.tools.customer_tools import get_customer_profile
from src.tools.ticket_tools import create_support_ticket
from src.tools.security_tools import mask_sensitive_data, audit_log_event


logger = structlog.get_logger(__name__)


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    parameters: list[ToolParameter]
    handler: Callable
    requires_auth: bool = False


@dataclass
class ToolCallResult:
    """Result of a tool call."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    tool_name: str = ""


class MCPToolServer:
    """
    MCP-compatible tool server for business operations.
    
    Exposes tools following the Model Context Protocol specification.
    Tools can be called by agents to perform business operations.
    
    Usage:
        server = MCPToolServer()
        result = await server.call_tool("get_order_details", {
            "order_id": "ORD-2024-001",
            "email": "alice@example.com"
        })
    """
    
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register all default business tools."""
        
        # Order tools
        self.register_tool(ToolDefinition(
            name="get_order_details",
            description="Retrieve order information by order ID. Requires customer email for verification.",
            parameters=[
                ToolParameter(
                    name="order_id",
                    type="string",
                    description="The order identifier (e.g., ORD-2024-001)"
                ),
                ToolParameter(
                    name="email",
                    type="string",
                    description="Customer email for ownership verification"
                ),
            ],
            handler=self._handle_get_order_details,
            requires_auth=True,
        ))
        
        self.register_tool(ToolDefinition(
            name="get_refund_policy",
            description="Get refund eligibility and policy information for an order.",
            parameters=[
                ToolParameter(
                    name="order_id",
                    type="string",
                    description="The order identifier"
                ),
            ],
            handler=self._handle_get_refund_policy,
            requires_auth=False,
        ))
        
        # Customer tools
        self.register_tool(ToolDefinition(
            name="get_customer_profile",
            description="Retrieve customer profile information by email. Returns masked PII.",
            parameters=[
                ToolParameter(
                    name="email",
                    type="string",
                    description="Customer email address"
                ),
            ],
            handler=self._handle_get_customer_profile,
            requires_auth=True,
        ))
        
        # Ticket tools
        self.register_tool(ToolDefinition(
            name="create_support_ticket",
            description="Create a support ticket for tracking customer issues.",
            parameters=[
                ToolParameter(
                    name="customer_email",
                    type="string",
                    description="Customer email address"
                ),
                ToolParameter(
                    name="intent",
                    type="string",
                    description="Classified intent type"
                ),
                ToolParameter(
                    name="priority",
                    type="string",
                    description="Priority level (low, medium, high, urgent)"
                ),
                ToolParameter(
                    name="summary",
                    type="string",
                    description="Brief summary of the issue"
                ),
            ],
            handler=self._handle_create_support_ticket,
            requires_auth=False,
        ))
        
        # Security tools
        self.register_tool(ToolDefinition(
            name="mask_sensitive_data",
            description="Mask PII (credit cards, emails, phones, SSNs) in text.",
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="Text potentially containing sensitive data"
                ),
            ],
            handler=self._handle_mask_sensitive_data,
            requires_auth=False,
        ))
        
        self.register_tool(ToolDefinition(
            name="audit_log_event",
            description="Log an audit event for compliance tracking.",
            parameters=[
                ToolParameter(
                    name="event_type",
                    type="string",
                    description="Type of event (e.g., tool_call, data_access)"
                ),
                ToolParameter(
                    name="payload",
                    type="object",
                    description="Event-specific data"
                ),
            ],
            handler=self._handle_audit_log_event,
            requires_auth=False,
        ))
    
    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a new tool with the server."""
        self._tools[tool.name] = tool
        logger.debug("tool_registered", tool_name=tool.name)
    
    def list_tools(self) -> list[dict]:
        """
        List all available tools in MCP format.
        
        Returns:
            List of tool definitions with name, description, and parameters
        """
        tools = []
        for tool in self._tools.values():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p.name: {
                            "type": p.type,
                            "description": p.description,
                        }
                        for p in tool.parameters
                    },
                    "required": [p.name for p in tool.parameters if p.required],
                },
            })
        return tools
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
        context: Optional[dict] = None,
    ) -> ToolCallResult:
        """
        Call a tool by name with the given arguments.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of argument values
            context: Optional context (session info, etc.)
            
        Returns:
            ToolCallResult with success status and data or error
        """
        if tool_name not in self._tools:
            return ToolCallResult(
                success=False,
                error=f"Unknown tool: {tool_name}",
                tool_name=tool_name,
            )
        
        tool = self._tools[tool_name]
        
        # Validate required parameters
        for param in tool.parameters:
            if param.required and param.name not in arguments:
                return ToolCallResult(
                    success=False,
                    error=f"Missing required parameter: {param.name}",
                    tool_name=tool_name,
                )
        
        # Log the tool call
        logger.info(
            "tool_call",
            tool_name=tool_name,
            has_context=context is not None,
        )
        
        try:
            result = await tool.handler(arguments, context)
            return ToolCallResult(
                success=True,
                data=result,
                tool_name=tool_name,
            )
        except Exception as e:
            logger.error("tool_call_error", tool_name=tool_name, error=str(e))
            return ToolCallResult(
                success=False,
                error=str(e),
                tool_name=tool_name,
            )
    
    # Tool handlers
    
    async def _handle_get_order_details(
        self,
        args: dict,
        context: Optional[dict] = None,
    ) -> Optional[dict]:
        """Handle get_order_details tool call."""
        result = get_order_details(args["order_id"], args["email"])
        if result:
            return result.model_dump()
        return None
    
    async def _handle_get_refund_policy(
        self,
        args: dict,
        context: Optional[dict] = None,
    ) -> Optional[dict]:
        """Handle get_refund_policy tool call."""
        result = get_refund_policy(args["order_id"])
        if result:
            return result.model_dump()
        return None
    
    async def _handle_get_customer_profile(
        self,
        args: dict,
        context: Optional[dict] = None,
    ) -> Optional[dict]:
        """Handle get_customer_profile tool call."""
        result = get_customer_profile(args["email"])
        if result:
            return result.model_dump()
        return None
    
    async def _handle_create_support_ticket(
        self,
        args: dict,
        context: Optional[dict] = None,
    ) -> dict:
        """Handle create_support_ticket tool call."""
        result = create_support_ticket(
            customer_email=args["customer_email"],
            intent=args["intent"],
            priority=args["priority"],
            summary=args["summary"],
        )
        return result.model_dump()
    
    async def _handle_mask_sensitive_data(
        self,
        args: dict,
        context: Optional[dict] = None,
    ) -> str:
        """Handle mask_sensitive_data tool call."""
        return mask_sensitive_data(args["text"])
    
    async def _handle_audit_log_event(
        self,
        args: dict,
        context: Optional[dict] = None,
    ) -> dict:
        """Handle audit_log_event tool call."""
        return audit_log_event(
            event_type=args["event_type"],
            payload=args.get("payload", {}),
            session_id=context.get("session_id") if context else None,
        )
    
    def get_tool_schema_for_llm(self) -> str:
        """
        Get tool definitions formatted for LLM function calling.
        
        Returns:
            JSON string of tool definitions
        """
        return json.dumps(self.list_tools(), indent=2)
