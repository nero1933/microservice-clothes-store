import asyncio

from core import settings
from core.messaging import BaseMessagingConnection
from loggers import default_logger
from messaging.workers import auth_authenticate_worker


async def main():
	rabbitmq = BaseMessagingConnection()
	await rabbitmq.setup_connection(settings.rabbitmq_url)

	workers = [
		await auth_authenticate_worker,
	]

	await asyncio.gather(*[await worker.start() for worker in workers])


if __name__ == "__main__":

	default_logger.info("* * Worker started")
	asyncio.run(main())