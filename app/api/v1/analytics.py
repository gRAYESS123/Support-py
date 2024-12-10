from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ...database import get_db
from ...models.email import Email, Response, EmailStatus, UrgencyLevel
from ...schemas.email import EmailAnalytics, DateRange

router = APIRouter()

@router.get("/summary", response_model=Dict)
async def get_analytics_summary(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db)
):
    """Get summary analytics for the specified date range."""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Get basic metrics
    total_emails = db.query(func.count(Email.id)).filter(
        Email.received_at.between(start_date, end_date)
    ).scalar()

    avg_response_time = db.query(
        func.avg(Response.created_at - Email.received_at)
    ).join(Email).filter(
        Email.received_at.between(start_date, end_date)
    ).scalar()

    # Get category distribution
    category_dist = db.query(
        Email.main_category,
        func.count(Email.id).label('count')
    ).filter(
        Email.received_at.between(start_date, end_date)
    ).group_by(Email.main_category).all()

    # Get sentiment distribution
    sentiment_dist = db.query(
        case(
            (Email.sentiment_score > 0.3, 'positive'),
            (Email.sentiment_score < -0.3, 'negative'),
            else_='neutral'
        ).label('sentiment'),
        func.count(Email.id).label('count')
    ).filter(
        Email.received_at.between(start_date, end_date)
    ).group_by('sentiment').all()

    return {
        "total_emails": total_emails,
        "avg_response_time_hours": avg_response_time.total_seconds() / 3600 if avg_response_time else None,
        "category_distribution": {cat: count for cat, count in category_dist},
        "sentiment_distribution": {sent: count for sent, count in sentiment_dist}
    }

@router.get("/trends")
async def get_trends(
    metric: str = Query(..., enum=["volume", "response_time", "sentiment"]),
    interval: str = Query(..., enum=["day", "week", "month"]),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get trend data for specified metric and time interval."""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    if interval == "day":
        date_trunc = func.date_trunc('day', Email.received_at)
    elif interval == "week":
        date_trunc = func.date_trunc('week', Email.received_at)
    else:
        date_trunc = func.date_trunc('month', Email.received_at)

    if metric == "volume":
        data = db.query(
            date_trunc.label('date'),
            func.count(Email.id).label('value')
        ).filter(
            Email.received_at.between(start_date, end_date)
        ).group_by('date').order_by('date').all()

    elif metric == "response_time":
        data = db.query(
            date_trunc.label('date'),
            func.avg(Response.created_at - Email.received_at).label('value')
        ).join(Response).filter(
            Email.received_at.between(start_date, end_date)
        ).group_by('date').order_by('date').all()

    else:  # sentiment
        data = db.query(
            date_trunc.label('date'),
            func.avg(Email.sentiment_score).label('value')
        ).filter(
            Email.received_at.between(start_date, end_date)
        ).group_by('date').order_by('date').all()

    return {
        "metric": metric,
        "interval": interval,
        "data": [{"date": d.date, "value": float(d.value) if d.value else 0} for d in data]
    }

@router.get("/category-analysis")
async def get_category_analysis(
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get detailed analysis for specific category or all categories."""
    query = db.query(Email)
    if category:
        query = query.filter(Email.main_category == category)
    if start_date:
        query = query.filter(Email.received_at >= start_date)
    if end_date:
        query = query.filter(Email.received_at <= end_date)

    emails = query.all()

    return {
        "total_count": len(emails),
        "avg_sentiment": sum(e.sentiment_score for e in emails) / len(emails) if emails else 0,
        "urgent_count": sum(1 for e in emails if e.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]),
        "sub_categories": db.query(
            Email.sub_category,
            func.count(Email.id).label('count')
        ).filter(Email.main_category == category).group_by(Email.sub_category).all() if category else None
    }

@router.get("/response-effectiveness")
async def get_response_effectiveness(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Analyze effectiveness of responses based on customer feedback and follow-ups."""
    responses = db.query(Response).join(Email).filter(
        Email.received_at.between(start_date, end_date) if start_date and end_date else True
    ).all()

    return {
        "total_responses": len(responses),
        "helpful_rate": sum(1 for r in responses if r.was_helpful) / len(responses) if responses else 0,
        "reply_rate": sum(1 for r in responses if r.customer_replied) / len(responses) if responses else 0,
        "avg_response_length": sum(len(r.content) for r in responses) / len(responses) if responses else 0
    }