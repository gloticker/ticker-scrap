import yfinance as yf
import pandas as pd
import pytz
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.stock_models import INDICES, STOCKS, CRYPTO, FOREX, ALL_SYMBOLS
from ..utils.formatters import format_number, format_market_cap


class StockService:
    def __init__(self):
        self.timezone = pytz.timezone('America/New_York')

    async def get_current_market_data(self) -> Dict[str, Dict[str, Any]]:
        try:
            tickers = yf.Tickers(" ".join(ALL_SYMBOLS))
            result = {
                "indices": {},
                "stocks": {},
                "crypto": {},
                "forex": {}
            }

            # Process indices
            for symbol in INDICES:
                info = tickers.tickers[symbol].info
                result["indices"][symbol] = {
                    "current_value": format_number(info.get('regularMarketPrice')),
                    "change": format_number(info.get('regularMarketChange')),
                    "change_percent": format_number(info.get('regularMarketChangePercent'))
                }

            # Process stocks
            for symbol in STOCKS:
                info = tickers.tickers[symbol].info
                market_state = info.get('marketState', 'CLOSED')

                otc_price = None
                if market_state != 'REGULAR':
                    if market_state == 'PRE':
                        otc_price = info.get('preMarketPrice')
                    else:
                        otc_price = info.get('postMarketPrice')

                result["stocks"][symbol] = {
                    "current_price": format_number(info.get('regularMarketPrice')),
                    "market_cap": format_market_cap(info.get("marketCap")),
                    "change": format_number(info.get('regularMarketChange')),
                    "change_percent": format_number(info.get('regularMarketChangePercent')),
                    "market_state": market_state,
                    "otc_price": format_number(otc_price) if otc_price else None
                }

            # Process crypto
            for symbol in CRYPTO:
                info = tickers.tickers[symbol].info
                result["crypto"][symbol] = {
                    "current_price": format_number(info.get('regularMarketPrice')),
                    "market_cap": format_market_cap(info.get("marketCap")),
                    "change": format_number(info.get('regularMarketChange')),
                    "change_percent": format_number(info.get('regularMarketChangePercent'))
                }

            # Process forex
            for symbol in FOREX:
                info = tickers.tickers[symbol].info
                result["forex"][symbol] = {
                    "rate": format_number(info.get('regularMarketPrice')),
                    "change": format_number(info.get('regularMarketChange')),
                    "change_percent": format_number(info.get('regularMarketChangePercent'))
                }

            return result
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
