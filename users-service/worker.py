import asyncio

from messaging.consumers.rpc_worker import rpc_worker
from messaging.consumers.handlers import handle_auth_authenticate


if __name__ == "__main__":
	asyncio.run(rpc_worker("rpc.users.get_auth_data", handle_auth_authenticate))
