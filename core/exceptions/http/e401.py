from fastapi import status

from core.exceptions.custom_http_exeption import CustomHTTPException


class CredentialsHTTPException(CustomHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Invalid credentials"
	headers = {"WWW-Authenticate": "Bearer"}
