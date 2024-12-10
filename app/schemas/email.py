from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.email import UrgencyLevel, EmailStatus

class EmailBase(BaseModel):
    subject: str
    body: str
    sender_email: EmailStr
    sender_name: Optional[str] = None
    recipient_email: EmailStr

class EmailCreate(EmailBase):
    message_id: str
    thread_id: Optional[str] = None
    is_reply: bool = False
    additional_data: Optional[Dict[str, Any]] = None

class EmailClassification(BaseModel):
    main_category: str
    sub_category: str
    classification_confidence: float = Field(..., ge=0.0, le=1.0)
    keywords: List[str]
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    urgency: UrgencyLevel

class EmailResponse(EmailBase):
    id: int
    message_id: str
    thread_id: Optional[str]
    received_at: datetime
    processed_at: Optional[datetime]
    status: EmailStatus
    classification: Optional[EmailClassification]
    error_message: Optional[str]

    class Config:
        orm_mode = True

class ResponseBase(BaseModel):
    content: str
    model_version: str
    prompt_tokens: int
    completion_tokens: int

class ResponseCreate(ResponseBase):
    email_id: int

class ResponseUpdate(BaseModel):
    was_helpful: Optional[bool]
    customer_replied: Optional[bool]
    error_message: Optional[str]

class ResponseOut(ResponseBase):
    id: int
    email_id: int
    created_at: datetime
    sent_at: Optional[datetime]
    is_sent: bool
    send_attempts: int
    was_helpful: Optional[bool]
    customer_replied: bool

    class Config:
        orm_mode = True

class CustomerBase(BaseModel):
    email: EmailStr
    name: Optional[str]
    account_id: str

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str]
    subscription_status: Optional[str]
    subscription_end_date: Optional[datetime]
    preferences: Optional[Dict[str, Any]]

class CustomerOut(CustomerBase):
    id: int
    created_at: datetime
    is_active: bool
    subscription_status: Optional[str]
    subscription_end_date: Optional[datetime]
    last_contact: Optional[datetime]
    total_tickets: int

    class Config:
        orm_mode = True

class EmailAnalytics(BaseModel):
    total_emails: int
    average_response_time: float
    category_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    urgency_distribution: Dict[UrgencyLevel, int]
    response_rate: float

class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime = Field(default_factory=datetime.utcnow)

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v