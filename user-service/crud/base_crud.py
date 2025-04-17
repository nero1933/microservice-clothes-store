from abc import ABC
from typing import Any, TypeVar, Generic, Optional, Type

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta

from db import Base

DB = TypeVar('DB', bound=DeclarativeMeta)
M = TypeVar('M', bound=Base) # SQLAlchemy model
C = TypeVar('C', bound=BaseModel) # Create schema
U = TypeVar('U', bound=BaseModel) # Update schema


# Create, Update, Delete --- return model? return_model=True?

class ModelCRUD(ABC, Generic[DB]):
	model: Type[M]

	def __init__(self, db: AsyncSession) -> None:
		self.db = db


class LookupModelCRUD(ModelCRUD[DB]):
	model: Type[M]
	lookup_field: str = 'id'

	def __init__(self, db: AsyncSession):
		super().__init__(db)
		self._validate_model_field()

	def _validate_model_field(self):
		if not hasattr(self.model, self.lookup_field):
			raise AttributeError(
				f"Model {self.model.__name__} has no field '{self.lookup_field}'"
			)


class SingleRetrieveModelCRUD(LookupModelCRUD):

	async def get_single_object(self, value) -> Optional[M]:
		stmt = select(self.model).where(getattr(self.model, self.lookup_field) == value)
		result = await self.db.execute(stmt)
		return result.scalar_one_or_none()


class MultipleRetrieveModelCRUD(ModelCRUD):

	async def get_multiple_objects(self) -> list[M]:
		stmt = select(self.model)
		result = await self.db.execute(stmt)
		return list(result.scalars().all())


class RetrieveModelCRUD(SingleRetrieveModelCRUD):
	async def retrieve(self, value: Any) -> Optional[M]:
		obj = await self.get_single_object(value)
		return obj if obj is not None else None


class ListModelCRUD(MultipleRetrieveModelCRUD):
	async def list(self) -> list[M]:
		objs = await self.get_multiple_objects()
		return objs


class CreateModelCRUD(ModelCRUD, Generic[C]):
	async def create(self, data: C) -> bool:
		if not isinstance(data, BaseModel):
			raise TypeError("Data must be a Pydantic BaseModel")

		obj = self.model(**data.model_dump())
		self.db.add(obj)
		await self.db.commit()
		return True


class UpdateModelCRUD(SingleRetrieveModelCRUD, Generic[U]):
	async def update(self, value: Any, data: U) -> bool:
		if not isinstance(data, BaseModel):
			raise TypeError("Data must be a Pydantic BaseModel")

		obj = await self.get_single_object(value)
		if not obj:
			return False

		for field, value in data.model_dump(exclude_unset=True).items():
			setattr(obj, field, value)

		await self.db.commit()
		return True


class DeleteModelCRUD(SingleRetrieveModelCRUD):
	async def delete(self, value: Any) -> bool:
		obj = await self.get_single_object(value)
		if not obj:
			return False

		await self.db.delete(obj)
		await self.db.commit()
		return True
