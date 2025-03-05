from typing import List

INDICES = [
    "^IXIC",  # NASDAQ Composite
    "^GSPC",  # S&P 500
    "^KS11",  # KOSPI
    "^VIX",   # VIX
]

STOCKS = [
    "AAPL",  # Apple
    "NVDA",  # NVIDIA
    "MSFT",  # Microsoft
    "AMZN",  # Amazon
    "GOOGL",  # Alphabet
    "META",  # Meta
    "TSLA",  # Tesla
]

FOREX = [
    "KRW=X",    # USD/KRW
    "EURKRW=X",  # EUR/KRW
    "CNYKRW=X",  # CNY/KRW
    "JPYKRW=X"  # JPY/KRW
]

ALL_SYMBOLS = INDICES + STOCKS + FOREX
