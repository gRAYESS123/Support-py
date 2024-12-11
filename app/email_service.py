import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import asyncio
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import EmailConfig, Ticket
from .utils import calculate_sentiment, categorize_content, determine_urgency

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailProcessor:
    def __init__(self, config: EmailConfig):
        self.config = config
        self.imap_conn = None
    
    async def connect(self):
        """Establish IMAP connection"""
        try:
            self.imap_conn = imaplib.IMAP4_SSL(self.config.imap_server, self.config.imap_port)
            self.imap_conn.login(self.config.email, self.config.password)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {str(e)}")
            return False
    
    def disconnect(self):
        """Close IMAP connection"""
        if self.imap_conn:
            try:
                self.imap_conn.logout()
            except:
                pass
            self.imap_conn = None

    def process_email_body(self, email_message) -> str:
        """Extract and clean email body"""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
                elif part.get_content_type() == "text/html":
                    html = part.get_payload(decode=True).decode()
                    soup = BeautifulSoup(html, 'html.parser')
                    body = soup.get_text()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()
        
        # Clean the body text
        body = re.sub(r'\s+', ' ', body).strip()
        return body

    def decode_email_header(self, header_value: str) -> str:
        """Decode email header"""
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8'))
                except:
                    decoded_parts.append(part.decode('utf-8', 'ignore'))
            else:
                decoded_parts.append(part)
        return ' '.join(decoded_parts)

    async def fetch_emails(self, db: Session, days_back: int = 30) -> List[Ticket]:
        """Fetch and process emails"""
        if not await self.connect():
            return []

        try:
            # Select inbox
            self.imap_conn.select("INBOX")
            
            # Search for emails within date range
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            _, message_numbers = self.imap_conn.search(None, f'(SINCE {since_date})')
            
            tickets = []
            
            for num in message_numbers[0].split():
                try:
                    _, msg_data = self.imap_conn.fetch(num, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Process email
                    subject = self.decode_email_header(email_message['subject'])
                    from_addr = self.decode_email_header(email_message['from'])
                    to_addr = self.decode_email_header(email_message['to'])
                    date_str = email_message['date']
                    message_id = email_message['message-id']
                    
                    # Skip if already processed
                    existing_ticket = db.query(Ticket).filter(Ticket.email_id == message_id).first()
                    if existing_ticket:
                        continue
                    
                    # Get email body
                    body = self.process_email_body(email_message)
                    
                    # Categorize and analyze
                    main_cat, sub_cat = categorize_content(subject, body)
                    urgency = determine_urgency(subject, body)
                    sentiment = calculate_sentiment(body)
                    
                    # Create ticket
                    ticket = Ticket(
                        date=datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z'),
                        main_category=main_cat,
                        sub_category=sub_cat,
                        urgency_level=urgency,
                        sentiment_score=sentiment,
                        content=body,
                        email_id=message_id,
                        subject=subject,
                        from_address=from_addr,
                        to_address=to_addr
                    )
                    
                    db.add(ticket)
                    tickets.append(ticket)
                
                except Exception as e:
                    logger.error(f"Error processing email: {str(e)}")
                    continue
            
            db.commit()
            return tickets
        
        finally:
            self.disconnect()

class EmailSyncManager:
    def __init__(self, db: Session):
        self.db = db
    
    async def sync_all_configs(self):
        """Sync emails for all active configurations"""
        configs = self.db.query(EmailConfig).filter(EmailConfig.is_active == True).all()
        for config in configs:
            try:
                processor = EmailProcessor(config)
                await processor.fetch_emails(self.db)
                
                config.last_sync = datetime.utcnow()
                self.db.commit()
                
            except Exception as e:
                logger.error(f"Error syncing emails for {config.email}: {str(e)}")
    
    async def run_periodic_sync(self, interval_minutes: int = 60):
        """Run periodic email synchronization"""
        while True:
            try:
                await self.sync_all_configs()
            except Exception as e:
                logger.error(f"Error in periodic sync: {str(e)}")
            
            await asyncio.sleep(interval_minutes * 60)  # Convert minutes to seconds