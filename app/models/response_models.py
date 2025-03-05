from pydantic import BaseModel
from typing import Dict, Optional


class IndexData(BaseModel):
    current_value: str
    change: str
    change_percent: str


class StockData(BaseModel):
    current_price: str
    market_cap: Optional[str]
    change: str
    change_percent: str
    market_state: str
    otc_price: Optional[str]


class CryptoData(BaseModel):
    current_price: str
    market_cap: Optional[str]
    change: str
    change_percent: str


class ForexData(BaseModel):
    rate: str
    change: str
    change_percent: str


class MarketResponse(BaseModel):
    indices: Dict[str, IndexData]
    stocks: Dict[str, StockData]
    crypto: Dict[str, CryptoData]
    forex: Dict[str, ForexData]


class ChartData(BaseModel):
    close: str


class ChartResponse(BaseModel):
    interval: str
    period: str
    data: Dict[str, Dict[str, ChartData]]
    trading_date: Optional[str]
    timezone: str
    market_hours: str
