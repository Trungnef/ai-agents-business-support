"""Intent Classification Agent."""

import json
import re
from typing import Any, Optional

from src.agents.base import BaseAgent, AgentConfig
from src.schemas.message import AgentResponse, ConversationContext
from src.schemas.intent import IntentType, Priority, ClassificationResult, Intent


INTENT_CLASSIFIER_PROMPT = """You are an intent classification agent for a customer support system.

Analyze the customer message and classify it into one of these intents:
- refund_request: Customer wants money back or to return an item
- order_status: Customer asking about order location, delivery, or tracking
- billing_issue: Problems with payment, charges, or invoices
- account_access: Login problems, password issues, account locked
- shipping_issue: Package lost, damaged, delayed, wrong address
- human_escalation: Customer explicitly asks for human agent or manager
- other: Anything that doesn't fit above categories

Also determine the priority:
- urgent: Angry customer, threatening legal action, large order, security issue
- high: Time-sensitive, customer frustrated, payment problem
- medium: Standard request needing attention
- low: General inquiry, not time-sensitive

Extract any entities mentioned:
- order_id: Any order number (format: ORD-XXXX-XXX)
- email: Any email address mentioned
- amount: Any dollar amounts mentioned

Respond ONLY with valid JSON in this exact format:
{
    "intent": "one_of_the_intent_types",
    "confidence": 0.95,
    "priority": "low|medium|high|urgent",
    "requires_human": false,
    "entities": {
        "order_id": "if_found_or_null",
        "email": "if_found_or_null",
        "amount": "if_found_or_null"
    },
    "reasoning": "Brief explanation of classification"
}

Customer message to classify:
"""


class IntentClassifierAgent(BaseAgent):
    """
    Agent responsible for classifying customer intent and priority.
    
    This is typically the first agent in the pipeline, analyzing
    the customer's message to determine what they need.
    """
    
    def __init__(self):
        config = AgentConfig(
            name="IntentClassifier",
            description="Classifies customer intent and extracts entities",
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=512,
            system_prompt=INTENT_CLASSIFIER_PROMPT,
        )
        super().__init__(config)
    
    async def process(
        self,
        input_data: str,
        context: Optional[ConversationContext] = None,
    ) -> AgentResponse:
        """
        Classify the customer's intent.
        
        Args:
            input_data: The customer's message text
            context: Optional conversation context
            
        Returns:
            AgentResponse containing ClassificationResult in metadata
        """
        # Try LLM classification first
        llm_result = await self._classify_with_llm(input_data)
        
        if llm_result:
            classification = llm_result
        else:
            # Fallback to rule-based classification
            classification = self._classify_with_rules(input_data)
        
        # Build response
        return self._create_response(
            content=f"Classified as {classification.primary_intent.type} with {classification.priority} priority",
            confidence=classification.primary_intent.confidence,
            metadata={
                "classification": classification.model_dump(),
            },
            next_action="data_retrieval" if self._needs_data(classification) else "response_generation",
            requires_escalation=classification.requires_human,
        )
    
    async def _classify_with_llm(
        self,
        message: str,
    ) -> Optional[ClassificationResult]:
        """Classify using LLM."""
        prompt = f"{INTENT_CLASSIFIER_PROMPT}\n\n\"{message}\""
        
        response = await self._call_llm(prompt)
        
        if not response:
            return None
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if not json_match:
                return None
            
            data = json.loads(json_match.group())
            
            # Parse into schema
            intent_type = IntentType(data.get("intent", "other"))
            
            return ClassificationResult(
                primary_intent=Intent(
                    type=intent_type,
                    confidence=float(data.get("confidence", 0.8)),
                ),
                secondary_intents=[],
                priority=Priority(data.get("priority", "medium")),
                requires_human=data.get("requires_human", False),
                extracted_entities=data.get("entities", {}),
                reasoning=data.get("reasoning"),
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return None
    
    def _classify_with_rules(self, message: str) -> ClassificationResult:
        """Rule-based fallback classification."""
        message_lower = message.lower()
        
        # Intent detection rules
        intent = IntentType.OTHER
        confidence = 0.7
        
        if any(w in message_lower for w in ["refund", "money back", "return", "reimburse"]):
            intent = IntentType.REFUND_REQUEST
            confidence = 0.85
        elif any(w in message_lower for w in [
            "where is my order", "order status", "tracking", "delivery", "shipped",
            "track my", "package", "when will", "arrive", "status of"
        ]):
            intent = IntentType.ORDER_STATUS
            confidence = 0.85
        elif any(w in message_lower for w in ["charged", "billing", "invoice", "payment", "double charged"]):
            intent = IntentType.BILLING_ISSUE
            confidence = 0.85
        elif any(w in message_lower for w in [
            "login", "log in", "password", "can't access", "cannot access", "locked out", 
            "account", "sign in", "forgot"
        ]):
            intent = IntentType.ACCOUNT_ACCESS
            confidence = 0.85
        elif any(w in message_lower for w in ["lost package", "damaged", "wrong item", "shipping"]):
            intent = IntentType.SHIPPING_ISSUE
            confidence = 0.85
        elif any(w in message_lower for w in ["speak to", "human", "manager", "supervisor", "real person"]):
            intent = IntentType.HUMAN_ESCALATION
            confidence = 0.9
        
        # Priority detection
        priority = Priority.MEDIUM
        if any(w in message_lower for w in ["urgent", "immediately", "asap", "right now"]):
            priority = Priority.URGENT
        elif any(w in message_lower for w in ["angry", "frustrated", "unacceptable", "legal", "lawyer"]):
            priority = Priority.URGENT
        elif any(w in message_lower for w in ["important", "need help", "please help"]):
            priority = Priority.HIGH
        
        # Entity extraction
        entities = {}
        
        # Extract order ID
        order_match = re.search(r'ORD-\d{4}-\d{3}', message, re.IGNORECASE)
        if order_match:
            entities["order_id"] = order_match.group().upper()
        
        # Extract email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
        if email_match:
            entities["email"] = email_match.group().lower()
        
        # Extract amount
        amount_match = re.search(r'\$[\d,]+\.?\d*', message)
        if amount_match:
            entities["amount"] = amount_match.group()
        
        return ClassificationResult(
            primary_intent=Intent(type=intent, confidence=confidence),
            secondary_intents=[],
            priority=priority,
            requires_human=intent == IntentType.HUMAN_ESCALATION,
            extracted_entities=entities,
            reasoning="Rule-based classification (LLM unavailable)",
        )
    
    def _needs_data(self, classification: ClassificationResult) -> bool:
        """Determine if this intent needs data retrieval."""
        data_intents = {
            IntentType.ORDER_STATUS,
            IntentType.REFUND_REQUEST,
            IntentType.BILLING_ISSUE,
            IntentType.SHIPPING_ISSUE,
        }
        return classification.primary_intent.type in data_intents
