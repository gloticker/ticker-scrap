from fastapi import FastAPI
import asyncio
import logging
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from .workers.market_publisher import publish_market_data, publish_forex_data
from .workers.chart_worker import store_chart_data
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

# 프로메테우스 설정
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics"]
)

# 메트릭 설정 (FastAPI Observability 대시보드용)
instrumentator.add(
    metrics.latency(
        should_include_handler=True,
        should_include_method=True,
        should_include_status=True,
        metric_namespace="http",
        metric_subsystem="",
        buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1,
                 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
    )
).add(
    metrics.requests(
        should_include_handler=True,
        should_include_method=True,
        should_include_status=True,
        metric_namespace="http",
        metric_subsystem=""
    )
)

# 메트릭 활성화
instrumentator.instrument(app).expose(app)


@app.on_event("startup")
async def startup_event():
    # 백그라운드 태스크 시작
    asyncio.create_task(publish_market_data())
    asyncio.create_task(publish_forex_data())
    asyncio.create_task(store_chart_data())
    asyncio.create_task(publish_market_indicators())


@app.get("/ping")
async def jenkins_health_check():
    return {"status": "pong"}


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }
