from fastapi import FastAPI
import asyncio
from .workers.market_publisher import publish_market_data, publish_forex_data
from .workers.chart_worker import store_chart_data
from .core.redis_manager import RedisManager

app = FastAPI(
    title="ticker scraper",
    description="worker for scraping ticker data",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    # Redis 연결 확인
    redis_manager = RedisManager()
    if not redis_manager.check_connection():
        raise Exception("Cannot connect to Redis server")

    # 백그라운드 태스크 시작
    asyncio.create_task(publish_market_data())
    asyncio.create_task(publish_forex_data())
    asyncio.create_task(store_chart_data())


@app.get("/ping")
async def health_check():
    return "pong"
