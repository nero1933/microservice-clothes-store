from aiosmtplib import SMTP

from config import settings
from core.base_connection import BaseConnection
from core.loggers import log


class SmtpConnection(BaseConnection):
	_name = 'SMTP'

	@classmethod
	async def validate_url(cls, url: str):
		return None

	@classmethod
	async def _connect(cls, url: str | None = None):
		if cls._connection is None or cls._connection.is_closed:
			smtp = SMTP(
				hostname=settings.SMTP_HOST,
				port=settings.SMTP_PORT,
			)
			await smtp.connect()
			cls._connection = smtp

		return cls._connection

	@classmethod
	async def _check_connection(cls) -> bool:
		if cls._connection is None or not cls._connection.is_connected:
			return False

		return True

	@classmethod
	async def disconnect(cls) -> None:
		if await cls._check_connection():
			await cls._connection.quit()

		log.info(f"Disconnected from {cls._name}")
