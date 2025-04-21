from typing import TypeVar, Any, Optional, Generic

from pydantic import BaseModel

from core.db import Base

M = TypeVar('M', bound=Base) # SQLAlchemy model
C = TypeVar('C', bound=BaseModel) # Create schema
U = TypeVar('U', bound=BaseModel) # Update schema


class RetrieveModelMixin(Generic[M]):
	async def retrieve(self, value: Any) -> Optional[M]:
		obj = await self.get_object(value)
		return obj


class ListModelMixin(Generic[M]):
	async def list(self) -> list[M]:
		objs = await self.get_objects()
		return objs


class CreateModelMixin(Generic[M, C]):
	async def create(self, data: C, return_attributes: Optional[list[str]] = None) -> M:
		obj = self.model(**data.model_dump())
		self.db.add(obj)
		await self.db.commit()

		if return_attributes:
			await self.db.refresh(obj, attribute_names=return_attributes)
		else:
			await self.db.refresh(obj)

		return obj


class UpdateModelMixin(Generic[M, U]):
	async def update(
			self,
			value: Any,
			data: U,
			return_attributes: Optional[list[str]] = None
	) -> Optional[M]:

		obj = await self.get_object(value)
		if not obj:
			return None

		for field, value in data.model_dump(exclude_unset=True).items():
			setattr(obj, field, value)

		await self.db.commit()

		if return_attributes:
			await self.db.refresh(obj, attribute_names=return_attributes)
		else:
			await self.db.refresh(obj)

		return obj


class DestroyModelMixin(Generic[M]):
	async def destroy(self, value: Any) -> bool:
		obj = await self.get_object(value)
		if not obj:
			return False

		await self.db.delete(obj)
		await self.db.commit()
		return True
