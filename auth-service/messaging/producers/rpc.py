import asyncio
import json
from typing import MutableMapping

import uuid

from aio_pika import Message
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue, AbstractIncomingMessage

from loggers import default_logger
from messaging.connection_manager import rabbitmq


class RPCClient:
	connection: AbstractConnection
	channel: AbstractChannel | None = None
	callback_queue: AbstractQueue

	def __init__(self) -> None:
		self.futures: MutableMapping[str, asyncio.Future] = {}

	async def connect(self) -> "RPCClient":
		if not self.channel:
			self.channel = await rabbitmq.create_channel()

		return self

	async def on_response(self, message: AbstractIncomingMessage) -> None:
		if message.correlation_id is None:
			default_logger.warning(f"Received message without correlation_id: {message!r}")
			return

		future: asyncio.Future = self.futures.pop(message.correlation_id)
		future.set_result(message.body)

	async def call(self, data: dict, routing_key: str) -> bytes:
		callback_queue = await self.channel.declare_queue(exclusive=True, auto_delete=True)

		correlation_id = str(uuid.uuid4())
		loop = asyncio.get_running_loop()
		future = loop.create_future()
		self.futures[correlation_id] = future
		consumer_tag = await callback_queue.consume(self.on_response, no_ack=True)

		body = json.dumps(data).encode()
		default_logger.info(f"Calling {correlation_id} to {routing_key} with data={data}")

		await self.channel.default_exchange.publish(
			Message(
				body,
				content_type="text/plain",
				correlation_id=correlation_id,
				reply_to=callback_queue.name,
			),
			routing_key=routing_key,
		)

		try:
			result = await asyncio.wait_for(future, timeout=5.0)
		finally:
			await callback_queue.cancel(consumer_tag)
			await callback_queue.delete()

		return result


rpc_client = RPCClient()
