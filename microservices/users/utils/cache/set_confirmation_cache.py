import json
import uuid
from typing import Any

from core.loggers import log
from exceptions.exceptions import OperationCacheException, \
	ExceedLimitConfirmationCacheException, ConfirmationCacheException
from .base_confirmation_cache import BaseConfirmationCache


class BaseSetConfirmationCache(BaseConfirmationCache):
	"""
	Sets confirmation key and counter with values in the cache.
	"""
	_confirmation_token: str | None = None

	confirmation_key_template: str
	timeout_key: int

	confirmation_counter_template: str
	timeout_counter: int

	max_attempts: int

	async def _set_confirmation_token(self) -> str:
		"""
		Sets a confirmation token, if token is None, or returns existing one
		"""
		if self._confirmation_token is None:
			self._confirmation_token = str(uuid.uuid4())

		return self._confirmation_token

	async def get_confirmation_token(self) -> str:
		"""
		Returns a confirmation token, or sets new one, if token is None.
		"""
		if self._confirmation_token:
			return self._confirmation_token

		return await self._set_confirmation_token()

	async def _cache_confirmation(
			self,
			key: str,
			data: dict[str, str | int],
			timeout: int,
	) -> str:
		"""
		Set the confirmation data in the cache.

		This method creates a confirmation key from the template,
		sets it in the cache with the provided data,
		and applies a timeout for expiry.
		"""
		if not isinstance(timeout, int):
			raise ValueError("Timeout should be an integer")

		cache = await self.get_connection()
		try:
			if isinstance(data, dict):
				data = json.dumps(data)

			await cache.set(
				key,
				data,
				ex=timeout
			)
			return key

		except Exception as e:
			error_message = f"Failed to set confirmation data in cache: {e}"
			log.error(error_message)
			raise OperationCacheException(error_message)

	async def handle_cache_confirmation(self, user_id: str) -> None:
		if not isinstance(user_id, str):
			raise ValueError("'user_id' should be a string")

		try:
			conf_token = await self.get_confirmation_token()
			confirmation_key = await self._get_confirmation_key(conf_token)
			confirmation_counter_key = await self._get_confirmation_counter_key(user_id)

			# Set to cache 'confirmation_key' with 'user_id'
			confirmation_data = {'user_id': user_id}
			await self._cache_confirmation(
				key=confirmation_key,
				data=confirmation_data,
				timeout=self.timeout_key,
			)

			cache = await self.get_connection()
			confirmation_counter_data = await cache.get(confirmation_counter_key)
			if confirmation_counter_data is None:
				# if 'confirmation_counter_key' is not in cache set 'count' to 1
				count = 1
			else:
				# else set 'count' to 'count' from 'confirmation_counter_key' + 1
				counter_value = json.loads(confirmation_counter_data)
				count = next(iter(counter_value.values())) + 1
				if count > self.max_attempts:
					raise ExceedLimitConfirmationCacheException()

			# Set to cache 'confirmation_counter_key' with 'confirmation_counter_value'
			confirmation_counter_data = {confirmation_key: count}
			await self._cache_confirmation(
				key=confirmation_counter_key,
				data=confirmation_counter_data,
				timeout=self.timeout_key,
			)

		except ExceedLimitConfirmationCacheException as e:
			raise
		except ConfirmationCacheException as e:
			pass
		except OperationCacheException as e:
			pass
