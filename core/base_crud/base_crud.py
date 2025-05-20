# from abc import ABC
# from typing import TypeVar, Generic, Optional, Type, Sequence
#
# from pydantic import BaseModel
# from sqlalchemy import select, Row, Select, update, Update, RowMapping
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from core.base_crud import AbstractCRUD
# from core.db import Base
# from core.loggers import log
# from exceptions import RecordNotUniqueCRUDException
#
# M = TypeVar('M', bound=Base) # SQLAlchemy model
# S = TypeVar('S', bound=BaseModel) # Pydantic schema


# class BaseCRUD(ABC, Generic[M, S]):
# 	model: Type[M]
# 	schema: Type[S] | None = None
# 	lookup_field: str = 'id'
# 	_obj: M | Row | None = None
#
# 	def __init__(self, db: AsyncSession) -> None:
# 		self.db = db
# 		self._validate_model_field()
#
# 	def _validate_model_field(self) -> None:
# 		if not hasattr(self.model, self.lookup_field):
# 			raise AttributeError(
# 				f"Model {self.model.__name__} has no field '{self.lookup_field}'"
# 			)
#
# 	async def get_fields_from_schema(self):
# 		return tuple(self.schema.model_fields.keys())
#
# 	async def get_statement(self, value) -> Select:
# 		"""
# 		Generate a SELECT statement for the given value using the lookup field.
#
# 		- If `self.schema` is None, it selects the entire ORM model.
# 		- If `self.schema` is provided, it selects only fields defined in the schema.
# 		"""
# 		if not self.schema:
# 			fields = (self.model, )  # If 'self.schema' is not defined -- get orm model
# 		else:  # If 'self.schema' is defined -- get schemas fields
# 			schema_fields = await self.get_fields_from_schema()
# 			fields = [getattr(self.model, field) for field in schema_fields]
#
# 		return select(*fields).where(getattr(self.model, self.lookup_field) == value)
#
# 	async def get_statement_for_update(self, value) -> Update:
# 		return update(self.model). \
# 			where(getattr(self.model, self.lookup_field) == value) \
# 			.values(hashed_password='1')
#
#
# 	async def _get_orm_object(self, value) -> M | None:
# 		stmt = await self.get_statement(value)
# 		result = await self.db.execute(stmt)
# 		return result.scalar_one_or_none()
#
# 	async def _get_schema_object(self, value) -> Row | None:
# 		stmt = await self.get_statement(value)
# 		result = await self.db.execute(stmt)
# 		rows = result.all()
#
# 		if not rows:
# 			return None
#
# 		if len(rows) > 1:
# 			error_message = f"More than one record found for {value} in {self.model.__name__}"
# 			log.error(error_message)
# 			raise ValueError(error_message)
#
# 		return rows[0]
#
# 	async def get_object(self, value) -> M | Row | None:
# 		if getattr(self, '_obj', None) is not None:
# 			return self._obj
#
# 		if getattr(self, 'schema', None) is None:
# 			self._obj = await self._get_orm_object(value)
# 		else:
# 			self._obj = await self._get_schema_object(value)
#
# 		return self._obj
#
# 	async def get_objects(self) -> list[M]:
# 		stmt = select(self.model)
# 		result = await self.db.execute(stmt)
# 		return list(result.scalars().all())

# ------------------------------------------------------------------------------------------------

# class AbstractReadCRUD(AbstractCRUD[M, S], ABC):
#
# 	async def _get_fields(self) -> list:
# 		schema_fields = tuple(self.schema.model_fields.keys())
# 		return [getattr(self.model, field) for field in schema_fields]
#
# 	async def _get_statement(self, value) -> Select:
# 		fields = await self._get_fields()
# 		if self.lookup_field == '__all__':
# 			return select(*fields)
#
# 		return select(*fields).where(getattr(self.model, self.lookup_field) == value)
#
# 	async def _get_rows(self, value) -> Sequence[RowMapping]:
# 		if self._db_data is None:
# 			stmt = await self._get_statement(value)
# 			result = await self.db.execute(stmt)
# 			self._db_data = result.mappings().all()
#
# 		return self._db_data
#
#
# class AbstractListCRUD(AbstractReadCRUD[M, S], ABC):
#
# 	async def get_list(self, value=None) -> list[S]:
# 		rows = await self._get_rows(value)
# 		return [self.schema(**row) for row in rows]
#
#
# class AbstractRetrieverCRUD(AbstractReadCRUD[M, S], ABC):
# 	lookup_field: str = 'id'
#
# 	def __init__(self, db: AsyncSession) -> None:
# 		self.__validate_lookup_field()
# 		super().__init__(db)
#
# 	def __validate_lookup_field(self) -> None:
# 		if self.lookup_field == '__all__':
# 			raise AttributeError('"lookup_field" cannot be "__all__"')
#
# 	async def retrieve(self, value) -> Type[S] | None:
# 		row = await self._get_row(value)
# 		return self.schema(**row) if row else None
#
# 	async def _get_row(self, value) -> RowMapping | None:
# 		rows = await self._get_rows(value)
# 		if not rows:
# 			return None
#
# 		if len(rows) > 1:
# 			error_message = \
# 				(f"More than one record found "
# 				 f"for field: <{self.lookup_field}>, "
# 				 f"with value: <{value}>, "
# 				 f"in model: <{self.model.__name__}>")
# 			log.error(error_message)
# 			raise RecordNotUniqueCRUDException(error_message)
#
# 		return rows[0]
