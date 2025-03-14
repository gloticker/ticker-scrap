from enum import Enum
from typing import Final
import os


class StreamChannel(Enum):
    INDEX = 'index.price.stream'
    STOCK = 'stock.price.stream'
    CRYPTO = 'crypto.price.stream'
    FOREX = 'forex.price.stream'


class ApiEndpoint(Enum):
    FEAR_GREED = os.environ['FEAR_GREED']
    BTC_DOMINANCE = os.environ['BTC_DOMINANCE']
    TOTAL3 = os.environ['TOTAL3']

# 기타 상수들


class TimeConstants:
    MARKET_CLOSE_HOUR: Final[int] = 20  # ET 20:00
    DEFAULT_RETRY_DELAY: Final[int] = 5  # 5초
    ERROR_WAIT_TIME: Final[int] = 300    # 5분
    DEFAULT_UPDATE_INTERVAL: Final[int] = 60  # 1분
    RATE_LIMIT_DELAY: Final[int] = 30    # 30초
    RANDOM_DELAY_MIN: Final[float] = 1.0  # 최소 지연 시간
    RANDOM_DELAY_MAX: Final[float] = 1.2  # 최대 지연 시간
    ERROR_THRESHOLD: Final[int] = 5      # 에러 임계값
    CHART_DAYS: Final[int] = 30          # 차트 데이터 기간
    CHART_BUFFER_DAYS: Final[int] = 45   # 차트 데이터 버퍼 기간
