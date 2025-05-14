from email.message import EmailMessage

from jinja2 import TemplateNotFound
from sendgrid import Content

from config import settings
from core.loggers import log
from templates import render_template
from .send_email import SendConfirmationEmailWorker


class SendResetPasswordEmailWorker(SendConfirmationEmailWorker):
	queue_name = 'email.send.reset_password'
	subject: str = 'Password reset'

	@classmethod
	async def get_html_content(cls, data: dict) -> str:
		try:
			reset_link = await cls.build_confirmation_link(data)
			return render_template(
				"reset_password.html",
				{'reset_link': reset_link}
			)
		except TemplateNotFound as e:
			log.error(f"Template not found: {e}")
			raise

	@classmethod
	async def get_plain_text_content(cls, data: dict) -> str:
		reset_link = await cls.build_confirmation_link(data)
		return f"Use the following link to reset your password: {reset_link}"

	@staticmethod
	async def build_confirmation_link(data: dict) -> str:
		if 'reset_id' not in data:
			raise KeyError("Missing 'reset_id' in data")

		url = settings.RESET_PASSWORD_URL
		return url.format(reset_id=data['reset_id'])
