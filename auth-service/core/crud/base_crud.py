from abc import ABC
from typing import TypeVar, Generic, Optional, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Base

M = TypeVar('M', bound=Base) # SQLAlchemy model


class BaseCRUD(ABC, Generic[M]):
	model: Type[M]
	lookup_field: str = 'id'

	def __init__(self, db: AsyncSession) -> None:
		self.db = db
		self._validate_model_field()

	def _validate_model_field(self) -> None:
		if not hasattr(self.model, self.lookup_field):
			raise AttributeError(
				f"Model {self.model.__name__} has no field '{self.lookup_field}'"
			)

	async def get_object(self, value) -> Optional[M]:
		stmt = select(self.model).where(getattr(self.model, self.lookup_field) == value)
		result = await self.db.execute(stmt)
		return result.scalar_one_or_none()

	async def get_objects(self) -> list[M]:
		stmt = select(self.model)
		result = await self.db.execute(stmt)
		return list(result.scalars().all())

