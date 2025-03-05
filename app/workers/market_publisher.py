import asyncio
import logging
import time
from ..services.stock_service import StockService
from typing import Dict, Any
from ..constants.app_constants import TimeConstants
from ..models.stock_models import INDICES, STOCKS, CRYPTO

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def publish_market_data():
    service = StockService()

    while True:
        try:
            start_time = time.time()
            logger.info(
                "Starting ALL MARKET (INDEX/STOCK/CRYPTO/FOREX) data collection...")

            await service.get_current_market_data()

            elapsed_time = time.time() - start_time
            logger.info(
                f"ALL MARKET data published. Took {elapsed_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Market data publishing error: {str(e)}")
            await asyncio.sleep(TimeConstants.DEFAULT_RETRY_DELAY)


async def publish_forex_data():
    service = StockService()

    while True:
        try:
            start_time = time.time()
            logger.info("Starting forex data collection...")

            await service.process_forex()

            elapsed_time = time.time() - start_time
            logger.info(
                f"Forex data published. Took {elapsed_time:.2f} seconds")
            await asyncio.sleep(TimeConstants.DEFAULT_UPDATE_INTERVAL)
        except Exception as e:
            logger.error(f"Forex data publishing error: {str(e)}")
            await asyncio.sleep(TimeConstants.DEFAULT_RETRY_DELAY)


async def main():
    logger.info("Market publisher starting...")
    try:
        # 두 작업을 병렬로 실행
        await asyncio.gather(
            publish_market_data(),
            publish_forex_data()
        )
    except Exception as e:
        logger.critical(f"Critical error in market publisher: {str(e)}")
        raise


async def process_and_publish_group(self, symbols: list, group_type: str) -> None:
    try:
        # 대문자로 표시
        logger.info(f"Starting {group_type.upper()} data collection...")
        start_time = time.time()

        # 데이터 처리 로직

        elapsed_time = time.time() - start_time
        logger.info(
            f"{group_type.upper()} data published. Took {elapsed_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Error publishing {group_type.upper()} data: {str(e)}")
        raise


async def get_current_market_data(self) -> Dict[str, Dict[str, Any]]:
    try:
        # 각 그룹별로 순차적으로 처리
        await self.process_and_publish_group(INDICES, 'INDEX')
        await self.process_and_publish_group(STOCKS, 'STOCK')
        await self.process_and_publish_group(CRYPTO, 'CRYPTO')
        await self.process_forex()

        logger.info("All market data published successfully")
        return {"status": "success", "message": "Data published to respective channels"}
    except Exception as e:
        raise Exception(f"Failed to fetch market data: {str(e)}")


async def process_forex(self):
    try:
        logger.info("Starting FOREX data collection...")
        start_time = time.time()

        # Forex 처리 로직

        elapsed_time = time.time() - start_time
        logger.info(f"FOREX data published. Took {elapsed_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Error publishing FOREX data: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
