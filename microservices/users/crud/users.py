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


class UserResetPasswordCRUD(mixins.UpdateModelMixin[None, schemas.ResetPassword],
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
	):
		# user = await self.get_object(user_id)
		# if user is None:
		# 	raise UserNotFoundException("User not found")
		#
		# old_hashed_password = user.hashed_password
		# if p.verify_password(new_password, old_hashed_password):
		# 	raise PasswordUnchangedException(
		# 		"New password must be different from the current one"
		# 	)
		return await self.update(user_id, p.get_password_hash(new_password))

	async def update_password(self, user_id, new_hashed_password):
		pass
