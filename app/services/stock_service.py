import yfinance as yf
import pandas as pd
import pytz
import asyncio
import random
import redis
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import time

from ..models.stock_models import INDICES, STOCKS, CRYPTO, FOREX, ALL_SYMBOLS
from ..utils.formatters import format_number, format_market_cap
from ..core.redis_manager import RedisManager

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self):
        self.timezone = pytz.timezone('America/New_York')
        self.redis_client = RedisManager().client
        self.channels = {
            'index': 'index.price.stream',
            'stock': 'stock.price.stream',
            'crypto': 'crypto.price.stream',
            'forex': 'forex.price.stream'
        }
        self.error_count = 0
        self.error_threshold = 5  # 5번 연속 에러시 대기 시간 추가

    async def handle_rate_limit(self):
        self.error_count += 1
        if self.error_count >= self.error_threshold:
            logger.warning(
                "Multiple errors detected, possibly rate limited. Adding delay...")
            await asyncio.sleep(30)  # 30초 대기
            self.error_count = 0
        else:
            await asyncio.sleep(5)  # 기본 5초 대기

    async def fetch_single_ticker(self, symbol: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            self.error_count = 0  # 성공시 에러 카운트 리셋
            await asyncio.sleep(random.uniform(1.0, 1.2))
            return symbol, info
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {str(e)}")
            await self.handle_rate_limit()
            raise

    async def process_and_publish_group(self, symbols: list, group_type: str) -> None:
        try:
            logger.info(f"Starting {group_type.upper()} data collection...")
            start_time = time.time()

            result = {}
            for symbol in symbols:
                symbol, info = await self.fetch_single_ticker(symbol)
                data = {}  # 여기로 이동 - 기본 빈 딕셔너리로 초기화

                if group_type == 'INDEX':  # 대문자로 통일
                    data = {
                        "current_value": format_number(info.get('regularMarketPrice')),
                        "change": format_number(info.get('regularMarketChange')),
                        "change_percent": format_number(info.get('regularMarketChangePercent'))
                    }
                elif group_type == 'STOCK':  # 대문자로 통일
                    market_state = info.get('marketState', 'CLOSED')
                    otc_price = None
                    if market_state != 'REGULAR':
                        if market_state == 'PRE':
                            otc_price = info.get('preMarketPrice')
                        else:
                            otc_price = info.get('postMarketPrice')

                    data = {
                        "current_price": format_number(info.get('regularMarketPrice')),
                        "market_cap": format_market_cap(info.get("marketCap")),
                        "change": format_number(info.get('regularMarketChange')),
                        "change_percent": format_number(info.get('regularMarketChangePercent')),
                        "market_state": market_state,
                        "otc_price": format_number(otc_price) if otc_price else None
                    }
                elif group_type == 'CRYPTO':  # 대문자로 통일
                    data = {
                        "current_price": format_number(info.get('regularMarketPrice')),
                        "market_cap": format_market_cap(info.get("marketCap")),
                        "change": format_number(info.get('regularMarketChange')),
                        "change_percent": format_number(info.get('regularMarketChangePercent'))
                    }

                if data:  # 데이터가 있는 경우만 추가
                    result[symbol] = data

            # 채널에 발행
            if result:
                self.redis_client.publish(
                    self.channels[group_type.lower()],  # 채널명은 소문자 유지
                    json.dumps(result)
                )

            elapsed_time = time.time() - start_time
            logger.info(
                f"{group_type.upper()} data published. Took {elapsed_time:.2f} seconds")

        except Exception as e:
            logger.error(
                f"Error publishing {group_type.upper()} data: {str(e)}")
            raise

    async def process_forex(self) -> None:
        """Forex는 tickers로 한 번에 처리"""
        tickers = yf.Tickers(" ".join(FOREX))
        result = {}

        for symbol in FOREX:
            info = tickers.tickers[symbol].info
            result[symbol] = {
                "rate": format_number(info.get('regularMarketPrice')),
                "change": format_number(info.get('regularMarketChange')),
                "change_percent": format_number(info.get('regularMarketChangePercent'))
            }

        if result:
            self.redis_client.publish(
                self.channels['forex'],
                json.dumps(result)
            )

    async def get_current_market_data(self) -> Dict[str, Dict[str, Any]]:
        try:
            # 각 그룹별로 순차적으로 처리
            await self.process_and_publish_group(INDICES, 'INDEX')
            await self.process_and_publish_group(STOCKS, 'STOCK')
            await self.process_and_publish_group(CRYPTO, 'CRYPTO')
            await self.process_forex()

            logger.info("All market data published successfully")
            return {"status": "success", "message": "Data published to respective channels"}
        except Exception as e:
            raise Exception(f"Failed to fetch market data: {str(e)}")

    async def get_chart_data(self) -> Dict[str, Any]:
        """Get last 30 trading days of daily chart data for all symbols"""
        try:
            # 현재 시간 기준으로 45일 전 날짜 계산 (주말/공휴일 고려하여 여유있게)
            end_date = datetime.now(self.timezone)
            start_date = end_date - timedelta(days=45)

            main_data = yf.download(
                tickers=" ".join(ALL_SYMBOLS),
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval="1d",
                prepost=True,
                group_by='ticker'
            )

            result = {}

            for symbol in ALL_SYMBOLS:
                symbol_data = {}
                data_view = main_data[symbol] if len(
                    ALL_SYMBOLS) > 1 else main_data

                # 최근 30 거래일만 사용
                valid_dates = [d for d in data_view.index if not pd.isna(
                    data_view["Close"].loc[d])][-30:]

                for timestamp in valid_dates:
                    close_value = data_view["Close"].loc[timestamp]
                    utc_time = pytz.utc.localize(
                        timestamp) if timestamp.tzinfo is None else timestamp
                    et_time = utc_time.astimezone(self.timezone)
                    et_timestamp = et_time.strftime("%Y-%m-%d")

                    symbol_data[et_timestamp] = {
                        "close": format_number(close_value)
                    }

                if symbol_data:
                    result[symbol] = symbol_data

            trading_date = None
            if main_data.index.size > 0:
                first_timestamp = main_data.index[-1]
                et_time = (pytz.utc.localize(
                    first_timestamp) if first_timestamp.tzinfo is None else first_timestamp).astimezone(self.timezone)
                trading_date = et_time.strftime('%Y-%m-%d')

            return {
                "interval": "1d",
                "period": "30d",
                "data": result,
                "trading_date": trading_date,
                "timezone": "America/New_York (ET)",
                "market_hours": "9:30 AM - 4:00 PM ET (Regular Market Hours)"
            }
        except Exception as e:
            raise Exception(f"Failed to fetch chart data: {str(e)}")
