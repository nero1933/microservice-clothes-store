from core.messaging import MessagingRPCWorkerABC
from services import LoginService
from core.db import AsyncSessionLocal
from core.loggers import log


class UsersAuthenticateRPC(MessagingRPCWorkerABC):
	queue_name = 'rpc.users.authenticate'

	@staticmethod
	async def callback(username, password) -> dict:
		log.info(
			f'[x] RPC | USERS received AUTH call <authenticate: {username}>'
		)
		async with AsyncSessionLocal() as db:
			login_service = LoginService(db)
			data = await login_service.authenticate(username, password)

		return data
