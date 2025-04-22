import json
from typing import Callable, Awaitable, Optional

from aio_pika import connect, Message
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from core.db import AsyncSessionLocal
from loggers import default_logger


async def get_rpc_worker(
    	queue_name: str,
    	handler: Callable[[AbstractIncomingMessage, AsyncSession], Awaitable[bytes]],
		db: bool,
):
	if db:
		async with AsyncSessionLocal() as session:
			await rpc_worker(queue_name, handler, session)
	else:
		await rpc_worker(queue_name, handler)


async def rpc_worker(
    	queue_name: str,
    	handler: Callable[[AbstractIncomingMessage, AsyncSession], Awaitable[bytes]] |
				 Callable[[AbstractIncomingMessage], Awaitable[bytes]],
		db: AsyncSession | None = None,
) -> None:
	# Perform connection
	connection = await connect(settings.rabbitmq_url)

	# Creating a channel
	channel = await connection.channel()
	exchange = channel.default_exchange

	# Declaring queue
	queue = await channel.declare_queue(queue_name, auto_delete=True)

	# Start listening the queue
	async with queue.iterator() as qiterator:
		message: AbstractIncomingMessage
		async for message in qiterator:
			try:
				default_logger.info(f"[x] Received message {message.correlation_id}")

				response = await handler(message, db) if db else await handler(message)
				await exchange.publish(
					Message(
						body=response,
						correlation_id=message.correlation_id,
					),
					routing_key=message.reply_to,
				)

				default_logger.info(f"[.] Message {message.correlation_id} completed")

			except Exception:
				default_logger.exception(f"[!] Processing error for {message.correlation_id}")

