from abc import ABC

from core.cache import CacheConnection


class BaseConfirmationCache(CacheConnection, ABC):
	"""
	Sets confirmation key and counter with values in the cache.
	"""
	confirmation_key_template: str
	confirmation_counter_template: str

	@classmethod
	async def _get_confirmation_key(cls, conf_token: str) -> str:
		return cls.confirmation_key_template.format(key_id=conf_token)

	@classmethod
	async def _get_confirmation_counter_key(cls, user_id: str) -> str:
		return cls.confirmation_counter_template.format(key_id=user_id)
