from typing import Dict, Union

from core.messaging import BaseMessagingConnection
from messaging.clients.instances import users_authenticate_rpc_client


class AuthService(BaseMessagingConnection):

	@staticmethod
	async def authenticate(username: str, password: str) -> Dict[str, Union[str, bool]]:
		rpc = await users_authenticate_rpc_client.get_rpc()
		res = await rpc.proxy.rpc.users.authenticate(username=username, password=password)
		return res
