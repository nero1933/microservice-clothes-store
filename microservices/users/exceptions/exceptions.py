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


class CacheException(Exception):
	""" Raised when a caching fails """
	pass


class OperationCacheException(CacheException):
	""" Raised when a cache operation fails """
	pass


class ConfirmationCacheException(CacheException):
	""" Raised when a cache operation for configuration fails """
	pass


class ConfirmationKeyExpiredCacheException(ConfirmationCacheException):
	""" Raised when the confirmation key is missing or expired """
	pass


class ConfirmationCounterKeyExpiredCacheException(ConfirmationCacheException):
	""" Raised when the confirmation counter key is missing or expired """
	pass


class InvalidConfirmationKeyCacheException(ConfirmationCacheException):
	""" Raised when the confirmation key is invalid """
	pass


class ValidationConfirmationCacheException(ConfirmationCacheException):
	""" Raised when the confirmation validation fails """
	pass


class ExceedLimitConfirmationCacheException(ConfirmationCacheException):
	""" Raised when the limit of consumptions is exceeded """
	pass


# ---------- STOPS CacheException ----------

# ---------- STARTS CRUDException ----------


class CRUDException(Exception):
	pass

class RecordNotUniqueCRUDException(CRUDException):
	pass

# ---------- STOPS CRUDException ----------