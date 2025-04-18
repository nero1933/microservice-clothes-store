from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from crud import mixins
from crud.base_crud import M, BaseCRUD
from exceptions.custom_exceptions import EmailExistsException
from models.users import User
from schemas import UserCreateSchema, UserInDBSchema
from utils import password as p


class RegisterService(mixins.CreateModelMixin[User, UserInDBSchema],
					  BaseCRUD):
	model = User
	# lookup_field = "email"

	def __init__(self, db: AsyncSession):
		super().__init__(db)


	async def create_user(
			self,
			user_data: UserCreateSchema,
			is_active: bool = True,
			is_admin: bool = False,
	) -> User:
		""" Creates a new user. """

		hashed_password = p.get_password_hash(user_data.password)

		try:
			validated_data = UserInDBSchema(
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


	async def authenticate(
			self,
			email: str,
			password: str,
	) -> Optional[User]:
		""" Authenticate user """

		user = await self.get_object(email)
		if not user:
			return None

		if not p.verify_password(password, user.hashed_password):
			return None

		return user


# class UserMeService(mixins.RetrieveModelMixin[User],
# 					BaseCRUD):
# 	model = User
# 	lookup_field = "id"

