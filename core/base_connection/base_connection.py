import asyncio
from abc import ABC, abstractmethod

from ..loggers import log


class BaseConnection(ABC):
	_connection: None = None
	_url: str | None = None
	_name: str | None = None

	@classmethod
	async def validate_url(cls, url: str):
		if url is None:
			error = "url cannot be None"
			log.error(error)
			raise ValueError(error)

		return url

	@classmethod
	async def setup_connection(cls, url: str | None = None, max_attempts: int = 10) -> None:
		cls._url = await cls.validate_url(url)
		for attempt in range(1, max_attempts + 1):
			try:
				await cls._connect(url)
				connection = await cls._check_connection()
				if connection:
					log.info(f"Successfully connected to {cls._name}")
					break
			except Exception as e:
				log.warning(
					f"[{attempt}/{max_attempts}] "
					f"Failed to connect to {cls._name}: {e} "
					f"Retrying in 5 seconds...")
				await asyncio.sleep(5)

		if not cls._connection:
			log.error(f"Exceeded max connection attempts to {cls._name}")
			raise ConnectionError(f"Could not connect to {cls._name} after several attempts")

	@classmethod
	@abstractmethod
	async def _connect(cls, url: str | None = None):
		raise NotImplementedError

	@classmethod
	@abstractmethod
	async def _check_connection(cls) -> bool:
		raise NotImplementedError

	@classmethod
	async def get_connection(cls):
		connection_established = await cls._check_connection()
		if not connection_established:
			if cls._url is None:
				error = (f"No url provided for connection to {cls._name} "
						 f"(Probably wasn't connected at app startup)")
				log.error(error)
				raise ValueError(error)

			log.warning(f"No connection to {cls._name}")
			return None

		return cls._connection

	@classmethod
	@abstractmethod
	async def disconnect(cls) -> None:
		raise NotImplementedError
