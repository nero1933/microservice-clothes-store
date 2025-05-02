from typing import Dict

from core.loggers import log
from messaging.clients.rpc import RPCUsersGetAuthData


class AuthService(RPCUsersGetAuthData):

	async def authenticate(self, username: str, password: str) -> Dict[str, str | bool]:
		auth_data = await self.call(username=username, password=password)
		log.info(f'[X] RPC | AUTH received USERS data: {auth_data}')
		return auth_data
