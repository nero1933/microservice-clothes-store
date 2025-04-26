from typing import Dict

from core.messaging import BaseMessagingConnection
from loggers import default_logger
from messaging.clients.rpc import RPCUsersGetAuthData


class AuthService(BaseMessagingConnection):
	@staticmethod
	async def authenticate(username: str, password: str) -> Dict[str, str | bool]:
		rpc = RPCUsersGetAuthData()
		auth_data = await rpc(username=username, password=password)
		default_logger.info(f'AUTH DATA: {auth_data}')
		return {}
