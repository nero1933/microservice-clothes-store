from typing import Optional, Type

from exceptions.custom_exceptions import HTTPCustomException


class ExceptionDocFactory:
	@staticmethod
	def from_exception(
			exc_cls: Type[HTTPCustomException],
			description: Optional[str] = None
	):
		detail = getattr(exc_cls, 'detail', 'Error')
		return {
			'description': description or detail,
			'content': {
				"application/json": {
					"example": {
						"detail": detail,
					}
				}
			}
		}

	@staticmethod
	def from_multiple_exceptions(
			exc_cls_tup: tuple[Type[HTTPCustomException], ...],
			description: str,
	):
		examples = {}
		for exc_cls in exc_cls_tup:
			detail = getattr(exc_cls, 'detail', 'Error')
			exc_cls_data = {
				'summary': detail,
				'value': {'detail': detail},
			}
			examples[exc_cls.__name__] = exc_cls_data

		return {
			'description': description,
			'content': {
				'application/json': {
					'examples': examples
				}
			}
		}
