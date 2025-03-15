from enum import Enum
from typing import List


class IndexSymbol(Enum):
    NASDAQ = "^IXIC"    # NASDAQ Composite
    SNP500 = "^GSPC"    # S&P 500
    DOW = "^DJI"        # Dow Jones Industrial Average
    RUSSELL = "^RUT"    # Russell 2000
    TLT = "^TLT"        # 20-Year Treasury Bond
    VIX = "^VIX"        # VIX
    FEAR_GREED = "Fear&Greed"  # Fear & Greed Index


class StockSymbol(Enum):
    APPLE = "AAPL"      # Apple
    NVIDIA = "NVDA"     # NVIDIA
    MICROSOFT = "MSFT"  # Microsoft
    AMAZON = "AMZN"     # Amazon
    ALPHABET = "GOOGL"  # Alphabet
    META = "META"       # Meta
    TESLA = "TSLA"      # Tesla


class CryptoSymbol(Enum):
    BITCOIN = "BTC-USD"  # Bitcoin
    ETHEREUM = "ETH-USD"  # Ethereum
    SOLANA = "SOL-USD"  # Solana
    BTC_DOMINANCE = "BTC.D"  # BTC Dominance
    TOTAL3 = "TOTAL3"  # Total Market Cap (Excluding BTC and ETH)


class ForexSymbol(Enum):
    DXY = "DX-Y.NYB"  # DXY
    USDKRW = "KRW=X"     # USD/KRW
    EURKRW = "EURKRW=X"  # EUR/KRW
    CNYKRW = "CNYKRW=X"  # CNY/KRW
    JPYKRW = "JPYKRW=X"  # JPY/KRW

# 리스트로 변환하는 헬퍼 함수들


def get_symbols(enum_class) -> List[str]:
    if enum_class == IndexSymbol:
        # Fear & Greed 제외
        return [e.value for e in enum_class if e != IndexSymbol.FEAR_GREED]
    elif enum_class == CryptoSymbol:
        # BTC.D와 TOTAL3 제외
        return [e.value for e in enum_class if e not in [CryptoSymbol.BTC_DOMINANCE, CryptoSymbol.TOTAL3]]
    return [e.value for e in enum_class]


# 실제 사용할 리스트들
INDICES = get_symbols(IndexSymbol)
STOCKS = get_symbols(StockSymbol)
CRYPTO = get_symbols(CryptoSymbol)
FOREX = get_symbols(ForexSymbol)
ALL_SYMBOLS = INDICES + STOCKS + CRYPTO + FOREX

# 심볼 타입 매핑


class AssetType(Enum):
    INDEX = 'INDEX'
    STOCK = 'STOCK'
    CRYPTO = 'CRYPTO'
    FOREX = 'FOREX'


class IndicatorType(Enum):
    FEAR_GREED = 'fear-greed'
    BTC_DOMINANCE = 'btc-dominance'
    TOTAL3 = 'total3'
