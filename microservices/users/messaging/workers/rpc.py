from api.v1.services import LoginService
from core.db import AsyncSessionLocal
from core.messaging import RPCWorkerABC
from loggers import default_logger


class RPCUsersGetAuthData(RPCWorkerABC):
	_method_name = 'rpc.users.get_auth_data'

	@staticmethod
	async def callback(username, password) -> dict:
		default_logger.info(
			f'[x] RPC | USERS received AUTH call "get_auth_data": {username}'
		)
		async with AsyncSessionLocal() as db:
			s = LoginService(db)
			d = await s.authenticate(username, password)
			default_logger.info(f"RES: {d}")

		return {'user_id': '9e2fbe43-7486-4d3f-9323-6b0fae4e2f4e'}
