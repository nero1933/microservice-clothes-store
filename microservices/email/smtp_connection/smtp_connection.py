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
		if cls._connection is None:
			return False

		return True

	@classmethod
	async def disconnect(cls) -> None:
		connection = await cls.get_connection()
		await connection.quit()
		log.info(f"Disconnected from {cls._name}")
