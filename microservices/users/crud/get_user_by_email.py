from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from core.base_crud import BaseCRUD, mixins
from exceptions import UserNotFoundException, PasswordUnchangedException
from models import User
from utils import password as p


class UserByEmailRetriever(mixins.RetrieveModelMixin,
						   BaseCRUD):
	model = User
	schema = schemas.UserForgotPassword
	lookup_field = 'email'

	def __init__(self, db: AsyncSession):
		super().__init__(db)


class UserResetPasswordCRUD(mixins.UpdateModelMixin[None, schemas.UserResetPassword],
							BaseCRUD):
	model = User
	# schema = None         # .update() needs orm model
	 				        # .get_object() returns orm model if schema is None
	# lookup_field = 'id'   # is default

	def __init__(self, db: AsyncSession):
		super().__init__(db)

	async def reset_password(
			self,
			user_id: Any,    # lookup_field
			new_password: str,   # data to update
			return_attributes: Optional[list[str]] = None,
			refresh: bool = False,
	):
		user = await self.get_object(user_id)
		if user is None:
			raise UserNotFoundException("User not found")

		old_password = user.password
		if p.verify_password(new_password, old_password):
			raise PasswordUnchangedException(
				"New password must be different from the current one"
			)
		schema = schemas.UserResetPassword(hashed_password=p.get_password_hash(new_password))
		return await self.update(user_id, schema, return_attributes, refresh)
