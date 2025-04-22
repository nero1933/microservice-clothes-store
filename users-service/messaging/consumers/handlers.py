import json
from typing import Awaitable

from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import AsyncSessionLocal, get_async_session
from core.db.db_config import engine
from loggers import default_logger
from models import User
from services import LoginService
from utils import password as p


async def handle_auth_authenticate(
		message: AbstractIncomingMessage,
		db: AsyncSession
) -> bytes:
	async with message.process(requeue=False):
		# assert message.reply_to is not None
		body = json.loads(message.body.decode())
		login_service = LoginService(db)

		data = await login_service.authenticate(body['username'], body['password'])

		default_logger.info("[.] Authenticated" if data.get('user_id') else '[.] Not Authenticated')
		return json.dumps(data).encode()