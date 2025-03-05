import asyncio
import logging
import pytz
from datetime import datetime, timedelta
from ..services.stock_service import StockService
from ..models.stock_models import INDICES, STOCKS, CRYPTO, FOREX
from ..core.redis_manager import RedisManager
from ..models.data_models import StoredChartData, ChartMetadata
from ..constants.app_constants import TimeConstants

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def is_market_closed() -> bool:
    """미국 장이 완전히 종료되었는지 확인 (Post-market 포함)"""
    et_tz = pytz.timezone('America/New_York')
    now_et = datetime.now(et_tz)

    market_close_time = now_et.replace(
        hour=TimeConstants.MARKET_CLOSE_HOUR, minute=0, second=0, microsecond=0)

    return now_et >= market_close_time


async def get_next_run_time() -> datetime:
    """다음 실행 시간 계산 (ET 20:00)"""
    et_tz = pytz.timezone('America/New_York')
    now_et = datetime.now(et_tz)
    target_time = now_et.replace(
        hour=TimeConstants.MARKET_CLOSE_HOUR, minute=0, second=0, microsecond=0)

    if now_et >= target_time:
        target_time += timedelta(days=1)

    return target_time


async def store_symbol_data(redis_client, symbol: str, type: str, chart_data: dict, stored_time: str):
    """단일 심볼 데이터 저장"""
    if symbol in chart_data['data']:
        stored_data = StoredChartData(
            type=type,
            symbol=symbol,
            stored_at=stored_time,
            chart_data=chart_data['data'][symbol],
            metadata=ChartMetadata(
                interval=chart_data['interval'],
                period=chart_data['period'],
                timezone=chart_data['timezone'],
                market_hours=chart_data['market_hours']
            )
        )
        redis_client.set(f"{type}.{symbol}", stored_data.model_dump_json())


async def collect_and_store_data():
    """차트 데이터 수집 및 저장"""
    service = StockService()
    redis_client = RedisManager().client

    logger.info("Starting chart data collection...")
    chart_data = await service.get_chart_data()

    stored_time = datetime.now(pytz.timezone(
        'America/New_York')).strftime('%Y-%m-%d %H:%M:%S %Z')

    # 각 자산 유형별로 데이터 저장
    for symbol in INDICES:
        await store_symbol_data(redis_client, symbol, "index", chart_data, stored_time)

    for symbol in STOCKS:
        await store_symbol_data(redis_client, symbol, "stock", chart_data, stored_time)

    for symbol in CRYPTO:
        await store_symbol_data(redis_client, symbol, "crypto", chart_data, stored_time)

    for symbol in FOREX:
        await store_symbol_data(redis_client, symbol, "forex", chart_data, stored_time)

    logger.info("Chart data stored successfully")


async def store_chart_data():
    """메인 워커 함수"""
    while True:
        try:
            await collect_and_store_data()
            next_run = await get_next_run_time()
            now = datetime.now(pytz.timezone('America/New_York'))
            wait_seconds = (next_run - now).total_seconds()

            logger.info(
                f"Waiting {wait_seconds/3600:.2f} hours until next chart data collection at {next_run}")
            await asyncio.sleep(wait_seconds)

            if not await is_market_closed():
                logger.warning(
                    "Market not fully closed yet, waiting for next cycle")
                continue

        except Exception as e:
            logger.error(f"Error storing chart data: {str(e)}")
            await asyncio.sleep(TimeConstants.ERROR_WAIT_TIME)


async def main():
    logger.info("Chart data worker starting...")
    await store_chart_data()

if __name__ == "__main__":
    asyncio.run(main())
