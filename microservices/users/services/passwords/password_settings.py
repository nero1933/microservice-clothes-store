from config import settings


class PasswordCacheSettings:
	confirmation_key_template: str = settings.RESET_PASSWORD_KEY_TEMPLATE
	timeout_key: int = settings.RESET_PASSWORD_KEY_TIMEOUT

	confirmation_counter_template: str = settings.RESET_PASSWORD_COUNTER_TEMPLATE
	timeout_counter: int = settings.RESET_PASSWORD_COUNTER_TIMEOUT

	max_attempts: int = settings.RESET_PASSWORD_MAX_ATTEMPTS
