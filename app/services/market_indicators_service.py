import aiohttp
import json
import logging
import time
from typing import Dict, Any
from ..utils.formatters import format_number, format_market_cap
from ..core.redis_manager import RedisManager
from ..constants.app_constants import ApiEndpoint, StreamChannel
from ..models.stock_models import IndexSymbol, CryptoSymbol, IndicatorType

logger = logging.getLogger(__name__)


class MarketIndicatorsService:
    def __init__(self):
        self.redis_client = RedisManager().client
        self.fear_greed_url = ApiEndpoint.FEAR_GREED.value
        self.btc_dominance_url = ApiEndpoint.BTC_DOMINANCE.value
        self.total3_url = ApiEndpoint.TOTAL3.value
        self.total3_proportion = None

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
                async with session.get(self.fear_greed_url, headers=headers, ssl=False) as response:
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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.btc_dominance_url, headers=headers, ssl=False) as response:
                    data = await response.json()
                    dominance_data = data.get('data', {}).get('dominance', [])
                    btc_dominance = dominance_data[0].get('mcProportion', 0)
                    self.total3_proportion = dominance_data[2].get(
                        'mcProportion', 0)  # save total3 proportion
                    return {
                        CryptoSymbol.BTC_DOMINANCE.value: {
                            "value": format_number(btc_dominance)
                        }
                    }
        except Exception as e:
            logger.error(f"Error fetching BTC Dominance: {str(e)}")
            raise

    async def fetch_total3(self) -> Dict[str, Any]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9'
            }

            payload = {
                "symbols": {
                    "tickers": ["CRYPTOCAP:TOTAL3"],
                    "query": {"types": []}
                },
                "columns": ["close", "change_abs", "change"]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.total3_url, headers=headers, json=payload, ssl=False) as response:
                    data = await response.json()
                    if data.get('data'):
                        market_data = data['data'][0]['d']
                        change_percent = market_data[2]
                        change_value = format_market_cap(abs(market_data[1]))

                        if change_percent < 0:
                            change_value = f"-{change_value}"

                        return {
                            "TOTAL3": {
                                "value": format_number(self.total3_proportion or 0),
                                "market_cap": format_market_cap(market_data[0]),
                                "change": change_value,
                                "change_percent": format_number(change_percent)
                            }
                        }
                    return {}
        except Exception as e:
            logger.error(f"Error fetching Total3: {str(e)}")
            raise

    async def publish_fear_greed_index(self):
        try:
            start_time = time.time()
            logger.info("Starting Fear & Greed Index collection...")

            data = await self.fetch_fear_greed_index()
            self.redis_client.publish(
                StreamChannel.INDEX.value,
                json.dumps(data)
            )
            self.redis_client.set(
                f"snapshot.{IndicatorType.FEAR_GREED.value}",
                json.dumps(data)
            )

            elapsed_time = time.time() - start_time
            logger.info(
                f"Fear & Greed Index published. Took {elapsed_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error publishing Fear & Greed Index: {str(e)}")
            raise

    async def publish_btc_dominance(self):
        try:
            start_time = time.time()
            logger.info("Starting BTC Dominance collection...")

            data = await self.fetch_btc_dominance()
            self.redis_client.publish(
                StreamChannel.CRYPTO.value,
                json.dumps(data)
            )
            self.redis_client.set(
                f"snapshot.{IndicatorType.BTC_DOMINANCE.value}",
                json.dumps(data)
            )

            elapsed_time = time.time() - start_time
            logger.info(
                f"BTC Dominance published. Took {elapsed_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error publishing BTC Dominance: {str(e)}")
            raise

    async def publish_total3(self):
        try:
            start_time = time.time()
            logger.info("Starting Total3 collection...")

            data = await self.fetch_total3()
            self.redis_client.publish(
                StreamChannel.CRYPTO.value,
                json.dumps(data)
            )
            self.redis_client.set(
                f"snapshot.{IndicatorType.TOTAL3.value}",
                json.dumps(data)
            )

            elapsed_time = time.time() - start_time
            logger.info(f"Total3 published. Took {elapsed_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error publishing Total3: {str(e)}")
            raise
