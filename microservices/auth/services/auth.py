from typing import Dict

from core.messaging import BaseMessagingConnection
from loggers import default_logger
from messaging.clients.rpc import RPCUsersGetAuthData


class AuthService(BaseMessagingConnection):
	@staticmethod
	async def authenticate(username: str, password: str) -> Dict[str, str | bool]:
		auth_data = await RPCUsersGetAuthData.call(username=username, password=password)
		default_logger.info(f'[X] RPC | AUTH received USERS data: {auth_data}')
		return auth_data
