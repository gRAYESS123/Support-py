from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ...database import get_db
from ...models.email import Email, Response, EmailStatus
from ...schemas.email import EmailCreate, EmailResponse, ResponseOut
from ...services.email_processor import EmailProcessor
from ...services.email_sender import EmailSender

router = APIRouter()

@router.post("/process", response_model=EmailResponse)
async def process_new_email(
    email_data: EmailCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process a new incoming email."""
    processor = EmailProcessor(db)
    result = await processor.process_email(email_data.dict())
    
    if not result:
        raise HTTPException(status_code=400, detail="Could not process email")
    
    # Queue response sending in background
    if result.get('response'):
        background_tasks.add_task(
            EmailSender().send_response,
            result['email'],
            result['response']
        )
    
    return result['email']

@router.get("/pending", response_model=List[EmailResponse])
async def get_pending_emails(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all pending emails."""
    emails = db.query(Email).filter(
        Email.status == EmailStatus.NEW
    ).offset(skip).limit(limit).all()
    return emails

@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: int,
    db: Session = Depends(get_db)
):
    """Get specific email by ID."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@router.get("/{email_id}/responses", response_model=List[ResponseOut])
async def get_email_responses(
    email_id: int,
    db: Session = Depends(get_db)
):
    """Get all responses for an email."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email.responses

@router.post("/{email_id}/retry")
async def retry_email_processing(
    email_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry processing a failed email."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    processor = EmailProcessor(db)
    result = await processor.process_email({
        'subject': email.subject,
        'body': email.body,
        'sender_email': email.sender_email,
        'sender_name': email.sender_name
    })
    
    if not result:
        raise HTTPException(status_code=400, detail="Retry processing failed")
    
    return {"status": "success", "message": "Email reprocessing queued"}

@router.post("/{email_id}/manual-response")
async def add_manual_response(
    email_id: int,
    response_content: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Add a manual response to an email."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    response = Response(
        email_id=email_id,
        content=response_content,
        is_manual=True
    )
    
    db.add(response)
    db.commit()
    db.refresh(response)
    
    # Queue response sending
    background_tasks.add_task(
        EmailSender().send_response,
        email,
        response
    )
    
    return {"status": "success", "response_id": response.id}

@router.get("/search", response_model=List[EmailResponse])
async def search_emails(
    query: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search emails based on various criteria."""
    filters = []
    if query:
        filters.append(
            (Email.subject.ilike(f"%{query}%")) |
            (Email.body.ilike(f"%{query}%")) |
            (Email.sender_email.ilike(f"%{query}%"))
        )
    
    if start_date:
        filters.append(Email.received_at >= start_date)
    if end_date:
        filters.append(Email.received_at <= end_date)
    if category:
        filters.append(Email.main_category == category)
    
    emails = db.query(Email).filter(
        *filters
    ).offset(skip).limit(limit).all()
    
    return emails