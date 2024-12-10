import asyncio
import aioimaplib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import email
from email.header import decode_header
import traceback

from ..config import settings
from ..database import SessionLocal
from ..services.email_processor import EmailProcessor
from ..models.email import Email, EmailStatus, EmailAnalytics

class EmailPoller:
    def __init__(self):
        self.imap_server = settings.SMTP_SERVER
        self.imap_port = 993  # Standard IMAPS port
        self.email_user = settings.SMTP_USER
        self.email_password = settings.SMTP_PASSWORD
        self.fetch_interval = settings.EMAIL_FETCH_INTERVAL  # in seconds
        self.max_emails = settings.MAX_EMAILS_PER_FETCH
        self._running = False
        self._last_error = None
        self._processed_count = 0

    async def start_polling(self):
        """Start the email polling loop."""
        self._running = True
        print(f"Starting email polling service...")
        print(f"Server: {self.imap_server}")
        print(f"User: {self.email_user}")
        print(f"Fetch interval: {self.fetch_interval} seconds")
        print(f"Max emails per fetch: {self.max_emails}")

        while self._running:
            try:
                await self.poll_emails()
                self._last_error = None
            except Exception as e:
                self._last_error = str(e)
                print(f"Error polling emails: {str(e)}")
                print(traceback.format_exc())
                # Wait a bit longer after an error
                await asyncio.sleep(30)
            
            await asyncio.sleep(self.fetch_interval)

    async def stop_polling(self):
        """Stop the polling loop."""
        self._running = False

    async def poll_emails(self):
        """Poll for new emails and process them."""
        try:
            # Connect to IMAP server
            imap_client = aioimaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            await imap_client.wait_hello_from_server()
            
            # Login
            await imap_client.login(self.email_user, self.email_password)
            
            # Select inbox
            await imap_client.select('INBOX')
            
            # Search for unread emails
            _, messages = await imap_client.search('UNSEEN')
            message_numbers = messages[0].split()
            
            if not message_numbers:
                print("No new emails found.")
                return

            print(f"Found {len(message_numbers)} new emails. Processing up to {self.max_emails}...")
            
            # Process emails
            for msg_num in message_numbers[:self.max_emails]:
                try:
                    success = await self._process_single_email(msg_num, imap_client)
                    if success:
                        self._processed_count += 1
                        # Mark as read if processed successfully
                        await imap_client.store(msg_num, '+FLAGS', '(\Seen)')
                        print(f"Successfully processed email {msg_num.decode()}")
                    else:
                        print(f"Failed to process email {msg_num.decode()}")

                except Exception as e:
                    print(f"Error processing email {msg_num.decode()}: {str(e)}")
                    print(traceback.format_exc())
                    continue

            await imap_client.close()
            await imap_client.logout()

        except Exception as e:
            print(f"IMAP connection error: {str(e)}")
            print(traceback.format_exc())
            raise

    async def _process_single_email(self, msg_num: bytes, imap_client) -> bool:
        """Process a single email message."""
        try:
            # Fetch the email
            _, msg_data = await imap_client.fetch(msg_num, '(RFC822)')
            if not msg_data:
                return False

            email_body = msg_data[0][1]
            
            # Parse email message
            email_message = email.message_from_bytes(email_body)
            
            # Skip if it's a reply to avoid processing loops
            if email_message.get('In-Reply-To'):
                print(f"Skipping reply email: {msg_num.decode()}")
                return True
            
            # Extract basic headers
            subject = self._decode_header(email_message.get('Subject', ''))
            from_addr = self._decode_header(email_message.get('From', ''))
            print(f"Processing email - From: {from_addr}, Subject: {subject}")

            # Process with database session
            db = SessionLocal()
            try:
                processor = EmailProcessor(db)
                result = await processor.process_email(email_body)
                
                if result:
                    db.commit()
                    return True
                else:
                    db.rollback()
                    return False
                    
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error processing single email: {str(e)}")
            print(traceback.format_exc())
            return False

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ""
        
        try:
            decoded = decode_header(header)[0]
            if isinstance(decoded[0], bytes):
                return decoded[0].decode(decoded[1] or 'utf-8', errors='ignore')
            return str(decoded[0])
        except Exception as e:
            print(f"Error decoding header: {str(e)}")
            return header

    @property
    def status(self) -> dict:
        """Get current status of the poller."""
        return {
            "running": self._running,
            "last_error": self._last_error,
            "processed_count": self._processed_count,
            "last_check": datetime.utcnow().isoformat(),
            "configuration": {
                "server": self.imap_server,
                "user": self.email_user,
                "fetch_interval": self.fetch_interval,
                "max_emails": self.max_emails
            }
        }