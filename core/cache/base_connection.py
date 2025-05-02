from core.base_connection import BaseConnection
from redis.asyncio import Redis

from ..loggers import log


class BaseCacheConnection(BaseConnection):
	_connection: Redis = None
	_url: str | None = None
	_name: str = "Reddis"

	@classmethod
	async def _connect(cls, url: str | None = None) -> Redis:
		if cls._connection is None:
			cls._connection = await Redis.from_url(
				url=url,
				#"redis://users-redis:6379/1",
				decode_responses=True
			)
			await cls._connection.ping()

		return cls._connection

	@classmethod
	async def _check_connection(cls) -> bool:
		if cls._connection is None:
			return False

		try:
			await cls._connection.ping()
		except Exception as e:
			log.warning(f"Connection check failed: {e}")
			return False

		return True

	@classmethod
	async def disconnect(cls) -> None:
		await cls._connection.close()
		await cls._connection.connection_pool.disconnect()
