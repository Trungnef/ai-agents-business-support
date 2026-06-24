"""
FastAPI application for the Multi-Agent Customer Support Assistant.

Provides REST endpoints for:
- /chat - Main chat endpoint for customer messages
- /session/{id} - Session management
- /health - Health check
- /tools - List available MCP tools
"""

from datetime import datetime
from typing import Optional
import asyncio

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

from src.orchestrator import SupportOrchestrator
from src.schemas.message import CustomerMessage
from src.mcp_server.server import MCPToolServer


logger = structlog.get_logger(__name__)


# Request/Response models
class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    
    message: str = Field(..., min_length=1, max_length=5000, description="Customer message")
    email: Optional[str] = Field(default=None, description="Customer email for verification")
    order_id: Optional[str] = Field(default=None, description="Order ID if known")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    
    message: str = Field(..., description="Assistant's response")
    session_id: str = Field(..., description="Session ID for follow-up messages")
    intent: str = Field(..., description="Detected intent")
    priority: str = Field(..., description="Request priority")
    ticket_id: Optional[str] = Field(default=None, description="Support ticket ID if created")
    tools_used: list[str] = Field(default_factory=list, description="MCP tools invoked")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class SessionResponse(BaseModel):
    """Session information response."""
    
    session_id: str
    customer_email: Optional[str]
    message_count: int
    intent_history: list[str]
    verified_order_ids: list[str]
    created_at: str
    last_activity: str


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    timestamp: str
    version: str


class ToolInfo(BaseModel):
    """Information about an MCP tool."""
    
    name: str
    description: str
    parameters: dict


# Application factory
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Multi-Agent Customer Support API",
        description="AI-powered customer support assistant using multi-agent architecture",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware for web clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store orchestrator instance in app state
    app.state.orchestrator = None
    app.state.mcp_server = None
    
    @app.on_event("startup")
    async def startup():
        """Initialize services on startup."""
        logger.info("starting_api_server")
        app.state.orchestrator = SupportOrchestrator(use_persistent_storage=True)
        app.state.mcp_server = MCPToolServer()
    
    @app.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown."""
        logger.info("shutting_down_api_server")
        # Clean up expired sessions
        if app.state.orchestrator:
            app.state.orchestrator.cleanup_expired_sessions()
    
    return app


# Create the app instance
app = create_app()


# Dependency to get orchestrator
def get_orchestrator() -> SupportOrchestrator:
    """Get the orchestrator instance."""
    if app.state.orchestrator is None:
        app.state.orchestrator = SupportOrchestrator(use_persistent_storage=True)
    return app.state.orchestrator


def get_mcp_server() -> MCPToolServer:
    """Get the MCP server instance."""
    if app.state.mcp_server is None:
        app.state.mcp_server = MCPToolServer()
    return app.state.mcp_server


# Endpoints
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0",
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    orchestrator: SupportOrchestrator = Depends(get_orchestrator),
):
    """
    Process a customer message and return an AI-generated response.
    
    This endpoint:
    1. Classifies the customer's intent
    2. Retrieves relevant business data (if needed)
    3. Generates a helpful response
    4. Applies safety checks and PII masking
    
    Use `session_id` to maintain conversation context across multiple messages.
    """
    logger.info(
        "chat_request",
        has_email=bool(request.email),
        has_order=bool(request.order_id),
        has_session=bool(request.session_id),
    )
    
    try:
        # Create message object
        message = CustomerMessage(
            content=request.message,
            customer_email=request.email,
            order_id=request.order_id,
            session_id=request.session_id,
        )
        
        # Process through orchestrator
        response = await orchestrator.process(message, request.session_id)
        
        return ChatResponse(
            message=response.message,
            session_id=response.session_id,
            intent=response.intent_detected,
            priority=response.priority,
            ticket_id=response.ticket_created,
            tools_used=response.tools_used,
            processing_time_ms=response.processing_time_ms or 0,
        )
        
    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process message")


@app.get("/session/{session_id}", response_model=SessionResponse, tags=["Session"])
async def get_session(
    session_id: str,
    orchestrator: SupportOrchestrator = Depends(get_orchestrator),
):
    """Get information about an existing session."""
    context = orchestrator.get_session(session_id)
    
    if context is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=context.session_id,
        customer_email=context.customer_email,
        message_count=len(context.messages),
        intent_history=context.intent_history,
        verified_order_ids=context.verified_order_ids,
        created_at=context.created_at.isoformat(),
        last_activity=context.last_activity.isoformat(),
    )


@app.delete("/session/{session_id}", tags=["Session"])
async def delete_session(
    session_id: str,
    orchestrator: SupportOrchestrator = Depends(get_orchestrator),
):
    """Delete a session and its history."""
    success = orchestrator.clear_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "deleted", "session_id": session_id}


@app.get("/session/{session_id}/history", tags=["Session"])
async def get_session_history(
    session_id: str,
    orchestrator: SupportOrchestrator = Depends(get_orchestrator),
):
    """Get conversation history for a session."""
    history = orchestrator.get_conversation_history(session_id)
    
    if not history:
        context = orchestrator.get_session(session_id)
        if context is None:
            raise HTTPException(status_code=404, detail="Session not found")
    
    return {"session_id": session_id, "messages": history}


@app.get("/tools", response_model=list[ToolInfo], tags=["MCP"])
async def list_tools(
    mcp_server: MCPToolServer = Depends(get_mcp_server),
):
    """List all available MCP tools."""
    tools = mcp_server.list_tools()
    return [
        ToolInfo(
            name=tool["name"],
            description=tool["description"],
            parameters=tool.get("parameters", {}),
        )
        for tool in tools
    ]


@app.post("/tools/{tool_name}/call", tags=["MCP"])
async def call_tool(
    tool_name: str,
    arguments: dict,
    mcp_server: MCPToolServer = Depends(get_mcp_server),
):
    """
    Directly call an MCP tool (for testing/debugging).
    
    Note: In production, tool calls should go through the chat endpoint
    where proper authorization and safety checks are applied.
    """
    result = await mcp_server.call_tool(tool_name, arguments)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {"tool": tool_name, "result": result.data}


# CLI runner for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
