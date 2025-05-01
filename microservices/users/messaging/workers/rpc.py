from services import LoginService
from core.db import AsyncSessionLocal
from core.messaging import RPCWorkerABC
from core.loggers import log


class RPCUsersGetAuthData(RPCWorkerABC):
	_method_name = 'rpc.users.authenticate'

	@staticmethod
	async def callback(username, password) -> dict:
		log.info(
			f'[x] RPC | USERS received AUTH call "authenticate": {username}'
		)
		async with AsyncSessionLocal() as db:
			login_service = LoginService(db)
			data = await login_service.authenticate(username, password)
			log.info(f"[x] Authentication completed")

		return data
