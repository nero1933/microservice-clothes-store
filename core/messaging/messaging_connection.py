from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from ..base_connection import BaseConnection
from ..loggers import log


class MessagingConnection(BaseConnection):
	_connection: AbstractRobustConnection | None = None
	_url: str | None = None
	_channel: AbstractChannel | None = None
	_name = 'RabbitMQ'

	@classmethod
	async def _connect(cls, url: str | None = None) -> AbstractRobustConnection:
		if cls._connection is None or cls._connection.is_closed:
			cls._connection = await connect_robust(url)

		return cls._connection

	@classmethod
	async def _check_connection(cls) -> bool:
		if cls._connection is None or cls._connection.is_closed:
			return False

		return True

	@classmethod
	async def disconnect(cls) -> None:
		if cls._connection and not cls._connection.is_closed:
			await cls._connection.close()
			cls._connection = None
			log.info(f"Disconnected from {cls._name}")

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
