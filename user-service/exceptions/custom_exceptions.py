from fastapi import HTTPException, status


class HTTPCustomException(HTTPException):
	detail: str


class EmailExistsException(HTTPCustomException):
	detail = "User with this email already exists"

	def __init__(self):
		super().__init__(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=self.detail,
			headers={"WWW-Authenticate": "Bearer"},
		)


class CredentialsException(HTTPCustomException):
	detail = "Invalid credentials"

	def __init__(self):
		super().__init__(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=self.detail,
			headers={"WWW-Authenticate": "Bearer"},
		)


class RefreshTokenMissingException(HTTPCustomException):
	detail = "Refresh token not found"

	def __init__(self):
		super().__init__(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=self.detail,
			headers={"WWW-Authenticate": "Bearer"},
		)


class NotAuthenticatedException(HTTPCustomException):
	detail = "Not authenticated"

	def __init__(self):
		super().__init__(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=self.detail,
			headers={"WWW-Authenticate": "Bearer"},
		)


class InactiveUserException(HTTPCustomException):
	detail = "Inactive user"

	def __init__(self):
		super().__init__(
			status_code=status.HTTP_403_FORBIDDEN,
			detail=self.detail
		)
