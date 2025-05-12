from services import PasswordConfirmationCacheService


def get_pwd_conf_cache_service() -> PasswordConfirmationCacheService:
	return PasswordConfirmationCacheService()
