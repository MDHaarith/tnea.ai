import re

def normalize_name(name: str) -> str:
    """Standardizes college/branch/district names."""
    if not name:
        return ""
    # Lowercase and strip whitespace
    name = name.lower().strip()
    # Remove excessive internal whitespace
    name = re.sub(r'\s+', ' ', name)
    return name

def normalize_query(query: str) -> str:
    """Cleans user query for processing."""
    if not query:
        return ""
    return query.lower().strip()
