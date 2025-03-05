from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime


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


class ChartData(BaseModel):
    close: str


class ChartMetadata(BaseModel):
    interval: str
    period: str
    timezone: str
    market_hours: str


class StoredChartData(BaseModel):
    type: str
    symbol: str
    stored_at: str
    chart_data: Dict[str, Dict[str, str]]
    metadata: ChartMetadata
