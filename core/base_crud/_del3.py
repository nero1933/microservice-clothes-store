from typing import TypeVar, Any, Optional, Generic

from pydantic import BaseModel
from sqlalchemy import Row

from core.db import Base

M = TypeVar("M", bound=Base)
S = TypeVar('S', bound=BaseModel) # Pydantic schema
C = TypeVar('C', bound=BaseModel) # Create schema
U = TypeVar('U', bound=BaseModel) # Update schema


class RetrieveModelMixin(Generic[M, S]):
	"""
	Retrieve either a Pydantic schema instance or an ORM model,
	depending on whether 'self.schema' is set.
	"""
	async def retrieve(self, value: str) -> S | M | None:
		if getattr(self, 'schema', None):
			return await self._retrieve_schema(value)

		return await self._retrieve_model(value)

	async def _retrieve_schema(self, value: str) -> S | None:
		"""
		Retrieve the object and convert it to a Pydantic schema.
		"""
		obj: Row | None = await self.get_object(value)
		if obj is not None:
			obj_dict = dict(obj._mapping)
			return self.schema(**obj_dict)

		return None

	async def _retrieve_model(self, value: str) -> M | None:
		"""
		Retrieve the ORM model instance.
		"""
		return await self.get_object(value)


class ListModelMixin(Generic[S]):
	async def list(self) -> list[S]: # CHANGE NAME
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
			value: Any,     # lookup_field
			schema: U,      # data to update
			return_attributes: Optional[list[str]] = None,
			refresh: bool = True
	) -> Optional[S]:

		obj = await self.get_object(value)
		if not obj:
			return None

		for field, value in schema.model_dump(exclude_unset=True).items():
			setattr(obj, field, value)

		await self.db.commit()

		if not refresh:
			return

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
