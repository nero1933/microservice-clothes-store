class DuplicateEmailException(Exception):
	""" Raised when an email already exists in the db """
	pass


class TooManyRequestsException(Exception):
	""" Raised when too many requests are sent """
	pass


class CacheOperationException(Exception):
	""" Raised when a cache operation fails """
	pass
