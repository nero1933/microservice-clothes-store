from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.db import get_async_session
from services.users import RegisterService, LoginService


def get_register_service(
    db: AsyncSession = Depends(get_async_session),
) -> RegisterService:
    return RegisterService(db)


def get_login_service(
        db: AsyncSession = Depends(get_async_session),
) -> LoginService:
    return LoginService(db)
