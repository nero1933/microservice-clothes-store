import json
from typing import Callable, Awaitable, Optional

from aio_pika import connect, Message
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from core.db import AsyncSessionLocal
from core.messaging.base_workers import BaseRPCWorker, get_worker_with_db
from loggers import default_logger
from services import LoginService


class AuthAuthenticateRPCWorker(BaseRPCWorker):
	async def handle_rpc(self, message: AbstractIncomingMessage) -> bytes:
		# async with message.process(requeue=False):
			# assert message.reply_to is not None
		body = json.loads(message.body.decode())
		login_service = LoginService(self.db)
		data = await login_service.authenticate(body['username'], body['password'])

		if data.get("user_id"):
			default_logger.info("[.] Authenticated")
		else:
			default_logger.info("[.] Not Authenticated")

		return json.dumps(data).encode()


test_worker = get_worker_with_db(
	AuthAuthenticateRPCWorker,
	queue_kwargs={"name": "rpc.users.get_auth_data"},
)

# async def get_rpc_worker(
#     	queue_name: str,
#     	handler: Callable[[AbstractIncomingMessage, AsyncSession], Awaitable[bytes]],
# 		db: bool,
# ):
# 	if db:
# 		async with AsyncSessionLocal() as session:
# 			await rpc_worker(queue_name, handler, session)
# 	else:
# 		await rpc_worker(queue_name, handler)
#
#
# async def rpc_worker(
#     	queue_name: str,
#     	handler: Callable[[AbstractIncomingMessage, AsyncSession], Awaitable[bytes]] |
# 				 Callable[[AbstractIncomingMessage], Awaitable[bytes]],
# 		db: AsyncSession | None = None,
# ) -> None:
# 	# Perform connection
# 	connection = await connect(settings.rabbitmq_url)
#
# 	# Creating a channel
# 	channel = await connection.channel()
# 	exchange = channel.default_exchange
#
# 	# Declaring queue
# 	queue = await channel.declare_queue(queue_name, exclusive=True, auto_delete=True)
#
# 	# Start listening the queue
# 	async with queue.iterator() as qiterator:
# 		message: AbstractIncomingMessage
# 		async for message in qiterator:
# 			try:
# 				default_logger.info(f"[x] Received message {message.correlation_id}")
#
# 				response = await handler(message, db) if db else await handler(message)
# 				await exchange.publish(
# 					Message(
# 						body=response,
# 						correlation_id=message.correlation_id,
# 					),
# 					routing_key=message.reply_to,
# 				)
#
# 				default_logger.info(f"[.] Message {message.correlation_id} completed")
#
# 			except Exception:
# 				default_logger.exception(f"[!] Processing error for {message.correlation_id}")
#
