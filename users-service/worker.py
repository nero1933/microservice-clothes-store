import asyncio
import logging

import json

from aio_pika import connect, Message
from aio_pika.abc import AbstractIncomingMessage

from core import settings
from core.db.db_config import AsyncSessionLocal
from loggers import default_logger
from services import LoginService


async def handle_message(message: AbstractIncomingMessage):
	async with message.process():
		assert message.reply_to is not None
		message_id = message.correlation_id
		default_logger.info(f"[x] Received message {message_id}")

		async with AsyncSessionLocal() as session:
			login_service = LoginService(session)

		body = json.loads(message.body.decode())
		data = await login_service.authenticate(body['username'], body['password'])
		response = json.dumps(data).encode()

		default_logger.info("[.] Authenticated" if data else '[.] Not Authenticated')

		return response


async def main() -> None:
	# Perform connection
	connection = await connect(settings.rabbitmq_url)

	# Creating a channel
	channel = await connection.channel()
	exchange = channel.default_exchange

	# Declaring queue
	queue = await channel.declare_queue("rpc_queue")

	# Start listening the queue with name 'hello'
	async with queue.iterator() as qiterator:
		message: AbstractIncomingMessage
		async for message in qiterator:
			try:
				response = await handle_message(message)
				await exchange.publish(
					Message(
						body=response,
						correlation_id=message.correlation_id,
					),
					routing_key=message.reply_to,
				)
				default_logger.info(f"[.] Message {message.correlation_id} completed")

			except Exception:
				logging.exception(f"[!] Processing error for {message.correlation_id}")


if __name__ == "__main__":
	asyncio.run(main())
