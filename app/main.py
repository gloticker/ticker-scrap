from fastapi import FastAPI
import asyncio
import logging
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Gauge
from .workers.market_publisher import publish_market_data, publish_forex_data
from .workers.chart_worker import store_chart_data
from .core.redis_manager import RedisManager
from .workers.market_indicators_worker import publish_market_indicators
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ticker scraper",
    description="worker for scraping ticker data",
    version="1.0.0"
)

# Redis 상태 게이지 정의
redis_health = Gauge(
    "redis_connection_status",
    "Redis connection health (1=up, 0=down)"
)


def redis_health_metric():
    redis_manager = RedisManager()
    redis_health.set(1 if redis_manager.check_connection() else 0)


# 프로메테우스 설정
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/ping", "/health"]
)

# 기본 메트릭 추가
instrumentator.add(metrics.default())
instrumentator.add(lambda: redis_health_metric())

instrumentator.instrument(app).expose(app)


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
