from anthropic import Anthropic
from typing import Dict, Optional
import json
from ..config import settings
from ..models.email import UrgencyLevel

class EmailClassifier:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-opus-20240229"

    async def classify_email(self, email_data: Dict) -> Dict:
        """
        Classify email content using Anthropic's Claude.
        Returns classification including category, sentiment, and urgency.
        """
        try:
            prompt = f"""
            Analyze this customer support email for SLYFONE (virtual phone number service):

            Subject: {email_data.get('subject', '')}
            Content: {email_data.get('body', '')}

            Classify this email based on the following criteria and return a JSON object:

            1. Main Categories (select one):
                - Account_Issues
                - Payment_Billing
                - Technical_Issues
                - Number_Management
                - Service_Questions
                - WhatsApp_Related
                - Other

            2. Sub-Categories for each main category:
                Account_Issues:
                    - Login_Problems
                    - Password_Reset
                    - Email_Change
                    - Account_Recovery
                    - Account_Deletion
                Payment_Billing:
                    - Refund_Request
                    - Payment_Failed
                    - Subscription_Issues
                    - Billing_Questions
                    - Credit_Purchase
                Technical_Issues:
                    - App_Not_Working
                    - Call_Problems
                    - SMS_Issues
                    - Activation_Error
                    - Connection_Problems
                Number_Management:
                    - Number_Change
                    - Multiple_Numbers
                    - Number_Retrieval
                    - Port_Number
                    - Number_Cancellation
                Service_Questions:
                    - Features_Inquiry
                    - Pricing_Questions
                    - Coverage_Area
                    - Service_Comparison
                    - Usage_Instructions
                WhatsApp_Related:
                    - Verification_Issues
                    - OTP_Problems
                    - WhatsApp_Ban
                    - Registration_Error
                    - WhatsApp_Setup

            3. Additional Classification:
                - Sentiment score (-1 to 1)
                - Urgency (LOW, MEDIUM, HIGH, CRITICAL)
                - Keywords (list of relevant terms)
                - Customer tone (frustrated, neutral, satisfied)
                - Response priority (1-5)

            Return the analysis as a JSON object with these exact fields:
            {
                "main_category": string,
                "sub_category": string,
                "sentiment_score": float,
                "urgency": string,
                "keywords": list[string],
                "customer_tone": string,
                "priority": int,
                "confidence": float,
                "requires_escalation": boolean
            }
            """

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            classification = json.loads(response.content[0].text)
            
            # Validate urgency level
            if classification["urgency"] not in [e.value for e in UrgencyLevel]:
                classification["urgency"] = UrgencyLevel.MEDIUM.value

            # Ensure confidence is between 0 and 1
            classification["confidence"] = max(0.0, min(1.0, classification["confidence"]))
            
            # Ensure sentiment score is between -1 and 1
            classification["sentiment_score"] = max(-1.0, min(1.0, classification["sentiment_score"]))

            return classification

        except Exception as e:
            print(f"Classification error: {str(e)}")
            return {
                "main_category": "Other",
                "sub_category": "Unknown",
                "sentiment_score": 0.0,
                "urgency": UrgencyLevel.MEDIUM.value,
                "keywords": [],
                "customer_tone": "neutral",
                "priority": 3,
                "confidence": 0.0,
                "requires_escalation": False
            }

    def _extract_keywords(self, text: str) -> list:
        """Extract relevant keywords from text."""
        # You could implement custom keyword extraction here
        # For now, we'll rely on Claude's extraction
        return []

    def _calculate_urgency(self, text: str, sentiment: float) -> str:
        """Calculate urgency based on content and sentiment."""
        # You could implement custom urgency calculation here
        # For now, we'll rely on Claude's calculation
        return UrgencyLevel.MEDIUM.value