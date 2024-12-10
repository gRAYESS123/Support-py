from anthropic import Anthropic
from typing import Dict, Optional
import json
from ..config import settings
from ..models.email import Email, Customer

class ResponseGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-opus-20240229"

    async def generate_response(self, 
                              email: Email, 
                              classification: Dict,
                              customer: Optional[Customer] = None) -> Dict:
        """
        Generate a response using Anthropic's Claude based on email content and classification.
        """
        try:
            # Build context for the AI
            context = self._build_context(email, classification, customer)
            
            # Create the prompt
            prompt = f"""
            You are Dee, a customer support specialist for SLYFONE. Generate a response to this customer email:

            Context:
            - Category: {classification['main_category']}/{classification['sub_category']}
            - Customer Tone: {classification['customer_tone']}
            - Urgency: {classification['urgency']}
            - Sentiment: {classification['sentiment_score']}

            Customer Information:
            {context['customer_info']}

            Original Email:
            Subject: {email.subject}
            Content: {email.body}

            Guidelines:
            1. Address the customer by name if available
            2. Always maintain a professional and empathetic tone
            3. Provide clear, actionable solutions
            4. Include relevant links or documentation when needed
            5. End with a clear next step or call to action
            6. Don't mention sentiment scores or internal classifications
            7. Keep responses concise but complete

            Generate a response following company policies:
            - No refunds after 24 hours of purchase
            - One number per device policy
            - Direct iOS/Android refunds to respective stores
            - Escalate technical issues to specialists
            
            Return response as JSON:
            {
                "response_text": "The actual response",
                "suggested_actions": ["list", "of", "follow-up", "actions"],
                "internal_notes": "Notes for support team",
                "requires_follow_up": boolean,
                "escalation_needed": boolean,
                "template_used": "template name if any"
            }
            """

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_data = json.loads(response.content[0].text)
            
            # Add signature if not present
            if "Best regards" not in response_data["response_text"]:
                response_data["response_text"] += "\n\nBest regards,\nDee\nSLYFONE Support Team"

            return response_data

        except Exception as e:
            print(f"Response generation error: {str(e)}")
            return {
                "response_text": "I apologize, but I'm having trouble generating a response. I'll escalate this to our support team who will get back to you shortly.\n\nBest regards,\nDee\nSLYFONE Support Team",
                "suggested_actions": ["Escalate to supervisor"],
                "internal_notes": f"Error generating response: {str(e)}",
                "requires_follow_up": True,
                "escalation_needed": True,
                "template_used": "error_fallback"
            }

    def _build_context(self, 
                      email: Email, 
                      classification: Dict,
                      customer: Optional[Customer]) -> Dict:
        """Build context for response generation."""
        context = {
            "customer_info": "New Customer"
        }

        if customer:
            context["customer_info"] = f"""
                Customer Status: {'Active' if customer.is_active else 'Inactive'}
                Subscription: {customer.subscription_status or 'None'}
                Total Tickets: {customer.total_tickets}
                Last Contact: {customer.last_contact.strftime('%Y-%m-%d') if customer.last_contact else 'Never'}
            """

        return context

    def _get_response_template(self, 
                             main_category: str, 
                             sub_category: str) -> Optional[str]:
        """Get response template based on email category."""
        templates = {
            "Account_Issues": {
                "Password_Reset": """
                Hello {name},

                I understand you're having trouble with your password. Here's how to reset it:
                1. Visit slyfone.com/reset
                2. Enter your email address
                3. Follow the instructions sent to your email

                Let me know if you need any further assistance.

                Best regards,
                Dee
                """,
                # Add more templates
            }
        }
        
        return templates.get(main_category, {}).get(sub_category)