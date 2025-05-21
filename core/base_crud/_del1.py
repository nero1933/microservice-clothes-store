from abc import ABC
from typing import TypeVar, Generic, Type, Sequence, Any

from pydantic import BaseModel
from sqlalchemy import Select, Update, Delete, RowMapping, select, and_, Insert, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Base
from core.loggers import log
from exceptions import RecordNotUniqueCRUDException

M = TypeVar('M', bound=Base)  # SQLAlchemy model
S = TypeVar('S', bound=BaseModel)  # Pydantic schema


class AbstractCRUD(Generic[M, S], ABC):
	model: Type[M] | None = None

	def __init__(self, db: AsyncSession) -> None:
		self._validate_model_attr()
		self.db = db

	def _validate_model_attr(self):
		if not self.model:
			raise AttributeError('Model cannot be None')


class AbstractSingleLookupCRUD(AbstractCRUD[M, S], ABC):
	lookup_field: str = 'id'

	def __init__(self, db: AsyncSession) -> None:
		self._validate_model_lookup_field()
		super().__init__(db)

	def _validate_model_lookup_field(self) -> None:
		if not hasattr(self.model, self.lookup_field):
			raise AttributeError(
				f"Model: <{self.model.__name__}> has no field: <{self.lookup_field}>"
			)

	def _get_stmt_with_lookup_filter(self, stmt, value) -> Select | Update | Delete:
		return stmt.where(getattr(self.model, self.lookup_field) == value)


class AbstractMultipleSingleLookupCRUD(AbstractSingleLookupCRUD[M, S], ABC):

	def _validate_model_lookup_field(self) -> None:
		if self.lookup_field is None:
			return

		if not hasattr(self.model, self.lookup_field):
			raise AttributeError(
				f"Model: <{self.model.__name__}> has no field: <{self.lookup_field}>"
			)

	def _get_filters(self) -> tuple | None:
		return None


class AbstractSchemaCRUD(AbstractCRUD[M, S], ABC):
	schema: Type[S] | None = None

	def __init__(self, db: AsyncSession) -> None:
		self._validate_schema_attr()
		super().__init__(db)

	def _validate_schema_attr(self):
		if not self.schema:
			raise AttributeError('Schema cannot be None')


class AbstractReturnFieldsCRUD(AbstractSchemaCRUD[M, S], ABC):

	def _get_fields(self) -> tuple:
		schema_fields = self.schema.model_fields.keys()
		return tuple(getattr(self.model, field) for field in schema_fields)


class AbstractListCRUD(AbstractReturnFieldsCRUD[M, S],
					   AbstractMultipleSingleLookupCRUD[M, S],
					   ABC):

	async def get_list(self, lookup_value: Any = None) -> list[S]:
		rows = await self._execute_statement(lookup_value)
		return [self.schema(**row) for row in rows]

	async def _execute_statement(self, lookup_value: Any) -> Sequence[RowMapping]:
		stmt = self._get_statement_for_list(lookup_value)
		result = await self.db.execute(stmt)
		return result.mappings().all()

	def _get_statement_for_list(self, lookup_value: Any = None) -> Select:
		fields = self._get_fields()
		stmt = select(*fields)
		if lookup_value:
			stmt = self._get_stmt_with_lookup_filter(stmt, lookup_value)

		if filters := self._get_filters():
			stmt = stmt.where(and_(*filters))

		return stmt


class AbstractSingleRetrieverCRUD(AbstractSingleLookupCRUD[M, S], AbstractReturnFieldsCRUD[M, S], ABC):

	async def retrieve(self, lookup_value: Any) -> Type[S] | None:
		row = await self._execute_statement(lookup_value)
		return self.schema(**row) if row else None

	def _get_statement_for_retrieve(self, value) -> Select:
		fields = self._get_fields()
		stmt = select(*fields)
		return self._get_stmt_with_lookup_filter(stmt, value)

	async def _execute_statement(self, lookup_value: Any) -> RowMapping | None:
		stmt = self._get_statement_for_retrieve(lookup_value)
		result = await self.db.execute(stmt)
		rows = result.mappings().all()

		if not rows:
			return None

		if len(rows) > 1:
			error_message = \
				(f"More than one record found "
				 f"for field: <{self.lookup_field}>, "
				 f"with value: <{lookup_value}>, "
				 f"in model: <{self.model.__name__}>")
			log.error(error_message)
			raise RecordNotUniqueCRUDException(error_message)

		return rows[0]


class AbstractCreateCRUD(AbstractReturnFieldsCRUD[M, S], ABC):

	async def create(self, schema_obj: S) -> Type[S]:
		stmt = await self._get_statement_for_create(schema_obj)
		result = await self.db.execute(stmt)
		await self.db.commit()
		row = result.mappings().one()
		return self.schema(**row) if row else None

	async def _get_statement_for_create(self, schema_obj: S) -> Insert:
		fields = self._get_fields()
		return insert(self.model).values(schema_obj.model_dump()).returning(*fields)


class AbstractSingleUpdateCRUD(AbstractSingleLookupCRUD[M, S], AbstractReturnFieldsCRUD[M, S], ABC):

	async def update(self, value: Any, schema_obj: S) -> Type[S] | None:
		stmt = self._get_statement_for_update(value, schema_obj)
		result = await self.db.execute(stmt)
		await self.db.commit()
		row = result.mappings().one_or_none()
		return self.schema(**row) if row else None

	def _get_statement_for_update(self, value: Any, schema_obj: S) -> Update:
		fields = self._get_fields()
		stmt = update(self.model)
		stmt = self._get_stmt_with_lookup_filter(stmt, value)
		return stmt.values(schema_obj.model_dump()).returning(*fields)


class AbstractSingleDeleteCRUD(AbstractSingleLookupCRUD[M, S], ABC):

	async def delete(self, value: Any) -> bool:
		stmt = await self._get_statement_for_delete(value)
		result = await self.db.execute(stmt)
		await self.db.commit()
		return result.rowcount() > 0

	async def _get_statement_for_delete(self, value: Any) -> Delete:
		stmt = delete(self.model)
		return self._get_stmt_with_lookup_filter(stmt, value)
