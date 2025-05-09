from typing import Optional, Dict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud import mixins
from core.crud.base import M, BaseCRUD
from core.loggers import log
from exceptions.exceptions import DuplicateEmailException
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
			log.warning(e)
			raise DuplicateEmailException


class LoginService:
	model = User

	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_object(self, value) -> Optional[M]:
		""" Get user with only 'id, 'email', 'hashed_password', 'is_active' fields """

		stmt = (
			select(
				self.model.id,
				self.model.email,
				self.model.hashed_password,
				self.model.role,
				self.model.is_active
			)
			.where(self.model.email == value)
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

		Returns {"user_id": user.id}
		"""

		data = {}
		user = await self.get_object(username)

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


class UserMeService(mixins.RetrieveModelMixin,
					BaseCRUD):
	model = User

	def __init__(self, db: AsyncSession):
		super().__init__(db)

	async def get_object(self, value) -> Optional[M]:
		stmt = (
			select(
				self.model.id,
				self.model.email,
				self.model.role,
				self.model.is_active,
				self.model.created_at,
			)
			.where(self.model.id == value)
		)
		result = await self.db.execute(stmt)
		return result.first()