from typing import Optional, Dict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud import mixins
from core.crud.base import M, BaseCRUD
# from core.exceptions.custom_http_exception import EmailExistsException
from loggers import default_logger
from models import User, RoleEnum
import schemas
from utils import password as p


class RegisterService(mixins.CreateModelMixin[User, schemas.UserInDB],
					  BaseCRUD):
	model = User

	def __init__(self, db: AsyncSession):
		super().__init__(db)


	async def create_user(
			self,
			user_data: schemas.UserCreate,
			is_active: bool = True,
			role: str = 'user',
	) -> User:
		""" Creates a new user. """

		hashed_password = p.get_password_hash(user_data.password)

		try:
			validated_data = schemas.UserInDB(
				**user_data.model_dump(exclude={"password"}),
				hashed_password=hashed_password,
				is_active=is_active,
				role=role
			)
			return await self.create(validated_data)

		except IntegrityError as e:
			await self.db.rollback()
			if 'unique constraint' in str(e.orig).lower() and 'email' in str(e.orig):
				# raise EmailExistsException()
				pass

			raise e

	# async def create_superuser(self, user_data: UserCreateSchema) -> User:
	# 	""" Creates a new superuser. """
	#
	# 	return await self.create_user(user_data, is_active=True, is_admin=True)


class LoginService:
	model = User

	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_object(self, field, value) -> Optional[M]:
		""" Get user with only 'email', 'hashed_password', 'is_active' fields """
		valid_fields = ('username', 'email')

		if field not in valid_fields:
			raise KeyError("field must be ether 'username' or 'email'")

		stmt = (
			select(
				self.model.id,
				self.model.username,
				self.model.email,
				self.model.hashed_password,
				self.model.role,
				self.model.is_active
			)
			.where(getattr(self.model, field) == value)
		)
		result = await self.db.execute(stmt)
		return result.first()

	@staticmethod
	def check_permission(user: User) -> bool:
		if not user.is_active:
			return False

		if user.role == RoleEnum.banned:
			return False

		return True

	async def authenticate(
			self,
			username: str,
			password: str,
	) -> Dict[str, str]:
		"""
		Authenticates user

		Returns {"user_id": user.id, "role": user.role}
		"""

		default_logger.info(f'[x] -> Trying to authenticate user: {username}')
		data = {}
		if '@' in username:
			field = 'email'
		else:
			field = 'username'

		user = await self.get_object(field, username)

		if not user:
			default_logger.info(f'[x] -> No such user: {username}')
			return data

		if not p.verify_password(password, user.hashed_password):
			default_logger.info(f'[x] -> Wrong password for user: {username}')
			return data

		permission = self.check_permission(user)
		if not permission:
			default_logger.info(f'[x] -> No permission for user: {username}')
			return data

		data.setdefault('user_id', str(user.id)) # UUID to str
		data.setdefault('role', str(user.role.value))  # UUID to str
		default_logger.info(f'[x] -> Authentication data: {data}')
		return data


# class UserMeService(mixins.RetrieveModelMixin[User],
# 					BaseCRUD):
# 	model = User
# 	lookup_field = "id"

