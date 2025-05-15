from utils import BaseSetConfirmationCache
from .password_settings import PasswordCacheSettings


class PasswordSetConfirmationCacheService(BaseSetConfirmationCache,
										  PasswordCacheSettings):
	pass
