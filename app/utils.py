from textblob import TextBlob
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any

def calculate_sentiment(text: str) -> float:
    """Calculate sentiment score for given text"""
    if not text:
        return 0.0
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def categorize_content(subject: str, body: str) -> tuple:
    """Categorize content based on subject and body"""
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    categories = {
        'Technical Issue': ['error', 'bug', 'broken', 'not working', 'failed'],
        'Account': ['password', 'login', 'account', 'sign in', 'access'],
        'Billing': ['payment', 'invoice', 'charge', 'subscription', 'price'],
        'Feature Request': ['feature', 'suggestion', 'improve', 'would be nice', 'can you add'],
        'General Inquiry': ['how to', 'question', 'help with', 'support']
    }
    
    for category, keywords in categories.items():
        if any(keyword in subject_lower or keyword in body_lower for keyword in keywords):
            return category, 'Support'
    
    return 'Other', 'General'

def determine_urgency(subject: str, body: str) -> str:
    """Determine content urgency level"""
    text = (subject + ' ' + body).lower()
    
    urgent_keywords = ['urgent', 'emergency', 'critical', 'asap', 'immediately']
    low_keywords = ['feedback', 'suggestion', 'feature request', 'when possible']
    
    if any(keyword in text for keyword in urgent_keywords):
        return 'High'
    elif any(keyword in text for keyword in low_keywords):
        return 'Low'
    return 'Medium'

def process_csv_data(df: pd.DataFrame) -> list:
    """Process CSV data and return list of tickets"""
    processed_data = []
    
    for _, row in df.iterrows():
        subject = row.get('subject', '')
        body = row.get('body', '') or row.get('content', '')
        
        main_cat, sub_cat = categorize_content(subject, body)
        
        processed_data.append({
            'date': pd.to_datetime(row.get('date')),
            'main_category': main_cat,
            'sub_category': sub_cat,
            'urgency_level': determine_urgency(subject, body),
            'content': body,
            'sentiment_score': calculate_sentiment(body),
            'email_id': row.get('email_id'),
            'subject': subject,
            'from_address': row.get('from_address'),
            'to_address': row.get('to_address')
        })
    
    return processed_data

def calculate_metrics(tickets: list) -> Dict[str, Any]:
    """Calculate metrics from tickets"""
    metrics = {
        'categoryDistribution': {},
        'timeDistribution': {},
        'urgencyDistribution': {},
        'averageSentiment': 0
    }
    
    if not tickets:
        return metrics
    
    total_sentiment = 0
    
    for ticket in tickets:
        # Category distribution
        category = ticket.main_category
        metrics['categoryDistribution'][category] = \
            metrics['categoryDistribution'].get(category, 0) + 1
        
        # Time distribution
        date_key = ticket.date.strftime('%Y-%m-%d')
        metrics['timeDistribution'][date_key] = \
            metrics['timeDistribution'].get(date_key, 0) + 1
        
        # Urgency distribution
        urgency = ticket.urgency_level
        metrics['urgencyDistribution'][urgency] = \
            metrics['urgencyDistribution'].get(urgency, 0) + 1
        
        # Sentiment
        total_sentiment += ticket.sentiment_score
    
    metrics['averageSentiment'] = total_sentiment / len(tickets)
    
    return metrics