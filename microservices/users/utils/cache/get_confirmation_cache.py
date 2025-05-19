import json

from core.loggers import log
from exceptions import ConfirmationKeyExpiredCacheException, \
	ConfirmationCounterKeyExpiredCacheException, InvalidConfirmationKeyCacheException
from .base_confirmation_cache import BaseConfirmationCache


class BaseGetConfirmationCache(BaseConfirmationCache):
	"""
	Confirmation data in cache is stored like this:

	First record:
	- Confirmation key is 'confirmation_key'
	- Confirmation value is 'user_id'

	Second record:
	- Counter key is 'confirmation_counter_key'
	- Counter value is {'confirmation_key': counter}

	"""
	confirmation_key_template: str
	confirmation_counter_template: str
	_user_id: str | None = None

	async def get_user_id_from_cache(self, conf_token: str) -> str:
		"""
		Pass 'conf_token' to get 'user_id'
		"""
		if not self._user_id:
			cache = await self.get_connection()
			confirmation_key = await self._get_confirmation_key(conf_token)
			confirmation_data_json = await cache.get(confirmation_key)
			if confirmation_data_json is None:
				raise ConfirmationKeyExpiredCacheException(
					"Confirmation key expired or does not exist"
				)
			confirmation_data = json.loads(confirmation_data_json)
			self._user_id = confirmation_data['user_id']

		return self._user_id

	async def _get_counter_value_from_cache(self, user_id: str) -> dict:
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
		Checks that provided 'confirmation_key' matches latest one stored that is in
		'counter_value' dict stored with key

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
