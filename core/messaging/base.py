from abc import ABC

from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractRobustConnection, AbstractExchange, \
	AbstractQueue
from aio_pika.patterns import RPC

from loggers import default_logger


class BaseMessagingConnection:
	_connection: AbstractRobustConnection | None = None
	_connection_name: str | None = None
	_url: str | None = None
	_channel: AbstractChannel | None = None

	@classmethod
	async def setup_connection(cls, url: str | None = None) -> None:
		if url is None:
			error = "url cannot be None"
			default_logger.error(error)
			raise ValueError(error)

		cls._url = url

		try:
			await cls._connect(url)
		except Exception as e:
			default_logger.error(e)

	@classmethod
	async def _connect(cls, url: str | None = None) -> AbstractRobustConnection:
		if cls._connection is None or cls._connection.is_closed:
			try:
				cls._connection = await connect_robust(
					url,
					client_properties={"connection_name": cls._connection_name},
				)
				default_logger.info(f"Successfully connected to RabbitMQ server: {url}")
			except Exception as e:
				default_logger.error(f"Error connecting to RabbitMQ: {e}")
				raise e

		return cls._connection

	@classmethod
	async def get_connection(cls) -> AbstractRobustConnection:
		if cls._connection is None or cls._connection.is_closed:
			if cls._url is None:
				error = "No url provided (Probably wasn't connected at app startup)"
				default_logger.error(error)
				raise ValueError(error)

			default_logger.info(f"Reconnecting to RabbitMQ server: {cls._url}")
			connection = await cls._connect(cls._url)
			return connection

		return cls._connection

	@classmethod
	async def disconnect(cls) -> None:
		if cls._connection and not cls._connection.is_closed:
			await cls._connection.close()
			cls._connection = None

	@classmethod
	async def _create_channel(cls):
		if cls._channel:
			return cls._channel

		connection = await cls.get_connection()
		cls._channel = await connection.channel()

		return cls._channel

	@classmethod
	async def get_channel(cls) -> AbstractChannel:
		if cls._channel is None:
			return await cls._create_channel()

		return cls._channel


# class BaseMessagingExchange(BaseMessagingConnection, ABC):
# 	_exchange: AbstractExchange | None = None
#
# 	def __init__(
# 			self,
# 			exchange_kwargs: dict | None = None
# 	) -> None:
# 		super().__init__()
# 		self._exchange_name = (exchange_kwargs or {}).get('name') or None
# 		self._exchange_kwargs = exchange_kwargs if self._exchange_name else None
#
# 	async def _set_exchange(self) -> AbstractExchange:
# 		if self._exchange:
# 			return self._exchange
#
# 		channel = await self.get_channel()
# 		if self._exchange_name:
# 			self._exchange = await channel.declare_exchange(
# 				**self._exchange_kwargs
# 			)
# 		else:
# 			self._exchange = channel.default_exchange
#
# 		return self._exchange
#
# 	async def get_exchange(self) -> AbstractExchange:
# 		if self._exchange:
# 			return self._exchange
#
# 		return await self._set_exchange()
#
#
# class BaseMessagingQueue(BaseMessagingExchange, ABC):
# 	_queue: AbstractQueue | None = None
#
# 	def __init__(
# 			self,
# 			queue_kwargs: dict | None = None,
# 			bind_kwargs: dict| None = None,
# 			**kwargs,
# 	):
# 		super().__init__(**kwargs)
#
# 		self._queue_kwargs = queue_kwargs or {}
# 		self._bind_kwargs = bind_kwargs or {}
#
# 		if self._exchange_name and 'routing_key' not in self._bind_kwargs:
# 			raise ValueError("'routing_key' is required when binding to a named exchange")
#
# 	async def _create_queue(self) -> AbstractQueue:
# 		if self._queue:
# 			return self._queue
#
# 		channel = await self.get_channel()
# 		self._queue = await channel.declare_queue(**self._queue_kwargs)
#
# 		if self._exchange_name:
# 			exchange = await self.get_exchange()
# 			await self._queue.bind(exchange, **self._bind_kwargs)
#
# 		return self._queue
#
# 	async def get_queue(self) -> AbstractQueue:
# 		if self._queue:
# 			return self._queue
#
# 		return await self._create_queue()
