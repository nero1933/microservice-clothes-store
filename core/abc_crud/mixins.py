from abc import ABC
from typing import TypeVar, Any, Optional, Generic

from pydantic import BaseModel

from core.db import Base

S = TypeVar('S', bound=BaseModel) # Pydantic schema
C = TypeVar('C', bound=BaseModel) # Create schema
U = TypeVar('U', bound=BaseModel) # Update schema


class RetrieveModelMixin(Generic[S]):
	async def retrieve(self, email: str) -> Optional[S] | None:
		obj = await self.get_object(email, orm_model=False)
		if obj:
			obj_dict = dict(obj._mapping)
			return self.schema(**obj_dict)

		return None

class ListModelMixin(Generic[S]):
	async def list(self) -> list[S]:
		objs = await self.get_objects()
		return objs


class CreateModelMixin(Generic[S, C]):
	async def create(self, data: C, return_attributes: Optional[list[str]] = None) -> S:
		obj = self.model(**data.model_dump())
		self.db.add(obj)
		await self.db.commit()

		if return_attributes:
			await self.db.refresh(obj, attribute_names=return_attributes)
		else:
			await self.db.refresh(obj)

		return obj


class UpdateModelMixin(Generic[S, U]):
	async def update(
			self,
			value: Any,
			data: U,
			return_attributes: Optional[list[str]] = None
	) -> Optional[S]:

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


class DestroyModelMixin(Generic[S]):
	async def destroy(self, value: Any) -> bool:
		obj = await self.get_object(value)
		if not obj:
			return False

		await self.db.delete(obj)
		await self.db.commit()
		return True
