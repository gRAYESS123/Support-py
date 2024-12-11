from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey
from .database import Base
from datetime import datetime

class EmailConfig(Base):
    __tablename__ = 'email_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    imap_server = Column(String, nullable=False)
    imap_port = Column(Integer, default=993)
    last_sync = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    main_category = Column(String, nullable=False)
    sub_category = Column(String)
    urgency_level = Column(String)
    sentiment_score = Column(Float)
    content = Column(String)
    email_id = Column(String, unique=True)  # Original email message ID
    subject = Column(String)
    from_address = Column(String)
    to_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)