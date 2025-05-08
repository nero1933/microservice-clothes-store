import asyncio

from config import settings
from core.messaging import BaseMessagingConnection
from core.loggers import log
from workers.rpc import UsersAuthenticateRPC


async def main():
	RPCs = (UsersAuthenticateRPC, )
	rabbit = BaseMessagingConnection()
	await rabbit.setup_connection(settings.rabbitmq_url)
	for RPC in RPCs:
		await RPC.register()

	try:
		await asyncio.Future()
	finally:
		await rabbit.disconnect()


if __name__ == "__main__":
	log.info("Worker started")
	asyncio.run(main())
