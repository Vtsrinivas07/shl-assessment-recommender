"""Utility functions for the SHL Assessment Recommender."""

import json
from typing import Any


def sanitize_json_string(text: str) -> str:
    """
    Sanitize a string to be JSON-safe.
    
    Args:
        text: Input string
        
    Returns:
        JSON-safe string
    """
    # Replace problematic characters
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\t', ' ')
    
    # Remove multiple spaces
    while '  ' in text:
        text = text.replace('  ', ' ')
    
    return text.strip()


def validate_shl_url(url: str) -> bool:
    """
    Validate that a URL belongs to shl.com domain.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 'shl.com' in url.lower()


def format_duration(minutes: int) -> str:
    """
    Format duration in minutes to human-readable string.
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        Formatted duration string
    """
    if minutes < 60:
        return f"{minutes} minutes"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours > 1 else ''} {remaining_minutes} minutes"


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Input text
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
