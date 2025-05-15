from fastapi import status

from core.exceptions.custom_http_exeption import CustomHTTPException


class EmailExistsHTTPException(CustomHTTPException):
	status_code = status.HTTP_400_BAD_REQUEST
	detail = "Email already exists"

class ResetPasswordHTTPException(CustomHTTPException):
	status_code = status.HTTP_400_BAD_REQUEST
	detail = "New password matches old one"
