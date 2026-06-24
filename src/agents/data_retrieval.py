"""Data Retrieval Agent."""

from typing import Any, Optional

from src.agents.base import BaseAgent, AgentConfig
from src.schemas.message import AgentResponse, ConversationContext
from src.schemas.intent import ClassificationResult, IntentType
from src.mcp_server.server import MCPToolServer
from src.security.guardrails import SecurityGuardrail


class DataRetrievalAgent(BaseAgent):
    """
    Agent responsible for retrieving business data via MCP tools.
    
    This agent:
    - Determines which tools to call based on intent
    - Validates access permissions before data retrieval
    - Aggregates data from multiple sources if needed
    """
    
    def __init__(self, mcp_server: Optional[MCPToolServer] = None):
        config = AgentConfig(
            name="DataRetrieval",
            description="Retrieves business data through MCP tools",
            temperature=0.0,  # Deterministic tool selection
            max_tokens=256,
        )
        super().__init__(config)
        self.mcp_server = mcp_server or MCPToolServer()
        self.guardrail = SecurityGuardrail()
    
    async def process(
        self,
        input_data: dict,
        context: Optional[ConversationContext] = None,
    ) -> AgentResponse:
        """
        Retrieve relevant data based on classification result.
        
        Args:
            input_data: Dictionary with 'classification' (ClassificationResult)
                       and 'customer_email' (if verified)
            context: Conversation context for authorization
            
        Returns:
            AgentResponse with retrieved data in metadata
        """
        classification = input_data.get("classification")
        customer_email = input_data.get("customer_email")
        
        if not classification:
            return self._create_response(
                content="No classification provided",
                confidence=0.0,
                metadata={"error": "missing_classification"},
            )
        
        # Parse classification if it's a dict
        if isinstance(classification, dict):
            classification = ClassificationResult(**classification)
        
        # Determine which tools to call
        tools_to_call = self._determine_tools(classification)
        
        # Execute tool calls
        retrieved_data = {}
        tools_used = []
        errors = []
        
        for tool_name, tool_args in tools_to_call:
            # Add email for authorization if needed
            if "email" in tool_args and not tool_args["email"]:
                tool_args["email"] = customer_email
            
            # Security check for data access
            if tool_name in ["get_order_details", "get_customer_profile"]:
                resource_id = tool_args.get("order_id") or tool_args.get("email")
                guardrail_result = self.guardrail.check_data_access(
                    resource_type="order" if "order" in tool_name else "customer",
                    resource_id=resource_id or "",
                    requesting_email=customer_email,
                    context=context,
                )
                
                if not guardrail_result.passed:
                    errors.append({
                        "tool": tool_name,
                        "error": guardrail_result.blocked_reason,
                    })
                    continue
            
            # Call the tool
            result = await self.mcp_server.call_tool(
                tool_name=tool_name,
                arguments=tool_args,
                context={"session_id": context.session_id} if context else None,
            )
            
            if result.success:
                retrieved_data[tool_name] = result.data
                tools_used.append(tool_name)
            else:
                errors.append({
                    "tool": tool_name,
                    "error": result.error,
                })
        
        # Build response
        has_data = bool(retrieved_data)
        
        return self._create_response(
            content=f"Retrieved data from {len(tools_used)} tool(s)" if has_data else "No data retrieved",
            confidence=1.0 if has_data else 0.5,
            tools_used=tools_used,
            metadata={
                "data": retrieved_data,
                "errors": errors if errors else None,
            },
            next_action="response_generation",
        )
    
    def _determine_tools(
        self,
        classification: ClassificationResult,
    ) -> list[tuple[str, dict]]:
        """Determine which tools to call based on intent."""
        tools = []
        intent = classification.primary_intent.type
        entities = classification.extracted_entities
        
        order_id = entities.get("order_id")
        email = entities.get("email")
        
        if intent == IntentType.ORDER_STATUS:
            if order_id:
                tools.append(("get_order_details", {
                    "order_id": order_id,
                    "email": email,
                }))
        
        elif intent == IntentType.REFUND_REQUEST:
            if order_id:
                tools.append(("get_order_details", {
                    "order_id": order_id,
                    "email": email,
                }))
                tools.append(("get_refund_policy", {
                    "order_id": order_id,
                }))
        
        elif intent == IntentType.BILLING_ISSUE:
            if order_id:
                tools.append(("get_order_details", {
                    "order_id": order_id,
                    "email": email,
                }))
            if email:
                tools.append(("get_customer_profile", {
                    "email": email,
                }))
        
        elif intent == IntentType.ACCOUNT_ACCESS:
            if email:
                tools.append(("get_customer_profile", {
                    "email": email,
                }))
        
        elif intent == IntentType.SHIPPING_ISSUE:
            if order_id:
                tools.append(("get_order_details", {
                    "order_id": order_id,
                    "email": email,
                }))
        
        return tools
