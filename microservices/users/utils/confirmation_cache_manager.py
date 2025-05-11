import uuid

from core.cache.base_connection import BaseCacheConnection
from core.loggers import log
from exceptions.exceptions import TooManyRequestsException, CacheOperationException


class ConfirmationCacheManager(BaseCacheConnection):
	"""
	Manages confirmation keys and counter values in the cache.
	"""

	confirmation_key_template: str
	timeout_key: int

	confirmation_counter_template: str
	timeout_counter: int

	max_attempts: int

	@staticmethod
	async def create_confirmation_token() -> str:
		"""
		Returns a new confirmation token if one doesn't exist.
		"""
		return uuid.uuid4().hex

	@staticmethod
	async def create_confirmation_key(template: str, key_template: str) -> str:
		"""
		Creates a confirmation key from a template and key template.
		"""
		if not template or not key_template:
			raise ValueError("Template or key_template cannot be empty")

		try:
			return template.format(key_template=key_template)
		except KeyError as e:
			raise ValueError(f"Key template formatting failed: {e}")

	async def cache_confirmation_data(
			self,
			template: str,
			key_template: str,
			data: dict,
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
			confirmation_key = await self.create_confirmation_key(template, key_template)
			await cache.set(confirmation_key, data, timeout=timeout)
			return confirmation_key
		except Exception as e:
			raise CacheOperationException(f"Failed to set confirmation data in cache: {e}")

	async def cache_renewed_confirmation_key(self, counter_key: str, counter_value: dict) -> None:
		"""
		Renew the confirmation key in the cache by incrementing the counter value.
		This method deletes previous counter value and sets a new key and counter value
		to the same counter key.
		"""

		cache = await self.get_connection()
		try:
			confirmation_key = next(iter(counter_value.keys()))  # Get the old confirmation key
			if not await cache.exists(confirmation_key):  # If key doesn't exist in cache
				raise CacheOperationException(  # Raise error
					f"Confirmation key {confirmation_key} not found in cache."
				)
			counter = counter_value[confirmation_key] + 1  # Increment the counter

			# Get 'user_dict' and delete old confirmation_key
			user_dict: dict = await cache.get(confirmation_key)
			await cache.delete(confirmation_key)

			# Create new confirmation key
			new_confirmation_key = await self.create_confirmation_key(
				self.confirmation_key_template,
				await self.create_confirmation_token()
			)

			# Set new confirmation key to cache
			await cache.set(new_confirmation_key, user_dict, timeout=self.timeout_key)

			# Clear the old counter value
			counter_value.clear()
			# Set the new confirmation key with incremented counter
			counter_value.update({new_confirmation_key: counter})

			# Save the renewed counter data in the cache
			await cache.set(counter_key, counter_value, timeout=self.timeout_counter)

		except Exception as e:
			log.warning(f"Failed to cache new confirmation key: {e}")
			raise CacheOperationException

	async def cache_confirmation_key_with_counter(
			self,
			user_id: int
	) -> None:
		"""
		Cache the confirmation_key and the counter_key for a user.

		Value of confirmation_key is {'user_id': user_id}
		Value of counter_key is {confirmation_key: 1}
		"""

		try:
			confirmation_key = await self.cache_confirmation_data(
				self.confirmation_key_template,
				await self.create_confirmation_token(),
				{'user_id': user_id},
				self.timeout_key,
			)
			# Store the confirmation counter with an initial value of 1
			await self.cache_confirmation_data(
				self.confirmation_counter_template,
				str(user_id),
				{confirmation_key: 1},
				self.timeout_counter,
			)
		except Exception as e:
			error_message = f"Failed to cache new confirmation key: {e}"
			log.warning(error_message)
			raise CacheOperationException(error_message)

	async def handle_cache_confirmation(self, user_id: int) -> None:
		"""
		Handle the caching of the confirmation key and counter for a user.
		If the counter exceeds the max attempts, raise an exception.
		If the counter does not exist, cache a new confirmation key with counter 1.
		"""

		cache = await self.get_connection()
		counter_key = await self.create_confirmation_key(
			self.confirmation_counter_template, str(user_id)
		)
		try:
			counter_value = await cache.get(counter_key, None)
			if counter_value is None:
				# If no counter exists, create a new confirmation key and counter 1
				await self.cache_confirmation_key_with_counter(user_id)
				return None

			# counter = list(counter_value.values())[0]
			counter = next(iter(counter_value.values()))
			if counter >= self.max_attempts:
				# If the max attempts are reached, raise an error
				raise TooManyRequestsException

			# If counter is not exceeded, renew the confirmation key and increment the counter
			await self.cache_renewed_confirmation_key(counter_key, counter_value)
		except Exception as e:
			error_message = f"Error handling cache confirmation for user {user_id}: {e}"
			log.error(error_message)
			raise CacheOperationException(error_message)


