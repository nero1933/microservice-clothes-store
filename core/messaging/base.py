from abc import ABC

from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractRobustConnection, AbstractExchange, \
	AbstractQueue

from loggers import default_logger


class BaseMessagingConnection:
	_connection: AbstractRobustConnection | None = None
	_url: str | None = None

	def __init__(self) -> None:
		self._channel: AbstractChannel | None = None

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
				cls._connection = await connect_robust(url)
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

	async def _create_channel(self):
		if self._channel:
			return self._channel

		connection = await self.get_connection()
		self._channel = await connection.channel()

		return self._channel

	async def get_channel(self):
		if self._channel is None:
			return await self._create_channel()

		return self._channel


class BaseMessagingExchange(BaseMessagingConnection, ABC):
	_exchange: AbstractExchange | None = None

	def __init__(
			self,
			exchange_kwargs: dict
	) -> None:
		super().__init__()
		self._exchange_name = (exchange_kwargs or {}).get('name') or None
		self._exchange_kwargs = exchange_kwargs if self._exchange_name else None

	async def _set_exchange(self) -> AbstractExchange:
		if self._exchange:
			return self._exchange

		channel = await self.get_channel()
		if self._exchange_name:
			self._exchange = await channel.declare_exchange(
				**self._exchange_kwargs
			)
		else:
			self._exchange = channel.default_exchange

		return self._exchange

	async def get_exchange(self) -> AbstractExchange:
		if self._exchange:
			return self._exchange

		return await self._set_exchange()


class BaseMessagingQueue(BaseMessagingExchange, ABC):
	_queue: AbstractQueue | None = None

	def __init__(
			self,
			queue_kwargs: dict,
			exchange_kwargs: dict,
			bind_kwargs: dict,
	):
		super().__init__(exchange_kwargs)

		self._queue_kwargs = queue_kwargs
		self._bind_kwargs = bind_kwargs or {}

		if self._exchange_name and 'routing_key' not in self._bind_kwargs:
			raise ValueError("'routing_key' is required when binding to a named exchange")

	async def _create_queue(self) -> AbstractQueue:
		if self._queue:
			return self._queue

		channel = await self.get_channel()
		self._queue = await channel.declare_queue(**self._queue_kwargs)

		if self._exchange_name:
			exchange = await self.get_exchange()
			await self._queue.bind(exchange, **self._bind_kwargs)

		return self._queue

	async def get_queue(self) -> AbstractQueue:
		if self._queue:
			return self._queue

		return await self._create_queue()



# class RabbitMQBase(RabbitMQConnectionManager, ABC):
# 	def __init__(
# 			self,
# 			queue_name: str,
# 			exchange_name: str | None = None,
# 			exchange_type: ExchangeType = ExchangeType.DIRECT,
# 			auto_delete: bool = True,
# 	):
# 		self.queue_name = queue_name
# 		self.exchange_name = exchange_name
# 		self.exchange_type = exchange_type
# 		self.auto_delete = auto_delete
#
# 		self.channel: AbstractChannel | None = None
# 		self.exchange: AbstractExchange | None = None
# 		self.queue: AbstractQueue | None = None
#
# 	async def setup(self):
# 		""" Creates channel, exchange and queue """
#
# 		# Create a channel
# 		self.channel = await self.create_channel()
#
# 		# If 'exchange_name' was provided create a custom exchange
# 		if self.exchange_name:
# 			self.exchange = await self.channel.declare_exchange(
# 				self.exchange_name,
# 				type=self.exchange_type,
# 				durable=True,
# 			)
# 		else:
# 			self.exchange = self.channel.default_exchange
#
# 		# Create a queue
# 		self.queue = await self.channel.declare_queue(
# 			self.queue_name,
# 			auto_delete=self.auto_delete,
# 		)
#
# 		# If exchange is custom -- bind queue
# 		if self.exchange_name:
# 			await self.queue.bind(self.exchange, routing_key=self.queue_name)
#
# 	@abstractmethod
# 	async def handle_message(self, message: IncomingMessage) -> None:
# 		"""Метод, который должен быть реализован в потомках."""
# 		pass
#
# 	async def run(self) -> None:
# 		"""Запускает воркер и начинает слушать очередь."""
# 		await self.setup()
# 		async with self.queue.iterator() as queue_iter:
# 			async for message in queue_iter:
# 				try:
# 					await self.handle_message(message)
# 				except Exception as e:
# 					print(f"[!] Error while handling message: {e}")
