from services import LoginService
from core.db import AsyncSessionLocal
from core.messaging import RPCWorkerABC
from loggers import default_logger


class RPCUsersGetAuthData(RPCWorkerABC):
	_method_name = 'rpc.users.authenticate'

	@staticmethod
	async def callback(username, password) -> dict:
		default_logger.info(
			f'[x] RPC | USERS received AUTH call "authenticate": {username}'
		)
		async with AsyncSessionLocal() as db:
			login_service = LoginService(db)
			data = await login_service.authenticate(username, password)
			default_logger.info(f"[x] Authentication completed")

		return data
