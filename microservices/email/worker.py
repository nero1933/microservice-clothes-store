import asyncio

from config import settings
from core.messaging import BaseMessagingConnection
# from loggers import default_logger


async def main():
	# workers = (None, )
	rabbit = BaseMessagingConnection()
	await rabbit.setup_connection(settings.rabbitmq_url)
	# for worker in workers:
	# 	await worker.register()

	try:
		await asyncio.Future()
	finally:
		await rabbit.disconnect()


if __name__ == "__main__":
	# default_logger.info("* * Worker started")
	asyncio.run(main())
