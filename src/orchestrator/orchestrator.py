"""Main orchestrator for the multi-agent customer support system."""

import uuid
from datetime import datetime
from typing import Optional, Union
import structlog

from src.agents.intent_classifier import IntentClassifierAgent
from src.agents.data_retrieval import DataRetrievalAgent
from src.agents.response_generator import ResponseGeneratorAgent
from src.agents.quality_safety import QualitySafetyAgent
from src.mcp_server.server import MCPToolServer
from src.security.guardrails import SecurityGuardrail
from src.tools.ticket_tools import create_support_ticket
from src.tools.security_tools import audit_log_event
from src.schemas.message import (
    CustomerMessage,
    ConversationContext,
    FinalResponse,
)
from src.schemas.intent import Priority
from src.memory.session_store import SessionStore, SQLiteSessionStore, InMemorySessionStore


logger = structlog.get_logger(__name__)


class SupportOrchestrator:
    """
    Main orchestrator that coordinates the multi-agent pipeline.
    
    Flow:
    1. Receive customer message
    2. Validate input (security guardrail)
    3. Classify intent
    4. Retrieve data (if needed)
    5. Generate response
    6. Quality/safety check
    7. Optionally create ticket
    8. Return final response
    
    The orchestrator maintains conversation context across multiple
    interactions and handles error recovery.
    
    Session Memory:
    - Supports both in-memory and SQLite-based session storage
    - Maintains conversation history for multi-turn interactions
    - Uses context from previous messages to resolve follow-ups like "Can I refund it?"
    """
    
    def __init__(
        self,
        session_store: Optional[SessionStore] = None,
        use_persistent_storage: bool = True,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            session_store: Custom session store. If None, creates default.
            use_persistent_storage: If True (default), use SQLite. Otherwise, in-memory.
        """
        # Initialize MCP server
        self.mcp_server = MCPToolServer()
        
        # Initialize agents
        self.intent_classifier = IntentClassifierAgent()
        self.data_retrieval = DataRetrievalAgent(self.mcp_server)
        self.response_generator = ResponseGeneratorAgent()
        self.quality_safety = QualitySafetyAgent()
        
        # Security
        self.guardrail = SecurityGuardrail()
        
        # Session storage - supports both in-memory and persistent
        if session_store:
            self._session_store = session_store
        elif use_persistent_storage:
            self._session_store = SQLiteSessionStore()
        else:
            self._session_store = InMemorySessionStore()
        
        # Legacy in-memory fallback (for backward compatibility)
        self._sessions: dict[str, ConversationContext] = {}
    
    async def process(
        self,
        message: CustomerMessage,
        session_id: Optional[str] = None,
    ) -> FinalResponse:
        """
        Process a customer message through the agent pipeline.
        
        Args:
            message: The customer's message
            session_id: Optional session ID to continue a conversation
            
        Returns:
            FinalResponse with the customer-facing message and metadata
        """
        start_time = datetime.utcnow()
        tools_used = []
        
        # Get or create session context
        session_id = session_id or message.session_id or str(uuid.uuid4())
        context = self._get_or_create_context(session_id, message)
        
        logger.info(
            "processing_message",
            session_id=session_id,
            has_email=bool(message.customer_email),
            has_order_id=bool(message.order_id),
        )
        
        try:
            # Step 1: Input validation
            input_check = self.guardrail.validate_input(message.content, context)
            if not input_check.passed:
                return self._create_error_response(
                    input_check.blocked_reason or "Invalid input",
                    session_id,
                    start_time,
                )
            
            if input_check.warnings:
                logger.warning("input_warnings", warnings=input_check.warnings)
            
            # Step 2: Intent classification
            classification_response = await self.intent_classifier.process(
                input_data=message.content,
                context=context,
            )
            
            classification = classification_response.metadata.get("classification", {})
            intent = classification.get("primary_intent", {}).get("type", "other")
            priority = classification.get("priority", "medium")
            
            logger.info(
                "intent_classified",
                intent=intent,
                priority=priority,
                confidence=classification.get("primary_intent", {}).get("confidence", 0),
            )
            
            # Update context with intent
            context.intent_history.append(intent)
            
            # Step 3: Data retrieval (if needed)
            retrieved_data = {}
            if classification_response.next_action == "data_retrieval":
                # Merge email from context if available
                customer_email = message.customer_email or context.customer_email
                
                retrieval_response = await self.data_retrieval.process(
                    input_data={
                        "classification": classification,
                        "customer_email": customer_email,
                    },
                    context=context,
                )
                
                retrieved_data = retrieval_response.metadata.get("data", {})
                tools_used.extend(retrieval_response.tools_used)
                
                # Log tool calls to context
                for tool in retrieval_response.tools_used:
                    context.tools_called.append({
                        "tool": tool,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            
            # Step 4: Response generation
            generator_response = await self.response_generator.process(
                input_data={
                    "classification": classification,
                    "retrieved_data": retrieved_data,
                    "original_message": message.content,
                },
                context=context,
            )
            
            draft_response = generator_response.content
            
            # Step 5: Quality and safety check
            quality_response = await self.quality_safety.process(
                input_data={
                    "draft_response": draft_response,
                    "customer_email": message.customer_email or context.customer_email,
                },
                context=context,
            )
            
            final_message = quality_response.content
            requires_escalation = (
                quality_response.requires_escalation or
                classification_response.requires_escalation
            )
            
            # Step 6: Create ticket if needed
            ticket_id = None
            if self._should_create_ticket(intent, priority, requires_escalation):
                ticket_result = create_support_ticket(
                    customer_email=message.customer_email or context.customer_email or "unknown@customer.com",
                    intent=intent,
                    priority=priority,
                    summary=message.content[:200],
                )
                ticket_id = ticket_result.ticket_id
                tools_used.append("create_support_ticket")
                
                logger.info("ticket_created", ticket_id=ticket_id)
            
            # Update context
            context.messages.append({
                "role": "user",
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            })
            context.messages.append({
                "role": "assistant",
                "content": final_message,
                "timestamp": datetime.utcnow().isoformat(),
            })
            context.last_activity = datetime.utcnow()
            
            # Store any order IDs mentioned in this interaction
            entities = classification.get("extracted_entities", {})
            if entities.get("order_id") and entities["order_id"] not in context.verified_order_ids:
                context.verified_order_ids.append(entities["order_id"])
            
            # Persist context to session store
            self._save_context(context)
            
            # Calculate processing time
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Audit log
            audit_log_event(
                event_type="response_sent",
                payload={
                    "intent": intent,
                    "priority": priority,
                    "tools_used": tools_used,
                    "ticket_created": ticket_id is not None,
                    "processing_time_ms": processing_time,
                },
                session_id=session_id,
                customer_email=message.customer_email,
            )
            
            return FinalResponse(
                message=final_message,
                intent_detected=intent,
                priority=priority,
                ticket_created=ticket_id,
                tools_used=tools_used,
                session_id=session_id,
                requires_followup=requires_escalation,
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            logger.error("orchestrator_error", error=str(e), session_id=session_id)
            return self._create_error_response(
                "An unexpected error occurred. Please try again.",
                session_id,
                start_time,
            )
    
    def _get_or_create_context(
        self,
        session_id: str,
        message: CustomerMessage,
    ) -> ConversationContext:
        """
        Get existing context from session store or create new one.
        
        Supports multi-turn conversations by preserving:
        - Customer email for identity
        - Verified order IDs for quick access
        - Intent history for context-aware responses
        - Conversation history for follow-up handling
        """
        # Try to get from persistent store first
        context = self._session_store.get(session_id)
        
        if context:
            # Update email if provided and not already set
            if message.customer_email and not context.customer_email:
                context.customer_email = message.customer_email
            # Add new order ID if provided
            if message.order_id and message.order_id not in context.verified_order_ids:
                context.verified_order_ids.append(message.order_id)
            return context
        
        # Fallback to legacy in-memory store
        if session_id in self._sessions:
            context = self._sessions[session_id]
            if message.customer_email and not context.customer_email:
                context.customer_email = message.customer_email
            return context
        
        # Create new context
        context = ConversationContext(
            session_id=session_id,
            customer_email=message.customer_email,
            verified_order_ids=[message.order_id] if message.order_id else [],
        )
        
        # Store in both places for compatibility
        self._sessions[session_id] = context
        return context
    
    def _save_context(self, context: ConversationContext) -> None:
        """Save context to both session store and legacy dict."""
        self._session_store.save(context)
        self._sessions[context.session_id] = context
    
    def _should_create_ticket(
        self,
        intent: str,
        priority: str,
        requires_escalation: bool,
    ) -> bool:
        """Determine if a support ticket should be created."""
        # Always create ticket for escalations
        if requires_escalation:
            return True
        
        # Create ticket for high/urgent priority
        if priority in ["high", "urgent"]:
            return True
        
        # Create ticket for certain intents
        ticket_intents = ["human_escalation", "billing_issue", "account_access"]
        if intent in ticket_intents:
            return True
        
        return False
    
    def _create_error_response(
        self,
        error_message: str,
        session_id: str,
        start_time: datetime,
    ) -> FinalResponse:
        """Create an error response."""
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return FinalResponse(
            message=(
                "I apologize, but I'm having trouble processing your request right now. "
                f"{error_message}\n\n"
                "Please try again, or type 'speak to human' to connect with a support agent."
            ),
            intent_detected="error",
            priority="medium",
            ticket_created=None,
            tools_used=[],
            session_id=session_id,
            requires_followup=True,
            processing_time_ms=processing_time,
        )
    
    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """Get a session context by ID."""
        # Try persistent store first
        context = self._session_store.get(session_id)
        if context:
            return context
        # Fallback to legacy
        return self._sessions.get(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session from both stores."""
        deleted_persistent = self._session_store.delete(session_id)
        deleted_memory = session_id in self._sessions
        if deleted_memory:
            del self._sessions[session_id]
        return deleted_persistent or deleted_memory
    
    def get_conversation_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        context = self.get_session(session_id)
        if context:
            return context.messages
        return []
    
    def resolve_follow_up_context(
        self,
        message: str,
        context: ConversationContext,
    ) -> dict:
        """
        Resolve contextual references in follow-up messages.
        
        Handles messages like:
        - "Can I refund it?" -> Resolves 'it' to the last mentioned order
        - "What about that order?" -> Uses last order from context
        - "Yes, proceed" -> Continues previous action
        
        Returns:
            Dict with resolved entities (order_id, action, etc.)
        """
        resolved = {}
        message_lower = message.lower()
        
        # Check for pronouns referring to previous order
        pronoun_patterns = ["it", "that", "this order", "the order", "my order"]
        has_pronoun = any(p in message_lower for p in pronoun_patterns)
        
        if has_pronoun and context.verified_order_ids:
            # Use most recently mentioned order
            resolved["order_id"] = context.verified_order_ids[-1]
        
        # Check for continuation patterns
        continuation_patterns = ["yes", "proceed", "go ahead", "do it", "confirm"]
        if any(p in message_lower for p in continuation_patterns):
            # Get last intent for context
            if context.intent_history:
                resolved["continuing_intent"] = context.intent_history[-1]
        
        # Check for refund follow-up
        if "refund" in message_lower and "order_id" in resolved:
            resolved["action"] = "refund_request"
        
        return resolved
    
    def cleanup_expired_sessions(self, max_age_minutes: int = 30) -> int:
        """Clean up expired sessions from persistent store."""
        return self._session_store.cleanup_expired(max_age_minutes)
