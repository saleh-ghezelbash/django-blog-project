from django import template
import re

register = template.Library()

@register.filter
def highlight(text, query):
    """Highlight search terms in text"""
    if not query or not text:
        return text
    
    # Escape regex special characters
    query = re.escape(query)
    # Case-insensitive replacement with mark tag
    return re.sub(
        f'({query})', 
        r'<mark class="highlight">\1</mark>', 
        str(text), 
        flags=re.IGNORECASE
    )

@register.filter
def snippet(text, query, words=30):
    """Create a text snippet with highlighted search terms"""
    if not query or not text:
        return text[:200] + '...' if len(text) > 200 else text
    
    # Find position of first match
    text_lower = text.lower()
    query_lower = query.lower()
    
    try:
        pos = text_lower.index(query_lower)
        start = max(0, pos - 50)
        end = min(len(text), pos + 50)
        
        snippet = text[start:end]
        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet = snippet + '...'
        
        return highlight(snippet, query)
    except ValueError:
        return text[:200] + '...' if len(text) > 200 else text