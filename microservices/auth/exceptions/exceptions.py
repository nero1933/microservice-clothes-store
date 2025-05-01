class DuplicateJTIException(Exception):
	""" Raised when a JTI already exists in the blacklist """
	pass


class JWTTokenValidationException(Exception):
	""" Raised when a JWT token token is invalid """
	pass


class MissionAccessTokenException(Exception):
	""" Raised when a JWT token is missing """
	pass