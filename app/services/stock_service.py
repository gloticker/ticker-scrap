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
from curl_cffi import requests

from ..models.stock_models import (
    INDICES, STOCKS, CRYPTO, FOREX, ALL_SYMBOLS,
    AssetType, IndexSymbol, StockSymbol, CryptoSymbol, ForexSymbol
)
from app.utils.formatters import format_number, format_market_cap
from app.core.redis_manager import RedisManager
from app.constants.app_constants import StreamChannel, TimeConstants
from app.constants.header_constants import USER_AGENTS, HEADERS_TEMPLATES

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self):
        self.timezone = pytz.timezone('America/New_York')
        self.redis_client = RedisManager().client
        self.channels = {
            AssetType.INDEX.value.lower(): StreamChannel.INDEX.value,
            AssetType.STOCK.value.lower(): StreamChannel.STOCK.value,
            AssetType.CRYPTO.value.lower(): StreamChannel.CRYPTO.value,
            AssetType.FOREX.value.lower(): StreamChannel.FOREX.value
        }
        self.error_count = 0
        self.error_threshold = TimeConstants.ERROR_THRESHOLD

    async def handle_rate_limit(self):
        self.error_count += 1
        if self.error_count >= self.error_threshold:
            logger.warning(
                "Multiple errors detected, possibly rate limited. Adding delay...")
            await asyncio.sleep(TimeConstants.RATE_LIMIT_DELAY)
            self.error_count = 0
        else:
            await asyncio.sleep(TimeConstants.DEFAULT_RETRY_DELAY)

    def get_random_headers(self):
        headers = random.choice(HEADERS_TEMPLATES).copy()
        headers['User-Agent'] = random.choice(USER_AGENTS)
        return headers

    async def fetch_single_ticker(self, symbol: str, session: requests.Session) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol, session=session)
            info = ticker.info

            if info is None:  # info가 None인 경우 처리
                raise Exception(f"Failed to get info for {symbol}")

            self.error_count = 0
            await asyncio.sleep(random.uniform(
                TimeConstants.RANDOM_DELAY_MIN,
                TimeConstants.RANDOM_DELAY_MAX
            ))
            return symbol, info
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {str(e)}")
            await self.handle_rate_limit()
            raise

    async def process_and_publish_group(self, symbols: list, group_type: str) -> None:
        try:
            logger.info(f"Starting {group_type} data collection...")
            session = requests.Session(impersonate="chrome")
            session.headers.update(self.get_random_headers())

            start_time = time.time()
            result = {}

            for symbol in symbols:
                try:
                    symbol, info = await self.fetch_single_ticker(symbol, session)
                    data = {}

                    if group_type == AssetType.INDEX.value:
                        data = {
                            "current_value": format_number(info.get('regularMarketPrice')),
                            "change": format_number(info.get('regularMarketChange')),
                            "change_percent": format_number(info.get('regularMarketChangePercent'))
                        }
                    elif group_type == AssetType.STOCK.value:
                        market_state = info.get('marketState', 'CLOSED')
                        otc_price = None
                        otc_change = None
                        otc_change_percent = None

                        if market_state != 'REGULAR':
                            if market_state == 'PRE':
                                otc_price = info.get('preMarketPrice')
                                otc_change = info.get('preMarketChange')
                                otc_change_percent = info.get(
                                    'preMarketChangePercent')
                            else:
                                otc_price = info.get('postMarketPrice')
                                otc_change = info.get('postMarketChange')
                                otc_change_percent = info.get(
                                    'postMarketChangePercent')

                        data = {
                            "current_price": format_number(info.get('regularMarketPrice')),
                            "market_cap": format_market_cap(info.get("marketCap")),
                            "change": format_number(info.get('regularMarketChange')),
                            "change_percent": format_number(info.get('regularMarketChangePercent')),
                            "market_state": market_state,
                            "otc_price": format_number(otc_price) if otc_price else None,
                            "otc_change": format_number(otc_change) if otc_change else None,
                            "otc_change_percent": format_number(otc_change_percent) if otc_change_percent else None
                        }
                    elif group_type == AssetType.CRYPTO.value:
                        data = {
                            "current_price": format_number(info.get('regularMarketPrice')),
                            "market_cap": format_market_cap(info.get("marketCap")),
                            "change": format_number(info.get('regularMarketChange')),
                            "change_percent": format_number(info.get('regularMarketChangePercent'))
                        }

                    if data:
                        result[symbol] = data
                except Exception as e:
                    logger.error(f"Failed to process {symbol}: {str(e)}")
                    continue  # 한 심볼이 실패해도 계속 진행

            if result:
                # 스트림 발행
                self.redis_client.publish(
                    self.channels[group_type.lower()],
                    json.dumps(result)
                )
                # 스냅샷 저장
                self.redis_client.set(
                    f"snapshot.{group_type.lower()}",
                    json.dumps(result)
                )

            elapsed_time = time.time() - start_time
            logger.info(
                f"{group_type} data published. Took {elapsed_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error publishing {group_type} data: {str(e)}")
            raise

    async def process_forex(self) -> None:
        try:
            session = requests.Session(impersonate="chrome")
            session.headers.update(self.get_random_headers())
            result = {}

            for symbol in FOREX:
                ticker = yf.Ticker(symbol, session=session)
                info = ticker.info
                result[symbol] = {
                    "rate": format_number(info.get('regularMarketPrice')),
                    "change": format_number(info.get('regularMarketChange')),
                    "change_percent": format_number(info.get('regularMarketChangePercent'))
                }

            if result:
                # 스트림 발행
                self.redis_client.publish(
                    self.channels['forex'],
                    json.dumps(result)
                )
                # 스냅샷 저장
                self.redis_client.set(
                    "snapshot.forex",
                    json.dumps(result)
                )

        except Exception as e:
            logger.error(f"Error publishing FOREX data: {str(e)}")
            raise

    async def get_current_market_data(self) -> Dict[str, Dict[str, Any]]:
        try:
            await self.process_and_publish_group(INDICES, AssetType.INDEX.value)
            await self.process_and_publish_group(STOCKS, AssetType.STOCK.value)
            await self.process_and_publish_group(CRYPTO, AssetType.CRYPTO.value)
            await self.process_forex()

            logger.info("All market data published successfully")
            return {"status": "success", "message": "Data published to respective channels"}
        except Exception as e:
            raise Exception(f"Failed to fetch market data: {str(e)}")

    async def get_chart_data(self) -> Dict[str, Any]:
        """Get last 30 trading days of daily chart data for all symbols"""
        try:
            session = requests.Session(impersonate="chrome")
            session.headers.update(self.get_random_headers())

            end_date = datetime.now(self.timezone)
            start_date = end_date - timedelta(days=45)

            main_data = yf.download(
                tickers=" ".join(ALL_SYMBOLS),
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval="1d",
                prepost=True,
                group_by='ticker',
                session=session
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
