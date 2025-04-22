import logging
from typing import Optional, Dict, Union

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud import mixins
from core.crud.base_crud import M, BaseCRUD
from exceptions.custom_exceptions import EmailExistsException
from loggers import default_logger
from models import User
import schemas
from utils import password as p


class RegisterService(mixins.CreateModelMixin[User, schemas.UserInDB],
					  BaseCRUD):
	model = User
	# lookup_field = "email"

	def __init__(self, db: AsyncSession):
		super().__init__(db)


	async def create_user(
			self,
			user_data: schemas.UserCreate,
			is_active: bool = True,
			is_admin: bool = False,
	) -> User:
		""" Creates a new user. """

		hashed_password = p.get_password_hash(user_data.password)

		try:
			validated_data = schemas.UserInDB(
				**user_data.model_dump(exclude={"password"}),
				hashed_password=hashed_password,
				is_active=is_active,
				is_admin=is_admin,
			)

			return await self.create(
				validated_data,
				return_attributes=[
					'email', 'first_name', 'last_name', 'is_active', 'created_at'
				]
			)

		except IntegrityError as e:
			await self.db.rollback()
			if 'unique constraint' in str(e.orig).lower() and 'email' in str(e.orig):
				raise EmailExistsException()

			raise e

	# async def create_superuser(self, user_data: UserCreateSchema) -> User:
	# 	""" Creates a new superuser. """
	#
	# 	return await self.create_user(user_data, is_active=True, is_admin=True)


class LoginService:
	model = User

	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_object(self, value) -> Optional[M]:
		""" Get user with only 'email', 'hashed_password', 'is_active' fields """

		stmt = (
			select(
				self.model.id,
				self.model.email,
				self.model.hashed_password,
				self.model.is_active
			)
			.where(self.model.email == value)
		)
		result = await self.db.execute(stmt)
		return result.first()

	@staticmethod
	def check_permission(user: User) -> bool:
		return user.is_active

	async def authenticate(
			self,
			email: str,
			password: str,
	) -> Optional[Dict[str, Union[str, bool]]]:
		"""
		Authenticate user
		Returns {"user_id": "some uuid4 string", "permission": "True"}
		"""

		default_logger.info(f'[.] Try to authenticate user: {email}')

		data = {'user_id': '', 'permission': True}
		user = await self.get_object(email)

		if not user:
			return None

		if not p.verify_password(password, user.hashed_password):
			return None

		permission = self.check_permission(user)
		if not permission:
			data['permission'] = False

		data['user_id'] = str(user.id) # UUID to str
		return data


# class UserMeService(mixins.RetrieveModelMixin[User],
# 					BaseCRUD):
# 	model = User
# 	lookup_field = "id"

