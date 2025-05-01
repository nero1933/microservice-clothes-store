from fastapi import status

from core.exceptions.custom_http_exeption import CustomHTTPException


class CredentialsHTTPException(CustomHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Invalid credentials"
	headers = {"WWW-Authenticate": "Bearer"}


class ExpiredSignatureHTTPException(CustomHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Token has expired"
	headers = {"WWW-Authenticate": "Bearer"}


class RefreshTokenMissingHTTPException(CustomHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Refresh token not found"
	headers = {"WWW-Authenticate": "Bearer"}


class NotAuthenticatedHTTPException(CustomHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Not authenticated"
	headers = {"WWW-Authenticate": "Bearer"}
