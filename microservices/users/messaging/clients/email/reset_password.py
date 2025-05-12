from core.messaging import MessagingMasterClientABC


class ResetPasswordEmailClient(MessagingMasterClientABC):
	queue_name = 'email.send.reset_password'
