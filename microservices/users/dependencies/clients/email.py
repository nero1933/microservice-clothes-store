from messaging.clients import ResetPasswordEmailClient


def get_reset_password_email_client() -> ResetPasswordEmailClient:
	return ResetPasswordEmailClient()