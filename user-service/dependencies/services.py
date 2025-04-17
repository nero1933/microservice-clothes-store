from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.db import get_async_session
from services.users import UserService

def get_user_service(
    db: AsyncSession = Depends(get_async_session),
) -> UserService:
    return UserService(db)