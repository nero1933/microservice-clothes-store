from __future__ import annotations
from typing import Dict
from core.messaging import RPCClientABC
from loggers import default_logger


class RPCUsersGetAuthData(RPCClientABC):
	@classmethod
	async def call(cls, username: str, password: str) -> Dict[str, str | bool]:
		rpc = await cls.get_rpc()
		default_logger.info(
			f'[x] RPC | AUTH calling USERS to "get_auth_data": {username}'
		)
		return await rpc.call(
			"rpc.users.get_auth_data",
			kwargs={
				"username": username,
				"password": password
			}
		)
