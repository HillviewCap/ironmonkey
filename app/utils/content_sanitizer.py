from __future__ import annotations

import bleach


def sanitize_html_content(html: str) -> str:
    """
    Sanitize HTML content by removing potentially harmful tags and attributes.

    Args:
        html (str): The HTML content to sanitize.

    Returns:
        str: The sanitized HTML content.
    """
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul',
        'p', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre'
    ]
    allowed_attributes = {
        'a': ['href', 'title'],
        'abbr': ['title'],
        'acronym': ['title'],
    }

    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )

    return clean_html
