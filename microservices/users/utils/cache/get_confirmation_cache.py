import json

from core.cache import CacheConnection
from exceptions import ConfirmationKeyExpiredCacheException, \
	ConfirmationCounterKeyExpiredCacheException, InvalidConfirmationKeyCacheException


class BaseGetConfirmationCache(CacheConnection):
	confirmation_key_template: str
	confirmation_counter_template: str
	_user_id: str | None = None

	async def _get_confirmation_key(self, key_id: str) -> str:
		return self.confirmation_key_template.format(key_id=key_id)

	async def _get_confirmation_counter_key(self, user_id: str) -> str:
		return self.confirmation_counter_template.format(key_id=user_id)

	async def get_user_id_from_cache(self, key_id: str) -> str:
		"""
		Pass 'confirmation_id' as 'key_id' to get 'user_id'
		"""
		if self._user_id:
			return self._user_id

		cache = await self.get_connection()
		confirmation_key = await self._get_confirmation_key(key_id)
		user_id = await cache.get(confirmation_key)
		if user_id is None:
			raise ConfirmationKeyExpiredCacheException(
				"Confirmation key expired or does not exist"
			)
		self._user_id = user_id
		return user_id

	async def _get_counter_value_from_cache(self, user_id: str) -> str:
		"""
		Pass 'user_id' as 'key_id' to get counter value
		"""

		cache = await self.get_connection()
		counter_key = await self._get_confirmation_counter_key(user_id)
		counter_value = await cache.get(counter_key)
		if counter_value is None:
			raise ConfirmationCounterKeyExpiredCacheException(
				"Confirmation counter key expired or does not exist"
			)
		return json.loads(counter_value)

	async def _check_confirmation_key(self, key_id, counter_value) -> bool:
		"""
		Check if the provided 'confirmation_key' matches the latest one stored in the cache.

    	The confirmation key stored in 'counter_value' represents the most recent key,
    	which may have changed if the user requested confirmation multiple times.
		"""
		confirmation_key = await self._get_confirmation_key(key_id)
		if confirmation_key not in counter_value:
			raise InvalidConfirmationKeyCacheException()

		return True

	async def validate_confirmation(self, key_id: str) -> bool:
		user_id = await self.get_user_id_from_cache(key_id)
		counter_value = await self._get_counter_value_from_cache(user_id)
		return await self._check_confirmation_key(key_id, counter_value)
