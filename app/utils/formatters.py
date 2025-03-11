from typing import Optional


def format_number(value, default=0) -> str:
    """Format numbers to always show 2 decimal places as string"""
    try:
        return f"{float(value or default):.2f}"
    except (TypeError, ValueError):
        return f"{float(default):.2f}"


def format_market_cap(value) -> Optional[str]:
    """Convert market cap to T/B format with 2 decimal places"""
    if not value:
        return None

    trillion = 1_000_000_000_000  # 1T
    billion = 1_000_000_000       # 1B

    if value >= trillion:
        return f"{format_number(value/trillion)} T"
    return f"{format_number(value/billion)} B"
