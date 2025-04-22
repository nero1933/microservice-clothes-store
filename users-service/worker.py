import asyncio

from loggers import default_logger
from messaging.consumers.rpc_worker import get_rpc_worker
from messaging.consumers.handlers import handle_auth_authenticate


async def main():
	workers = [
		get_rpc_worker("rpc.users.get_auth_data", handle_auth_authenticate, db=True)
	]

	await asyncio.gather(*workers)


if __name__ == "__main__":
	default_logger.info("* * Worker started")
	asyncio.run(main())