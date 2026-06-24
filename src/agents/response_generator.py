"""Response Generator Agent."""

import json
from typing import Any, Optional

from src.agents.base import BaseAgent, AgentConfig
from src.schemas.message import AgentResponse, ConversationContext
from src.schemas.intent import IntentType, Priority


RESPONSE_GENERATOR_PROMPT = """You are a friendly customer support assistant for an online business.

Guidelines:
1. Be warm, professional, and empathetic
2. Use "you" and "we" language
3. Never reveal internal IDs, full credit card numbers, or internal notes
4. If information is missing, politely ask for it
5. Always offer next steps or ask if there's anything else you can help with
6. Keep responses concise but complete

You will receive:
- Customer's intent
- Priority level
- Retrieved data (order info, customer profile, etc.)
- The original customer message

Generate a helpful response that addresses their needs.
If no data was retrieved, politely explain what information you need from them.

IMPORTANT: Never make up order details, tracking numbers, or dates. Only use the data provided.
"""


class ResponseGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating customer-facing responses.
    
    This agent:
    - Takes the intent, retrieved data, and context
    - Generates a natural, helpful response
    - Ensures the response is appropriate and complete
    """
    
    def __init__(self):
        config = AgentConfig(
            name="ResponseGenerator",
            description="Generates customer-facing support responses",
            temperature=0.7,  # Some creativity for natural responses
            max_tokens=1024,
            system_prompt=RESPONSE_GENERATOR_PROMPT,
        )
        super().__init__(config)
    
    async def process(
        self,
        input_data: dict,
        context: Optional[ConversationContext] = None,
    ) -> AgentResponse:
        """
        Generate a response based on intent and data.
        
        Args:
            input_data: Dictionary with:
                - 'classification': The intent classification
                - 'retrieved_data': Data from tools
                - 'original_message': Customer's message
            context: Conversation context
            
        Returns:
            AgentResponse with the draft customer response
        """
        classification = input_data.get("classification", {})
        retrieved_data = input_data.get("retrieved_data", {})
        original_message = input_data.get("original_message", "")
        
        # Get intent and priority
        if isinstance(classification, dict):
            intent = classification.get("primary_intent", {}).get("type", "other")
            priority = classification.get("priority", "medium")
        else:
            intent = classification.primary_intent.type
            priority = classification.priority
        
        # Try LLM generation
        llm_response = await self._generate_with_llm(
            intent=intent,
            priority=priority,
            data=retrieved_data,
            original_message=original_message,
        )
        
        if llm_response:
            response_text = llm_response
        else:
            # Fallback to template-based response
            response_text = self._generate_template_response(
                intent=intent,
                data=retrieved_data,
            )
        
        return self._create_response(
            content=response_text,
            confidence=0.9 if llm_response else 0.7,
            metadata={
                "intent_handled": intent,
                "data_used": list(retrieved_data.keys()) if retrieved_data else [],
            },
            next_action="quality_check",
        )
    
    async def _generate_with_llm(
        self,
        intent: str,
        priority: str,
        data: dict,
        original_message: str,
    ) -> Optional[str]:
        """Generate response using LLM."""
        prompt = f"""Customer's message: "{original_message}"

Intent: {intent}
Priority: {priority}

Retrieved data:
{json.dumps(data, indent=2, default=str) if data else "No data available"}

