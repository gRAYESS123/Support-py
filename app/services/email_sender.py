import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime
from ..config import settings
from ..models.email import Email, Response

class EmailSender:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.default_sender = "support@slyfone.com"

    async def send_response(self,
                          email: Email,
                          response: Response,
                          cc_addresses: Optional[List[str]] = None,
                          bcc_addresses: Optional[List[str]] = None) -> bool:
        """Send email response to customer."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Re: {email.subject}"
            msg["From"] = self.default_sender
            msg["To"] = email.sender_email
            
            if cc_addresses:
                msg["Cc"] = ", ".join(cc_addresses)
            
            # Add response content
            html_content = self._format_html_response(response.content)
            msg.attach(MIMEText(html_content, "html"))

            # Add original message as quote
            if email.body:
                quoted_text = self._format_quoted_text(email.body)
                msg.attach(MIMEText(quoted_text, "html"))

            # Configure recipients
            recipients = [email.sender_email]
            if cc_addresses:
                recipients.extend(cc_addresses)
            if bcc_addresses:
                recipients.extend(bcc_addresses)

            # Send email
            async with aiosmtplib.SMTP(hostname=self.smtp_server,
                                     port=self.smtp_port,
                                     use_tls=True) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                await smtp.send_message(msg, recipients)

            # Update response status
            response.is_sent = True
            response.sent_at = datetime.utcnow()
            response.send_attempts += 1
            
            return True

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            response.error_message = str(e)
            response.send_attempts += 1
            return False

    def _format_html_response(self, content: str) -> str:
        """Format response content as HTML."""
        html_template = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="padding: 20px; background-color: #ffffff;">
                {content.replace('\n', '<br>')}
            </div>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                <img src="https://www.slyfone.com/images/logo.png" alt="SLYFONE" style="height: 40px;">
                <p style="color: #666; font-size: 12px;">
                    SLYFONE Support Team<br>
                    Website: <a href="https://www.slyfone.com">www.slyfone.com</a><br>
                    Need Help? Visit our <a href="https://support.slyfone.com">Help Center</a>
                </p>
            </div>
        </div>
        """
        return html_template

    def _format_quoted_text(self, original_text: str) -> str:
        """Format original message as quoted text."""
        quoted_html = f"""
        <div style="margin-top: 20px; padding: 10px; border-left: 2px solid #ccc; color: #666;">
            <p style="font-size: 12px; margin-bottom: 10px;">Original Message:</p>
            {original_text.replace('\n', '<br>')}
        </div>
        """
        return quoted_html