from email.message import EmailMessage

from core.loggers import log
from .send_email import SendConfirmationEmailWorker


class SendResetPasswordEmailWorker(SendConfirmationEmailWorker):
	queue_name = 'email.send.reset_password'
	subject: str = 'Password reset'
	body: str

	@classmethod
	async def get_email_message(cls, data: dict):
		pass

	@classmethod
	async def get_email_message(cls, data: dict) -> EmailMessage:
		log.info(f'Received message (send_mail): {data}')

		msg = EmailMessage()
		msg["From"] = cls.from_email
		msg["To"] = data.get("email")
		msg["Subject"] = 'Password reset'
		msg.set_content(f"Visit http://users.localhost/api/v1/reset-password/{data.get("reset_id")} to reset your password.")

		reset_id = data.get('reset_id')
		html = f"""
		<html>
		  <body>
		    <p>Click the link below to reset your password:</p>
		    <p><a href="http://users.localhost/api/v1/reset-password/{reset_id}">LINK</a></p>
		    <p>{reset_id}</p>
		  </body>
		</html>
		"""

		msg.add_alternative(html, subtype="html")
		return msg

