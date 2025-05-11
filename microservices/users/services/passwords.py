from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from core.crud import mixins
from core.crud.base import BaseCRUD
from models import User

from core.messaging import MessagingMasterClientABC


class ForgotPasswordService(mixins.RetrieveModelMixin,
							BaseCRUD):
	model = User
	lookup_field = 'email'

	def __init__(self, db: AsyncSession):
		super().__init__(db)

	async def get_object(self, value) -> BaseModel | None:
		stmt = select(self.model.id, self.model.email) \
			.where(getattr(self.model, self.lookup_field) == value)
		result = await self.db.execute(stmt)
		row = result.first()
		if row:
			return schemas.UserForgotPassword(id=row.id, email=row.email)

		return None


class Temp(MessagingMasterClientABC):
	queue_name = 'worker.email.send'
