import asyncio

from aio_pika.patterns import RPC

from config import settings
from core.messaging import BaseMessagingConnection
from loggers import default_logger
from messaging.workers.rpc import RPCUsersGetAuthData




async def main():
	rabbit = BaseMessagingConnection()
	await rabbit.setup_connection(settings.rabbitmq_url)
	await RPCUsersGetAuthData.register()


	try:
		await asyncio.Future()
	finally:
		await rabbit.disconnect()



if __name__ == "__main__":
	default_logger.info("* * Worker started")
	asyncio.run(main())
