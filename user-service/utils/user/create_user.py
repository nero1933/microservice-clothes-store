from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User
from schemas import UserCreateSchema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str):
    return pwd_context.hash(password)


async def create_user(user_data: UserCreateSchema, db: AsyncSession,
                      is_active: bool = False, is_admin: bool = False):
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=is_active,
        is_admin=is_admin,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError as e:
        await db.rollback()
        if 'unique constraint' in str(e.orig).lower():
            raise ValueError("User with this email already exists!")
        raise e


async def create_superuser(user_data: UserCreateSchema, db: AsyncSession):
    return await create_user(user_data, db, is_active=True, is_admin=True)
