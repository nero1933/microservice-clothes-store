import asyncio

from aio_pika import connect_robust, connect
from aio_pika.patterns import RPC

from config import settings
from core.messaging import BaseMessagingConnection
from loggers import default_logger


async def authenticate(username, password):
	print(f"Authenticating user {username}, {password}")
	return {'user_id': '9e2fbe43-7486-4d3f-9323-6b0fae4e2f4e'}


async def main():
	rabbitmq = BaseMessagingConnection()
	await rabbitmq.setup_connection(settings.rabbitmq_url)
	channel = await rabbitmq.get_channel()

	rpc = await RPC.create(channel)
	await rpc.register("rpc.users.authenticate", authenticate, auto_delete=True)

	try:
		await asyncio.Future()
	finally:
		await rpc.close()
		await channel.close()
		await rabbitmq.disconnect()


if __name__ == "__main__":

	default_logger.info("* * Worker started")
	asyncio.run(main())