from typing import Any, Sequence
from sqlalchemy import Select, Insert, Update, Delete, select, RowMapping, insert, update, delete

from .base import SchemaCRUD, M, RS, LookupCRUD, FilterCRUD, ReturningCRUD, CS, \
	ValueCreateCRUD, ValueUpdateCRUD, US


class RetrieverCRUD(SchemaCRUD[M, RS], LookupCRUD[M]):

	def _get_stmt(self) -> Select:
		fields = self._get_schema_fields()
		return select(*fields)

	async def _execute_stmt(self, stmt: Select) -> RowMapping:
		result = await self.db.execute(stmt)
		return result.mappings().one_or_none()

	async def retrieve(self, lookup_value: Any) -> RS | None:
		stmt = self._get_stmt()
		stmt = self._apply_lookup(stmt, lookup_value)
		row = await self._execute_stmt(stmt)
		return self.schema(**row)


class ListCRUD(SchemaCRUD[M, RS], LookupCRUD[M], FilterCRUD[M]):

	def _get_stmt(self) -> Select:
		fields = self._get_schema_fields()
		return select(*fields)

	async def _execute_stmt(self, stmt: Select) -> Sequence[RowMapping]:
		result = await self.db.execute(stmt)
		return result.mappings().all()

	async def get_list(self, lookup_value: Any) -> list[RS]:
		stmt = self._get_stmt()
		stmt = self._apply_lookup(stmt, lookup_value)
		stmt = self._apply_filters(stmt)
		rows = await self._execute_stmt(stmt)
		return [self.schema(**row) for row in rows]


class CreatorCRUD(ReturningCRUD[M, RS], ValueCreateCRUD[M, CS]):

	def _get_stmt(self) -> Insert:
		return insert(self.model)

	async def _execute_stmt(self, stmt: Insert) -> Sequence[RowMapping]:
		result = await self.db.execute(stmt)
		return result.mappings().all()

	async def create(self, schema_objs: CS | list[CS]) -> RS | list[RS]:
		stmt = self._get_stmt()
		stmt = self._apply_values(stmt, schema_objs)
		stmt = self._apply_returning(stmt)
		rows = await self._execute_stmt(stmt)
		if len(rows) == 1:
			return self.schema(**rows[0])

		return [self.schema(**row) for row in rows]


class UpdaterCRUD(ReturningCRUD[M, RS], LookupCRUD[M], FilterCRUD[M], ValueUpdateCRUD[M, US]):

	def _get_stmt(self) -> Update:
		return update(self.model)

	async def _execute_stmt(self, stmt: Update) -> Sequence[RowMapping]:
		result = await self.db.execute(stmt)
		return result.mappings().all()

	async def update(self, lookup_value: str, schema_objs: CS | list[CS]) -> RS | list[RS]:
		stmt = self._get_stmt()
		stmt = self._apply_lookup(stmt, lookup_value)
		stmt = self._apply_filters(stmt)
		stmt = self._apply_values(stmt, schema_objs)
		stmt = self._apply_returning(stmt)
		rows = await self._execute_stmt(stmt)
		if len(rows) == 1:
			return self.schema(**rows[0])

		return [self.schema(**row) for row in rows]


class DeleterCRUD(LookupCRUD[M], FilterCRUD[M]):

	def _get_stmt(self) -> Delete:
		return delete(self.model)

	async def _execute_stmt(self, stmt: Delete) -> int:
		result = await self.db.execute(stmt)
		return result.rowcount

	async def destroy(self, lookup_value: str) -> int:
		stmt = self._get_stmt()
		stmt = self._apply_lookup(stmt, lookup_value)
		stmt = self._apply_filters(stmt)
		return await self._execute_stmt(stmt)
