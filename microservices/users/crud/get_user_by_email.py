from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from core.base_crud import BaseCRUD, mixins
from models import User


class UserByEmailRetriever(mixins.RetrieveModelMixin,
						   BaseCRUD):
	model = User
	schema = schemas.UserForgotPassword
	lookup_field = 'email'
	# fields = ('id', 'email') # EXTRACT FIELDS FROM SCHEMA AND PASS TO GET_OBJ

	def __init__(self, db: AsyncSession):
		super().__init__(db)
