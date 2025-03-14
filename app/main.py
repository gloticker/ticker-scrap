from fastapi import FastAPI
import asyncio
from starlette_exporter import PrometheusMiddleware, handle_metrics
from .workers.market_publisher import publish_market_data, publish_forex_data
from .workers.chart_worker import store_chart_data
from .core.redis_manager import RedisManager
from .workers.market_indicators_worker import publish_market_indicators
from datetime import datetime

app = FastAPI(
    title="ticker scraper",
    description="worker for scraping ticker data",
    version="1.0.0"
)

app.add_middleware(
    PrometheusMiddleware,
    app_name="ticker_scraper",
    prefix="ticker",
    skip_paths=["/ping", "/health", "/metrics"]
)

app.add_route("/metrics", handle_metrics)


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
    asyncio.create_task(publish_market_indicators())


@app.get("/ping")
async def jenkins_health_check():
    return {"status": "pong"}


@app.get("/health")
async def prometheus_health_check():
    redis_manager = RedisManager()
    redis_status = "up" if redis_manager.check_connection() else "down"

    return {
        "status": "ok",
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }
