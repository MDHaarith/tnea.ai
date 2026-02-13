def validate_mark(mark: float) -> bool:
    """Validates if the mark is within 0-200 range."""
    try:
        m = float(mark)
        return 0 <= m <= 200
    except (ValueError, TypeError):
        return False

def validate_cutoff(cutoff: float) -> bool:
    """Validates if cutoff is within 0-200 range."""
    return validate_mark(cutoff)

def validate_year(year: int) -> bool:
    """Validates year (e.g. 2020-2030)."""
    try:
        y = int(year)
        return 2020 <= y <= 2030
    except (ValueError, TypeError):
        return False
