from core.loggers import log
from .send_email import SendConfirmationEmailWorker


class SendResetPasswordEmailWorker(SendConfirmationEmailWorker):
	queue_name = 'email.send.reset_password'

	@staticmethod
	async def send_mail(data: dict):
		log.info(f'Received message (send_mail): {data}')
