from abc import ABC, abstractmethod

from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession

from loggers import default_logger
from .base import BaseMessagingQueue
from ..db import AsyncSessionLocal


class BaseWorker(BaseMessagingQueue, ABC):
	def __init__(
			self,
			queue_kwargs: dict,
			exchange_kwargs: dict | None = None,
			bind_kwargs: dict | None = None,
			db: AsyncSession | None = None,
	):
		super().__init__(
			queue_kwargs,
			exchange_kwargs or {},
			bind_kwargs or {}
		)
		self.db: AsyncSession | None = db

	@abstractmethod
	async def handle_message(self, message: AbstractIncomingMessage):
		""" Must be implemented by subclass """
		pass

	async def start(self):
		# while True:
		# 	try:
		queue = await self.get_queue()
		async with queue.iterator() as queue_iter:
			message: AbstractIncomingMessage
			async for message in queue_iter:
				async with message.process():
					try:
						default_logger.info(
							f"[x] Received message {message.correlation_id} "
							f"on queue {queue.name}"
						)
						await self.handle_message(message)
					except Exception as e:
						error = (
							f"Processing error for "
							f"{message.correlation_id}. {str(e)}"
						)
						default_logger.error(f"[!] {error}")
		# except Exception:
		# 	default_logger.exception(
		# 		"Worker encountered an error, retrying in 5 seconds..."
		# 	)
		# 	await asyncio.sleep(5)


class BaseRPCWorker(BaseWorker):
	def __init__(self, *args, message_kwargs: dict | None = None, **kwargs):
		super().__init__(*args, **kwargs)
		self._message_kwargs = message_kwargs or {}
		self._message_kwargs.pop('body', None)
		self._message_kwargs.pop('correlation_id', None)

	async def handle_message(self, message: AbstractIncomingMessage):
		response = await self.handle_rpc(message)
		exchange = await self.get_exchange()
		await exchange.publish(
			Message(
				body=response,
				correlation_id=message.correlation_id,
				**self._message_kwargs
			),
			routing_key=message.reply_to
		)

	@abstractmethod
	async def handle_rpc(self, message: AbstractIncomingMessage) -> bytes:
		pass


async def get_worker(
		worker: type[BaseWorker] | type[BaseRPCWorker],
		db: bool = False,
		*args, **kwargs
):
	""" Factory method for creating worker instances with db session of db=True """
	if db:
		async with AsyncSessionLocal() as session:
			return worker(*args, **kwargs, db=session)

	return worker(*args, **kwargs)