Generate a helpful, friendly response for the customer. Remember:
- Address their specific concern
- Use the data provided (don't make things up)
- If data is missing, ask them to provide what you need
- Offer clear next steps"""

        return await self._call_llm(prompt)
    
    def _generate_template_response(
        self,
        intent: str,
        data: dict,
    ) -> str:
        """Generate a template-based response as fallback."""
        
        # Order status response
        if intent == "order_status":
            order_data = data.get("get_order_details")
            if order_data:
                status = order_data.get("status", "processing")
                desc = order_data.get("status_description", "Your order is being processed.")
                tracking_url = order_data.get("tracking_url")
                
                response = f"Thanks for reaching out! Here's the status of your order:\n\n"
                response += f"**Status:** {status.replace('_', ' ').title()}\n"
                response += f"{desc}\n"
                
                if tracking_url:
                    response += f"\nYou can track your package here: {tracking_url}\n"
                
                response += "\nIs there anything else I can help you with?"
                return response
            else:
                return ("I'd be happy to help you check on your order! "
                       "Could you please provide your order number (starts with ORD-) "
                       "and the email address you used for the order?")
        
        # Refund request response
        elif intent == "refund_request":
            policy = data.get("get_refund_policy")
            order_data = data.get("get_order_details")
            
            if policy:
                if policy.get("is_eligible"):
                    response = "I understand you'd like a refund. Good news! "
                    response += f"Your order is eligible for a refund.\n\n"
                    response += f"**Reason:** {policy.get('eligibility_reason')}\n"
                    if policy.get("days_remaining"):
                        response += f"**Time remaining:** {policy.get('days_remaining')} days\n"
                    if policy.get("refund_amount"):
                        response += f"**Refund amount:** ${policy.get('refund_amount'):.2f}\n"
                    response += "\nWould you like me to process this refund for you?"
                else:
                    response = "I understand you're looking for a refund. "
                    response += f"Unfortunately, {policy.get('eligibility_reason', 'this order is not currently eligible for a refund.')}\n\n"
                    response += "If you believe this is an error or have special circumstances, please let me know and I can escalate this to our support team."
                return response
            else:
                return ("I'd be happy to help with your refund request! "
                       "Could you please provide your order number so I can check the refund eligibility?")
        
        # Billing issue response
        elif intent == "billing_issue":
            profile = data.get("get_customer_profile")
            order_data = data.get("get_order_details")
            
            response = "I'm sorry to hear you're experiencing a billing issue. "
            response += "I want to help resolve this for you.\n\n"
            
            if order_data:
                response += f"I can see your order for {order_data.get('total_amount')}. "
            
            response += "Could you please describe the billing issue in more detail? For example:\n"
            response += "- Were you charged the wrong amount?\n"
            response += "- Did you see a duplicate charge?\n"
            response += "- Is there a charge you don't recognize?\n"
            
            return response
        
        # Account access response
        elif intent == "account_access":
            profile = data.get("get_customer_profile")
            
            if profile:
                status = profile.get("account_status", "active")
                if status == "suspended":
                    return ("I can see your account is currently suspended. "
                           "For security reasons, I'll need to escalate this to our security team. "
                           "They will contact you within 24 hours to help resolve this.")
                else:
                    return (f"I can see your account is active and in good standing. "
                           f"You've been a member since {profile.get('member_since', 'our records')}.\n\n"
                           "If you're having trouble logging in, try these steps:\n"
                           "1. Click 'Forgot Password' on the login page\n"
                           "2. Check your spam folder for the reset email\n"
                           "3. Make sure you're using the correct email address\n\n"
                           "Would you like me to send a password reset link?")
            else:
                return ("I'd be happy to help you access your account! "
                       "Could you please confirm the email address associated with your account?")
        
        # Human escalation response
        elif intent == "human_escalation":
            return ("I understand you'd like to speak with a human agent. "
                   "I'm creating a support ticket for you now, and one of our team members "
                   "will reach out within 24 hours.\n\n"
                   "Is there anything specific you'd like me to note for them?")
        
        # Shipping issue response
        elif intent == "shipping_issue":
            order_data = data.get("get_order_details")
            
            if order_data:
                status = order_data.get("status")
                response = f"I'm sorry to hear about the shipping issue with your order.\n\n"
                response += f"**Current status:** {status.replace('_', ' ').title()}\n"
                
                if order_data.get("tracking_url"):
                    response += f"\nTracking link: {order_data.get('tracking_url')}\n"
                
                response += "\nCould you tell me more about what happened? For example:\n"
                response += "- Package shows delivered but you didn't receive it?\n"
                response += "- Package arrived damaged?\n"
                response += "- Wrong item was delivered?\n"
                
                return response
            else:
                return ("I'm sorry to hear about your shipping issue! "
                       "To help you, I'll need your order number. "
                       "Could you please provide it?")
        
        # Default response
        else:
            return ("Thank you for contacting us! I'm here to help.\n\n"
                   "Could you please provide more details about what you need assistance with? "
                   "I can help with:\n"
                   "- Order status and tracking\n"
                   "- Returns and refunds\n"
                   "- Billing questions\n"
                   "- Account access\n"
                   "- Shipping issues")
