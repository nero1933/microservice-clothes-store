from typing import Any, TypeVar, Generic, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import Base

M = TypeVar('M', bound=Base) # SQLAlchemy model
C = TypeVar('C', bound=BaseModel) # Create schema
U = TypeVar('U', bound=BaseModel) # Update schema


class ModelCRUD(Generic[M]):
	model: type[M]

	def __init__(self, db: AsyncSession):
		self.db = db


class RetrieveModelCRUD(ModelCRUD[M]):
	async def retrieve(self, pk: UUID | int) -> Optional[M]:
		stmt = select(self.model).where(self.model.id == pk)
		result = await self.db.execute(stmt)
		return result.scalar_one_or_none()


class ListModelCRUD(ModelCRUD[M]):
	async def list(self) -> list[M]:
		stmt = select(self.model)
		result = await self.db.execute(stmt)
		return list(result.scalars().all())


class CreateModelCRUD(ModelCRUD[M], Generic[M, C]):
	async def create(self, data: C) -> M:
		if not isinstance(data, BaseModel):
			raise TypeError("Data must be a Pydantic BaseModel")

		obj = self.model(**data.model_dump())
		self.db.add(obj)
		await self.db.commit()
		await self.db.refresh(obj)
		return obj


class UpdateModelCRUD(ModelCRUD[M], Generic[M, U]):
	async def update(self, pk: UUID | int, data: U) -> Optional[M]:
		if not isinstance(data, BaseModel):
			raise TypeError("Data must be a Pydantic BaseModel")

		stmt = select(self.model).where(self.model.id == pk)
		result = await self.db.execute(stmt)
		obj = result.scalar_one_or_none()
		if not obj:
			return None

		for field, value in data.model_dump(exclude_unset=True).items():
			setattr(obj, field, value)

		await self.db.commit()
		await self.db.refresh(obj)
		return obj


class DeleteModelCRUD(ModelCRUD[M]):
	async def delete(self, pk: Any) -> bool:
		stmt = select(self.model).where(self.model.id == pk)
		result = await self.db.execute(stmt)
		obj = result.scalar_one_or_none()
		if not obj:
			return False

		await self.db.delete(obj)
		await self.db.commit()
		return True
