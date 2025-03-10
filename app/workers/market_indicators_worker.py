import asyncio
import logging
from ..services.market_indicators_service import MarketIndicatorsService
from ..constants.app_constants import TimeConstants

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def publish_market_indicators():
    service = MarketIndicatorsService()

    while True:
        try:
            await service.publish_fear_greed_index()
            await service.publish_btc_dominance()
            await asyncio.sleep(TimeConstants.DEFAULT_UPDATE_INTERVAL)
        except Exception as e:
            logger.error(f"Market indicators publishing error: {str(e)}")
            await asyncio.sleep(TimeConstants.DEFAULT_RETRY_DELAY)


async def main():
    logger.info("Market indicators worker starting...")
    await publish_market_indicators()

if __name__ == "__main__":
    asyncio.run(main())
