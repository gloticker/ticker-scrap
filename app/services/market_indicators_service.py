import aiohttp
import json
import logging
from typing import Dict, Any
from ..utils.formatters import format_number
from ..core.redis_manager import RedisManager
from ..constants.app_constants import ApiEndpoint, StreamChannel
from ..models.stock_models import IndexSymbol, CryptoSymbol, IndicatorType

logger = logging.getLogger(__name__)


class MarketIndicatorsService:
    def __init__(self):
        self.redis_client = RedisManager().client
        self.fear_greed_url = ApiEndpoint.FEAR_GREED.value
        self.btc_dominance_url = ApiEndpoint.BTC_DOMINANCE.value

    async def fetch_fear_greed_index(self) -> Dict[str, Any]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://www.cnn.com',
                'Referer': 'https://www.cnn.com/'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.fear_greed_url, headers=headers) as response:
                    data = await response.json()
                    fear_greed_data = data.get('fear_and_greed', {})
                    return {
                        IndexSymbol.FEAR_GREED.value: {
                            "score": format_number(fear_greed_data.get('score', 0)),
                            "rating": fear_greed_data.get('rating', 'Unknown').title()
                        }
                    }
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {str(e)}")
            raise

    async def fetch_btc_dominance(self) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.btc_dominance_url) as response:
                    data = await response.json()
                    btc_dominance = data.get('data', {}).get(
                        'market_cap_percentage', {}).get('btc', 0)
                    return {
                        CryptoSymbol.BTC_DOMINANCE.value: {
                            "value": format_number(btc_dominance)
                        }
                    }
        except Exception as e:
            logger.error(f"Error fetching BTC Dominance: {str(e)}")
            raise

    async def publish_fear_greed_index(self):
        try:
            data = await self.fetch_fear_greed_index()
            # 스트림 발행과 스냅샷 저장에 동일한 데이터 구조 사용
            self.redis_client.publish(
                StreamChannel.INDEX.value,
                json.dumps(data)
            )
            self.redis_client.set(
                f"snapshot.{IndicatorType.FEAR_GREED.value}",
                json.dumps(data)
            )
            logger.info("Fear & Greed Index published successfully")
        except Exception as e:
            logger.error(f"Error publishing Fear & Greed Index: {str(e)}")
            raise

    async def publish_btc_dominance(self):
        try:
            data = await self.fetch_btc_dominance()
            # 스트림 발행과 스냅샷 저장에 동일한 데이터 구조 사용
            self.redis_client.publish(
                StreamChannel.CRYPTO.value,
                json.dumps(data)
            )
            self.redis_client.set(
                f"snapshot.{IndicatorType.BTC_DOMINANCE.value}",
                json.dumps(data)
            )
            logger.info("BTC Dominance published successfully")
        except Exception as e:
            logger.error(f"Error publishing BTC Dominance: {str(e)}")
            raise
