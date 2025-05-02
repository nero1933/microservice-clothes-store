from fastapi import status

from core.exceptions.custom_http_exeption import CustomHTTPException


class NotFoundHTTPException(CustomHTTPException):
	status_code = status.HTTP_404_NOT_FOUND
	detail = "Not found"