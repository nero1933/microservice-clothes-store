from abc import ABC
from typing import TypeVar, Generic, Optional, Type

from pydantic import BaseModel
from sqlalchemy import select, Row, Select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Base
from core.loggers import log

M = TypeVar('M', bound=Base) # SQLAlchemy model
S = TypeVar('S', bound=BaseModel) # Pydantic schema


class BaseCRUD(ABC, Generic[M, S]):
	model: Type[M]
	schema: Type[S]
	lookup_field: str = 'id'

	def __init__(self, db: AsyncSession) -> None:
		self.db = db
		self._validate_model_field()

	def _validate_model_field(self) -> None:
		if not hasattr(self.model, self.lookup_field):
			raise AttributeError(
				f"Model {self.model.__name__} has no field '{self.lookup_field}'"
			)

	async def get_fields_from_schema(self):
		return tuple(self.schema.model_fields.keys())

	async def get_statement(self, value) -> Select:
		"""
		Generate a SELECT statement for the given value using the lookup field.

		- If `self.schema` is None, it selects the entire ORM model.
		- If `self.schema` is provided, it selects only fields defined in the schema.
		"""
		if not self.schema:
			fields = (self.model, )  # If 'self.schema' is not defined -- get orm model
		else:  # If 'self.schema' is defined -- get schemas fields
			schema_fields = await self.get_fields_from_schema()
			fields = [getattr(self.model, field) for field in schema_fields]

		return select(*fields).where(getattr(self.model, self.lookup_field) == value)

	async def get_object(self, value) -> M | Row | None:
		stmt = await self.get_statement(value)
		result = await self.db.execute(stmt)
		if self.schema is None:  # If 'self.schema' is not defined -- get orm model
			return result.scalar_one_or_none()

		# If 'self.schema' is defined -- get schemas fields
		rows = result.all()
		if not rows:
			return None

		if len(rows) > 1:
			error_message = f"More than one record found for {value} in {self.model.__name__}"
			log.error(error_message)
			raise ValueError(error_message)

		return rows[0]

	async def get_objects(self) -> list[M]:
		stmt = select(self.model)
		result = await self.db.execute(stmt)
		return list(result.scalars().all())
