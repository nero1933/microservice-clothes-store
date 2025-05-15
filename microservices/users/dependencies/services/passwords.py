from services.passwords import PasswordSetConfirmationCacheService, \
	PasswordGetConfirmationCacheService


def get_pwd_set_conf_cache_service() -> PasswordSetConfirmationCacheService:
	return PasswordSetConfirmationCacheService()

def get_pwd_get_conf_cache_service() -> PasswordGetConfirmationCacheService:
	return PasswordGetConfirmationCacheService()
