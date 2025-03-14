import redis
import logging
from typing import Optional
from redis.exceptions import ConnectionError
import os
from redis import Redis

logger = logging.getLogger(__name__)


class RedisManager:
    _instance: Optional['RedisManager'] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()

    def connect(self):
        try:
            self._client = Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD'),
                db=0,
                decode_responses=True,
                socket_timeout=5,
                retry_on_timeout=True
            )
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            raise

    @property
    def client(self) -> redis.Redis:
        if not self.check_connection():
            logger.warning("Redis connection lost, attempting to reconnect...")
            self.connect()
        return self._client

    def check_connection(self) -> bool:
        try:
            return self._client and self._client.ping()
        except (ConnectionError, Exception) as e:
            logger.error(f"Redis connection check failed: {str(e)}")
            return False
