import asyncio
import json
import logging
from typing import MutableMapping

import uuid

from aio_pika import connect, Message
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue, AbstractIncomingMessage

from core import settings
from loggers import default_logger


class RPCClient:
	connection: AbstractConnection
	channel: AbstractChannel
	callback_queue: AbstractQueue

	def __init__(self) -> None:
		self.futures: MutableMapping[str, asyncio.Future] = {}

	async def connect(self) -> "RPCClient":
		self.connection = await connect(settings.rabbitmq_url)
		self.channel = await self.connection.channel()
		self.callback_queue = await self.channel.declare_queue(exclusive=True)
		await self.callback_queue.consume(self.on_response, no_ack=True)

		return self

	async def on_response(self, message: AbstractIncomingMessage) -> None:
		if message.correlation_id is None:
			print(f"Bad message {message!r}")
			return

		future: asyncio.Future = self.futures.pop(message.correlation_id)
		future.set_result(message.body)

	async def call(self, data: dict) -> int:
		correlation_id = str(uuid.uuid4())
		loop = asyncio.get_running_loop()
		future = loop.create_future()
		self.futures[correlation_id] = future

		body = json.dumps(data).encode()
		# logging.info(f"Calling {correlation_id} with {body!r}")
		default_logger.info(f"Calling {correlation_id}")

		await self.channel.default_exchange.publish(
			Message(
				body,
				content_type="text/plain",
				correlation_id=correlation_id,
				reply_to=self.callback_queue.name,
			),
			routing_key="rpc_queue",

		)

		return await future
