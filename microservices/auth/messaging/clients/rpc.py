from typing import Dict
from core.messaging import RPCClientABC
from loggers import default_logger


class RPCUsersGetAuthData(RPCClientABC):
	@classmethod
	async def call(cls, username: str, password: str) -> Dict[str, str | bool]:
		rpc = await cls.get_rpc()
		default_logger.info(
			f'[X] RPC | AUTH calling USERS to "authenticate": {username}'
		)
		return await rpc.call(
			"rpc.users.authenticate",
			kwargs={
				"username": username,
				"password": password
			}
		)
