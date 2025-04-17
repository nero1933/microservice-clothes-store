from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from crud.users import UserCRUD
from exceptions.custom_exceptions import EmailExistsException
from models.users import User
from schemas import UserCreateSchema, UserInDBSchema
from utils import get_password_hash


class UserService(UserCRUD):
	model = User

	def __init__(self, db: AsyncSession) -> None:
		super().__init__(db)


	async def create_user(
			self,
			user_data: UserCreateSchema,
			is_active: bool = True,
			is_admin: bool = False,
	) -> User:
		""" Creates a new user. """

		hashed_password = get_password_hash(user_data.password)

		try:
			validated_data = UserInDBSchema(
				**user_data.model_dump(exclude={"password"}),
				hashed_password=hashed_password,
				is_active=is_active,
				is_admin=is_admin,
			)

			print('validated_data', validated_data)

			user = await self.create(validated_data)
			return user

		except IntegrityError as e:
			await self.db.rollback()
			if 'unique constraint' in str(e.orig).lower():
				if 'email' in str(e.orig):
					raise EmailExistsException()

			raise e


	async def create_superuser(self, user_data: UserCreateSchema) -> User:
		""" Creates a new superuser. """

		return await self.create_user(user_data, is_active=True, is_admin=True)




# async def create_user(
# 		user_data: UserCreateSchema,
# 		db: AsyncSession,
# 		is_active: bool = False,
# 		is_admin: bool = False
# ) -> User:
# 	""" Create a new user. """
#
# 	hashed_password = get_password_hash(user_data.password)
#
# 	try:
# 		stmt = insert(User).values(
# 			email=user_data.email,
# 			hashed_password=hashed_password,
# 			first_name=user_data.first_name,
# 			last_name=user_data.last_name,
# 			is_active=is_active,
# 			is_admin=is_admin,
# 		)
# 		await db.execute(stmt)
# 		await db.commit()
#
# 		stmt = select(User).where(User.email == user_data.email)
# 		user = await db.execute(stmt)
# 		user = user.scalar_one_or_none()
# 		return user
#
# 	except IntegrityError as e:
# 		await db.rollback()
# 		if 'unique constraint' in str(e.orig).lower():
# 			if 'email' in str(e.orig):
# 				raise ValueError("User with this email already exists")
#
# 		raise e
#
#
# async def create_superuser(user_data: UserCreateSchema, db: AsyncSession):
# 	""" Create a new superuser. """
#
# 	return await create_user(user_data, db, is_active=True, is_admin=True)
