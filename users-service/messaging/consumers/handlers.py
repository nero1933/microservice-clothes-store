import json

from aio_pika.abc import AbstractIncomingMessage

from core.db import AsyncSessionLocal
from loggers import default_logger
from services import LoginService


async def handle_auth_authenticate(message: AbstractIncomingMessage):
	body = json.loads(message.body.decode())
	async with message.process():
		# assert message.reply_to is not None
		async with AsyncSessionLocal() as session:
			login_service = LoginService(session)
			data = await login_service.authenticate(body['username'], body['password'])

		default_logger.info("[.] Authenticated" if data else '[.] Not Authenticated')
		return json.dumps(data).encode()
