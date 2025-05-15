from email.message import EmailMessage

from abc import ABC, abstractmethod

from jinja2 import TemplateNotFound

from config import settings
from core.loggers import log
from core.messaging import MessagingMasterWorkerABC
from smtp_connection import SmtpConnection


class SendEmailWorker(MessagingMasterWorkerABC, ABC):
	from_email: str = settings.DEFAULT_FROM_EMAIL
	subject: str

	@classmethod
	@abstractmethod
	async def get_html_content(cls, data: dict) -> str:
		raise NotImplementedError

	@classmethod
	@abstractmethod
	async def get_plain_text_content(cls, data: dict) -> str:
		raise NotImplementedError

	@classmethod
	async def get_mail(cls, to_email, data) -> EmailMessage:
		if to_email is None:
			raise ValueError('to_email cannot be None')

		plain_text_content = await cls.get_plain_text_content(data)
		html_content = await cls.get_html_content(data)

		mail = EmailMessage()
		mail["From"] = cls.from_email
		mail["To"] = to_email
		mail["Subject"] = getattr(cls, "subject", "Default Subject")

		# Attach plain text and HTML parts
		mail.set_content(plain_text_content, "plain")
		mail.add_alternative(html_content, subtype="html")

		return mail

	@classmethod
	async def callback(cls, data: dict, *args, **kwargs) -> None:
		log.info(f'Received message (callback): {data}')
		to_email = data.pop('email', None)
		try:
			mail = await cls.get_mail(to_email, data)
		except (ValueError, KeyError, TemplateNotFound) as e:
			log.error(f"Error while building email: {e}")
			return None

		try:
			smtp = await SmtpConnection.get_connection()
			await smtp.send_message(mail)
		except Exception as e:
			log.error(f"Error sending email: {e}")

		await cls.log_success(data, to_email)
		return None

	@classmethod
	async def log_success(cls, data: dict, to_email: str | None) -> None:
		log.info(f"Sent email with subject <{cls.subject}> to <{to_email}>")



class SendConfirmationEmailWorker(SendEmailWorker, ABC):

	@staticmethod
	async def build_confirmation_link(data: dict):
		raise NotImplementedError

