import yfinance as yf
import pandas as pd
import pytz
from typing import Dict, Any, Optional

from ..models.stock_models import INDICES, STOCKS, FOREX, ALL_SYMBOLS
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
                result["stocks"][symbol] = {
                    "current_price": format_number(info.get('currentPrice')),
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

    async def get_chart_data(self, period: str = "1d", interval: str = "5m") -> Dict[str, Any]:
        try:
            data = yf.download(
                tickers=" ".join(ALL_SYMBOLS),
                period=period,
                interval=interval,
                prepost=True,
                group_by='ticker'
            )

            result = {}
            for symbol in ALL_SYMBOLS:
                symbol_data = {}
                data_view = data[symbol] if len(ALL_SYMBOLS) > 1 else data

                for timestamp in data.index:
                    if not pd.isna(data_view["Close"].loc[timestamp]):
                        utc_time = pytz.utc.localize(
                            timestamp) if timestamp.tzinfo is None else timestamp
                        et_time = utc_time.astimezone(self.timezone)
                        et_timestamp = et_time.strftime(
                            "%Y-%m-%d %H:%M:%S-05:00")

                        symbol_data[et_timestamp] = {
                            "close": format_number(data_view["Close"].loc[timestamp])
                        }

                if symbol_data:
                    result[symbol] = symbol_data

            trading_date = None
            if data.index.size > 0:
                first_timestamp = data.index[0]
                et_time = (pytz.utc.localize(
                    first_timestamp) if first_timestamp.tzinfo is None else first_timestamp).astimezone(self.timezone)
                trading_date = et_time.strftime('%Y-%m-%d')

            return {
                "interval": str(interval),
                "period": str(period),
                "data": result,
                "trading_date": trading_date,
                "timezone": "America/New_York (ET)",
                "market_hours": "9:30 AM - 4:00 PM ET (Regular Market Hours)"
            }
        except Exception as e:
            raise Exception(f"Failed to fetch chart data: {str(e)}")
