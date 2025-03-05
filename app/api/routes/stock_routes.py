from fastapi import APIRouter, HTTPException
from typing import Optional

from ...services.stock_service import StockService
from ...models.response_models import MarketResponse, ChartResponse

router = APIRouter()
stock_service = StockService()


@router.get("/current", response_model=MarketResponse)
async def get_current_market_data():
    try:
        return await stock_service.get_current_market_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chart", response_model=ChartResponse)
async def get_chart_data():
    try:
        return await stock_service.get_chart_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
