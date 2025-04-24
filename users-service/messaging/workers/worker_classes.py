import json

from aio_pika.abc import AbstractIncomingMessage

from core.messaging.base_workers import BaseRPCWorker, get_worker
from loggers import default_logger
from services import LoginService


class AuthAuthenticateRPCWorker(BaseRPCWorker):
	async def handle_rpc(self, message: AbstractIncomingMessage) -> bytes:
		# async with message.process(requeue=False):
			# assert message.reply_to is not None
		body = json.loads(message.body.decode())
		login_service = LoginService(self.db)
		data = await login_service.authenticate(body['username'], body['password'])

		if data.get("user_id"):
			default_logger.info("[.] Authenticated")
		else:
			default_logger.info("[.] Not Authenticated")

		return json.dumps(data).encode()


test_worker = get_worker(
	AuthAuthenticateRPCWorker,
	queue_kwargs={"name": "rpc.users.get_auth_data"},
	db=True
)
