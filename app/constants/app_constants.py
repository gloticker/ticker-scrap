from enum import Enum
from typing import Final
import os
from functools import lru_cache


def get_required_env(key: str) -> str:
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


@lru_cache()
def get_api_endpoint(key: str) -> str:
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


class StreamChannel(Enum):
    INDEX = 'index.price.stream'
    STOCK = 'stock.price.stream'
    CRYPTO = 'crypto.price.stream'
    FOREX = 'forex.price.stream'


class ApiEndpoint:
    @property
    def FEAR_GREED(self) -> str:
        return get_api_endpoint('FEAR_GREED')

    @property
    def BTC_DOMINANCE(self) -> str:
        return get_api_endpoint('BTC_DOMINANCE')

    @property
    def TOTAL3(self) -> str:
        return get_api_endpoint('TOTAL3')


api_endpoints = ApiEndpoint()


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
