import re
from typing import Dict

def anonymize_text(text: str) -> Dict[str, str]:
    """
    Anonymize sensitive information in text.
    Returns dict with original and anonymized text.
    """
    anonymized = text
    
    # Anonymize emails
    anonymized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        anonymized
    )
    
    # Anonymize phone numbers
    anonymized = re.sub(
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        '[PHONE]',
        anonymized
    )
    
    # Anonymize URLs
    anonymized = re.sub(
        r'https?://[^\s]+',
        '[URL]',
        anonymized
    )
    
    # Anonymize credit card patterns (last 4 digits)
    anonymized = re.sub(
        r'\b(?:ending in|last|xxxx)\s*\d{4}\b',
        '[CARD]',
        anonymized,
        flags=re.IGNORECASE
    )
    
    # Anonymize transaction/invoice IDs
    anonymized = re.sub(
        r'\b(?:TXN|INV|ID)[-:]?\w+\b',
        '[TRANSACTION_ID]',
        anonymized,
        flags=re.IGNORECASE
    )
    
    # Anonymize API keys
    anonymized = re.sub(
        r'\bsk-[a-zA-Z0-9]+\b',
        '[API_KEY]',
        anonymized
    )
    
    return {
        'original': text,
        'anonymized': anonymized,
        'has_sensitive_data': anonymized != text
    }

def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def preprocess_ticket(ticket_text: str) -> Dict[str, str]:
    """
    Full preprocessing pipeline for a ticket.
    """
    cleaned = clean_text(ticket_text)
    anonymized_data = anonymize_text(cleaned)
    
    return {
        'original': ticket_text,
        'cleaned': cleaned,
        'anonymized': anonymized_data['anonymized'],
        'has_sensitive_data': anonymized_data['has_sensitive_data']
    }