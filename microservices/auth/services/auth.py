from core.loggers import log
from core.messaging import MessagingRPCClientABC


class AuthRPCService(MessagingRPCClientABC):
	queue_name: str = "rpc.users.authenticate"

	async def authenticate(self, username: str, password: str) -> dict[str] | dict:
		try:
			log.info(f'[X] RPC | AUTH calls USERS')
			auth_data = await self.call(username=username, password=password)
			if auth_data:
				res = auth_data.get("user_id")[:8]
			else:
				res = None
			log.info(
				f'[X] RPC | AUTH received USERS data: <user_id={res}...>'
			)
		except Exception as e:
			log.warning(f'[!] RPC | AUTH Call failed: {e}')
			return {}

		return auth_data
