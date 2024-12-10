from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Enum as SQLAlchemyEnum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base

class UrgencyLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EmailStatus(str, enum.Enum):
    NEW = "new"
    PROCESSED = "processed"
    RESPONDED = "responded"
    FAILED = "failed"

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True)
    thread_id = Column(String, index=True)
    
    # Sender information
    sender_email = Column(String, index=True)
    sender_name = Column(String)
    recipient_email = Column(String)
    subject = Column(String)
    body = Column(Text)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Classification
    main_category = Column(String)
    sub_category = Column(String)
    classification_confidence = Column(Float)
    keywords = Column(JSON)
    sentiment_score = Column(Float)
    urgency = Column(SQLAlchemyEnum(UrgencyLevel))
    
    # Status
    status = Column(SQLAlchemyEnum(EmailStatus), default=EmailStatus.NEW)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    customer_id = Column(Integer, nullable=True)
    is_reply = Column(Boolean, default=False)
    additional_data = Column(JSON, nullable=True)
    
    # Relationships
    responses = relationship("Response", back_populates="email")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Response metadata
    model_version = Column(String)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    response_time_ms = Column(Integer)
    
    # Status tracking
    is_sent = Column(Boolean, default=False)
    send_attempts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Response analytics
    was_helpful = Column(Boolean, nullable=True)
    customer_replied = Column(Boolean, default=False)
    
    # Relationships
    email = relationship("Email", back_populates="responses")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    account_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Account status
    is_active = Column(Boolean, default=True)
    subscription_status = Column(String)
    subscription_end_date = Column(DateTime, nullable=True)
    
    # Metadata
    last_contact = Column(DateTime, nullable=True)
    total_tickets = Column(Integer, default=0)
    preferences = Column(JSON, nullable=True)