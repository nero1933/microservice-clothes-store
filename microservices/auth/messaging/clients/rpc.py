from __future__ import annotations
from core.messaging import RPCCreator
from typing import Dict

from core.messaging.base import RPCSingleton


class RPCUsersGetAuthData(RPCCreator, RPCSingleton):
	async def __call__(self, username: str, password: str) -> Dict[str, str | bool]:
		rpc = await self.get_rpc()
		res = await rpc.call(
			"rpc.users.get_auth_data",
			kwargs={
				"username": username,
				"password": password
			}
		)
		return res
