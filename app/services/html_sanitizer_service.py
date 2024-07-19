import html
import re

def sanitize_html(text: str) -> str:
    """
    Remove HTML tags and unescape HTML entities.
    
    Args:
        text (str): The input text containing HTML.
    
    Returns:
        str: The sanitized text with HTML tags removed and entities unescaped.
    """
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
