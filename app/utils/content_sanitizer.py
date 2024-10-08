from __future__ import annotations

import bleach
from html import unescape


from bs4 import BeautifulSoup

def sanitize_html_content(html: str) -> str:
    """
    Sanitize HTML content by removing potentially harmful tags and attributes.

    This function uses both BeautifulSoup and bleach to clean the HTML content.
    It removes script and iframe tags, on* attributes, and then applies bleach
    to allow only specific safe tags and attributes. Finally, it unescapes HTML
    entities to prevent double-escaping.

    Args:
        html (str): The HTML content to sanitize.

    Returns:
        str: The sanitized HTML content with potentially harmful elements removed.

    Example:
        >>> sanitize_html_content('<script>alert("XSS")</script><p onclick="evil()">Safe content</p>')
        '<p>Safe content</p>'
    """
    # First pass: use BeautifulSoup to remove script, iframe, and on* attributes
    soup = BeautifulSoup(html, 'html.parser')
    
    for script in soup(["script", "iframe"]):
        script.decompose()
    
    for tag in soup():
        for attribute in list(tag.attrs):
            if attribute.startswith('on'):
                del tag.attrs[attribute]
    
    # Convert back to string for bleach processing
    html = str(soup)

    # Second pass: use bleach to allow only specific tags and attributes
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul',
        'p', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'img'
    ]
    allowed_attributes = {
        'a': ['href', 'title'],
        'abbr': ['title'],
        'acronym': ['title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
    }

    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )

    # Unescape HTML entities to prevent double-escaping
    return unescape(clean_html)


def strip_html_tags(html: str) -> str:
    """
    Remove all HTML tags from the given content.

    This function uses the bleach library to remove all HTML tags from the input,
    leaving only the text content.

    Args:
        html (str): The HTML content to strip.

    Returns:
        str: The content with all HTML tags removed.

    Example:
        >>> strip_html_tags('<p>This is <b>bold</b> text.</p>')
        'This is bold text.'
    """
    return bleach.clean(html, tags=[], strip=True)
