from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type, Sequence, Any

from pydantic import BaseModel
from sqlalchemy import Select, Update, Delete, RowMapping, select, and_, Insert, insert, update, delete, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Base
from core.loggers import log
from exceptions import RecordNotUniqueCRUDException

M = TypeVar('M', bound=Base)  # SQLAlchemy model
S = TypeVar('S', bound=BaseModel)  # Pydantic schema
RS = TypeVar('RS', bound=BaseModel)  # Pydantic return schema
CS = TypeVar('CS', bound=BaseModel)  # Pydantic create schema
US = TypeVar('US', bound=BaseModel)  # Pydantic update schema


class BaseCRUD(Generic[M], ABC):
	model: Type[M] | None = None

	def __init__(self, db: AsyncSession) -> None:
		self.__validate_attr_model()
		self.db = db

	def __validate_attr_model(self):
		if not self.model:
			raise AttributeError('Model cannot be None')

	@abstractmethod
	def _get_stmt(self) -> Select | Insert | Update | Delete:
		raise NotImplementedError

	@abstractmethod
	async def _execute_stmt(self, stmt) -> Any:
		raise NotImplementedError


class SchemaCRUD(BaseCRUD[M], Generic[M, RS], ABC):
	schema: Type[RS] | None = None

	def __init__(self, db: AsyncSession) -> None:
		self.__validate_attr_schema()
		super().__init__(db)

	def __validate_attr_schema(self):
		if not self.schema:
			raise AttributeError('Schema cannot be None')

	def _get_schema_fields(self) -> tuple:
		schema_fields = self.schema.model_fields.keys()
		return tuple(getattr(self.model, field) for field in schema_fields)


class ReturningCRUD(SchemaCRUD[M, RS], ABC):

	def _apply_returning(self, stmt) -> Insert | Update:
		returning_fields = self._get_schema_fields()
		return stmt.returning(*returning_fields)


class LookupCRUD(BaseCRUD[M], ABC):
	lookup_field: str = 'id'

	def __init__(self, db: AsyncSession) -> None:
		self.__validate_models_lookup_field()
		super().__init__(db)

	def __validate_models_lookup_field(self) -> None:
		if self.lookup_field is None:
			raise AttributeError(
				f"'lookup_field' cannot be None"
			)

		if not hasattr(self.model, self.lookup_field):
			raise AttributeError(
				f"Model: <{self.model.__name__}> has no field: <{self.lookup_field}>"
			)

	def _apply_lookup(self, stmt, lookup_value) -> Select | Update | Delete:
		return stmt.where(getattr(self.model, self.lookup_field) == lookup_value)


class FilterCRUD(BaseCRUD[M], ABC):
	def _apply_filters(self, stmt) -> Select | Update | Delete:
		return stmt


class ValueCRUD(BaseCRUD[M], Generic[M, S], ABC):

	def _apply_values(self, stmt: Insert | Update, schema_obj: S) -> Insert | Update:
		values = self._get_values(schema_obj)
		return stmt.values(**values)

	def _get_values(self, schema_obj: S) -> dict:
		return schema_obj.model_dump()


class ValueCreateCRUD(ValueCRUD[M, CS], Generic[M, CS], ABC):

	def _apply_values(self, stmt: Insert, schema_objs: CS | list[CS]) -> Insert | Update:
		values = self._get_values(schema_objs)
		if isinstance(values, list):
			return stmt.values(values)

		return stmt.values(**values)

	def _get_values(self, schema_objs: CS | list[CS]) -> list[dict]:
		if not isinstance(schema_objs, list):
			schema_objs = (schema_objs,)

		return [obj.model_dump() for obj in schema_objs]


class ValueUpdateCRUD(ValueCRUD[M, US], Generic[M, US], ABC):
	partial_update: bool = False

	def _get_values(self, schema_obj: US) -> dict:
		return schema_obj.model_dump(exclude_unset=self.partial_update)


# class ValueCRUD(BaseCRUD[M], Generic[M, S], ABC):
#
# 	def _apply_values(self, stmt: Insert | Update, schema_objs: S | list[S]) -> Insert | Update:
# 		values = self._get_values(schema_objs)
# 		if isinstance(values, list):
# 			return stmt.values(values)
#
# 		return stmt.values(**values)
#
# 	def _get_values(self, schema_objs: S | list[S]) -> dict | list[dict]:
# 		pass
#
#
# class ValueCreateCRUD(ValueCRUD[M, CS], Generic[M, CS], ABC):
#
# 	def _get_values(self, schema_objs: S | list[S]) -> list[dict]:
# 		if not isinstance(schema_objs, list):
# 			schema_objs = (schema_objs,)
#
# 		return [obj.model_dump() for obj in schema_objs]
#
#
# class ValueUpdateCRUD(ValueCRUD[M, US], Generic[M, US], ABC):
# 	partial_update: bool = False
#
# 	def _apply_values(self, stmt: Update, schema_obj: US) -> Update:
# 		values = self._get_values(schema_obj)
# 		return stmt.values(**values)
#
# 	def _get_values(self, schema_obj: US) -> dict:
# 		return schema_obj.model_dump(exclude_unset=self.partial_update)
