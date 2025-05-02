from fastapi import status

from core.exceptions.custom_http_exeption import CustomHTTPException


class BadRequestHTTPException(CustomHTTPException):
	status_code = status.HTTP_400_BAD_REQUEST
	detail = "Bad request"
