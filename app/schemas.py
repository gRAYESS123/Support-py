from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Email Config Schemas
class EmailConfigBase(BaseModel):
    email: EmailStr
    password: str
    imap_server: str
    imap_port: Optional[int] = 993

class EmailConfigCreate(EmailConfigBase):
    pass

class EmailConfigResponse(EmailConfigBase):
    id: int
    last_sync: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Ticket Schemas
class TicketBase(BaseModel):
    date: datetime
    main_category: str
    sub_category: Optional[str] = None
    urgency_level: Optional[str] = 'Medium'
    content: Optional[str] = None
    email_id: Optional[str] = None
    subject: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

class TicketCreate(TicketBase):
    pass

class TicketResponse(TicketBase):
    id: int
    sentiment_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Metrics Schema
class MetricsResponse(BaseModel):
    categoryDistribution: dict
    timeDistribution: dict
    urgencyDistribution: dict
    averageSentiment: float

# File Upload Response
class FileUploadResponse(BaseModel):
    message: str
    processed_count: int