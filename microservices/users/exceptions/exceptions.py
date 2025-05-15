class DuplicateEmailException(Exception):
	""" Raised when an email already exists in the db """
	pass


class TooManyRequestsException(Exception):
	""" Raised when too many requests are sent """
	pass


class UserNotFoundException(Exception):
	""" Raised when a user doesn't exist """
	pass


class PasswordUnchangedException(Exception):
	""" Raised when the new password is the same as the current password """
	pass


# ---------- STARTS CacheException ----------


class OperationCacheException(Exception):
	""" Raised when a cache operation fails """
	pass


class ConfirmationKeyExpiredCacheException(Exception):
	""" Raised when the confirmation key is missing or expired """
	pass


class ConfirmationCounterKeyExpiredCacheException(Exception):
	""" Raised when the confirmation counter key is missing or expired """
	pass


class InvalidConfirmationKeyCacheException(Exception):
	""" Raised when the confirmation key is invalid """
	pass


class ValidationConfirmationCacheException(Exception):
	""" Raised when the confirmation validation fails """
	pass

# ---------- STOPS CacheException ----------
