from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from core.abc_crud import mixins
from core.abc_crud.base import BaseCRUD
from models import User


class UserByEmailRetriever(mixins.RetrieveModelMixin,
						   BaseCRUD):
	model = User
	schema = schemas.UserForgotPassword
	lookup_field = 'email'
	fields = ('id', 'email')

	def __init__(self, db: AsyncSession):
		super().__init__(db)
