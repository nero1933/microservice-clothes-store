from abc import ABC
from typing import TypeVar, Generic, Optional, Type

from pydantic import BaseModel
from sqlalchemy import select, Row, Select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Base
from core.loggers import log

M = TypeVar('M', bound=Base) # SQLAlchemy model
S = TypeVar('S', bound=BaseModel) # Pydantic schema


class BaseCRUD(ABC, Generic[M]):
	model: Type[M]
	schema: Type[S]
	lookup_field: str = 'id'
	fields: tuple[str] = tuple()

	def __init__(self, db: AsyncSession) -> None:
		self.db = db
		self._validate_model_field()

	def _validate_model_field(self) -> None:
		if not hasattr(self.model, self.lookup_field):
			raise AttributeError(
				f"Model {self.model.__name__} has no field '{self.lookup_field}'"
			)

	async def get_statement(self, value, orm_model=True) -> Select:
		"""
		Generates an SQL query for selecting data from the database.

		Depending on the `orm_model` parameter, the method either creates a query
		for getting an entire model or for specific row.

		Parameters:
		----------
		value : str
		    The value used for filtering. Typically, this is the value for the lookup field (e.g., email).

		orm_model : bool, default True
		    Use True if you need to get SQLAlchemy ORM model
		    	(ex. for creating/deleting)
		    Use False if you need to get SQLAlchemy ROW, and don't forget to set 'fields'
		    	(ex. for retrieving)

		Returns:
		-------
		Select
		    A SQLAlchemy `Select` query object, which can be executed to fetch the data.
		"""

		if orm_model:
			fields = (self.model, )  # If 'orm_model' is True use self.model to select model
		else:
			if len(self.fields) == 0:
				error_message = ("When 'orm_model' is False, you are trying "
								 "to get certain fields, but 'fields' is empty")
				log.error(error_message)
				raise ValueError(error_message)
			fields = [getattr(self.model, field) for field in self.fields]

		return select(*fields).where(getattr(self.model, self.lookup_field) == value)


	async def get_object(self, value, orm_model=True) -> Row | None:
		stmt = await self.get_statement(value, orm_model)
		result = await self.db.execute(stmt)
		if orm_model:
			return result.scalar_one_or_none()

		rows = result.all()
		if not rows:
			return None

		if len(rows) > 1:
			error_message = f"More than one record found for {value}"
			log.info(error_message)
			raise ValueError(error_message)

		return rows[0]

	async def get_objects(self) -> list[M]:
		stmt = select(self.model)
		result = await self.db.execute(stmt)
		return list(result.scalars().all())

