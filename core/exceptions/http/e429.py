from fastapi import status

from core.exceptions.custom_http_exeption import CustomHTTPException


class TooManyRequestsHTTPException(CustomHTTPException):
	status_code = status.HTTP_429_TOO_MANY_REQUESTS
	detail = "Too many requests, please try again later"
