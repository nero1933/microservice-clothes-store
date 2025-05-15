from utils.cache import BaseGetConfirmationCache
from .password_settings import PasswordCacheSettings


class PasswordGetConfirmationCacheService(BaseGetConfirmationCache,
										  PasswordCacheSettings):
	pass
