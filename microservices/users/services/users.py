from typing import Dict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.base_crud import mixins, BaseCRUD
from core.loggers import log
from exceptions.exceptions import DuplicateEmailException
from models import User, RoleEnum
import schemas
from utils import password as p


class RegisterService(mixins.CreateModelMixin[User, schemas.UserInDB],
					  BaseCRUD[User, schemas.UserInDB]):
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
			# log.warning(e)
			raise DuplicateEmailException


class LoginService(mixins.RetrieveModelMixin[User, schemas.UserFull],
				   BaseCRUD[User, schemas.UserFull]):
	model = User
	schema = schemas.UserFull
	lookup_field = 'email'

	def __init__(self, db: AsyncSession):
		super().__init__(db)

	@staticmethod
	def check_permission(user: schemas.UserFull) -> bool:
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

		Returns {"user_id": user.id}
		"""

		data = {}
		user = await self.retrieve(username)

		if not user:
			log.info(f'[!] RPC | No such user: <{username}>')
			return data

		if not p.verify_password(password, user.hashed_password):
			log.info(f'[!] RPC | Wrong password for user: <{username}>')
			return data

		permission = self.check_permission(user)
		if not permission:
			log.info(f'[!] RPC | No permission for user: <{username}>')
			return data

		data.setdefault('user_id', str(user.id)) # UUID to str
		# data.setdefault('role', str(user.role.value))  # UUID to str
		return data


class UserMeService(mixins.RetrieveModelMixin[User, schemas.UserRead],
					BaseCRUD[User, schemas.UserRead]):
	model = User
	schema = schemas.UserRead

	def __init__(self, db: AsyncSession):
		super().__init__(db)
