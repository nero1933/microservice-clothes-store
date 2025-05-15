import asyncio
import signal

from config import settings
from core.messaging import MessagingConnection
from core.loggers import log, sql_logger
from workers.rpc import UsersAuthenticateRPC

shutdown_event = asyncio.Event()


def shutdown():
	log.info("Shutdown signal received.")
	shutdown_event.set()


async def main():
	# workers = (,)
	RPCs = (UsersAuthenticateRPC, )
	rabbit = MessagingConnection()

	await rabbit.setup_connection(settings.rabbitmq_url)
	for RPC in RPCs:
		await RPC.register()

	# await rabbit.setup_connection(settings.rabbitmq_url)
	# for worker in workers:
	# 	await worker.create_worker()

	loop = asyncio.get_running_loop()
	loop.add_signal_handler(signal.SIGINT, shutdown)
	loop.add_signal_handler(signal.SIGTERM, shutdown)

	try:
		await shutdown_event.wait()
	finally:
		log.info("Shutting down gracefully...")
		await rabbit.disconnect()


if __name__ == "__main__":
	log.info("Worker started")
	asyncio.run(main())