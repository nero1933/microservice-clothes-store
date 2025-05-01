from abc import ABC

from fastapi import HTTPException


class CustomHTTPException(HTTPException, ABC):
	def __init__(self):
		if not hasattr(self, 'detail'):
			raise TypeError("Subclasses must define 'detail' attribute")
		if not hasattr(self, 'status_code'):
			raise TypeError("Subclasses must define 'status_code' attribute")

		headers = getattr(self, 'headers', None)
		super().__init__(status_code=self.status_code, detail=self.detail, headers=headers)
