"""
This module provides a service for sanitizing HTML content.

It includes functionality to remove HTML tags, unescape HTML entities,
and clean up whitespace in text strings.
"""

import html
import re

def sanitize_html(text: str) -> str:
    """
    Remove HTML tags and unescape HTML entities.
    
    This function performs the following operations:
    1. Unescapes HTML entities (e.g., &amp; becomes &)
    2. Removes all HTML tags
    3. Cleans up extra whitespace
    
    Args:
        text (str): The input text containing HTML.
    
    Returns:
        str: The sanitized text with HTML tags removed, entities unescaped,
             and extra whitespace cleaned up.
    
    Example:
        >>> sanitize_html("<p>Hello &amp; welcome</p>")
        'Hello & welcome'
    """
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
