"""Base agent class and common interfaces."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field

from src.schemas.message import AgentResponse, ConversationContext


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    
    name: str
    description: str
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.3
    max_tokens: int = 1024
    system_prompt: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Agents are specialized components that handle specific tasks
    in the customer support pipeline. Each agent:
    - Has a defined role and responsibility
    - Receives input and produces structured output
    - May use tools via the MCP server
    - Logs its actions for audit
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self._llm_client = None
    
    @property
    def llm_client(self):
        """Lazy initialization of LLM client."""
        if self._llm_client is None:
            self._llm_client = self._create_llm_client()
        return self._llm_client
    
    def _create_llm_client(self):
        """Create the LLM client. Override for custom clients."""
        try:
            import google.generativeai as genai
            from src.config import settings
            
            if settings.google_api_key:
                genai.configure(api_key=settings.google_api_key)
                return genai.GenerativeModel(self.config.model_name)
            else:
                return None
        except ImportError:
            return None
    
    @abstractmethod
    async def process(
        self,
        input_data: Any,
        context: Optional[ConversationContext] = None,
    ) -> AgentResponse:
        """
        Process input and return a response.
        
        Args:
            input_data: The input to process (type depends on agent)
            context: Optional conversation context
            
        Returns:
            AgentResponse with the agent's output
        """
        pass
    
    def _create_response(
        self,
        content: str,
        confidence: float = 1.0,
        tools_used: list[str] = None,
        metadata: dict = None,
        next_action: str = None,
        requires_escalation: bool = False,
    ) -> AgentResponse:
        """Helper to create a standardized AgentResponse."""
        return AgentResponse(
            agent_name=self.name,
            content=content,
            confidence=confidence,
            tools_used=tools_used or [],
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
            next_action=next_action,
            requires_escalation=requires_escalation,
        )
    
    async def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Call the LLM with the given prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt override
            
        Returns:
            The LLM response text, or None if unavailable
        """
        if self.llm_client is None:
            return None
        
        try:
            # Use system prompt from config if not overridden
            sys_prompt = system_prompt or self.config.system_prompt or ""
            
            full_prompt = f"{sys_prompt}\n\n{prompt}" if sys_prompt else prompt
            
            response = self.llm_client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                }
            )
            
            return response.text
        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.error("llm_call_error", agent=self.name, error=str(e))
            return None
