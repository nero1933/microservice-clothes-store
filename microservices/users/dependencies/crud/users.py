from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from crud import UserByEmailRetriever


def get_user_by_email_crud(
		db: AsyncSession = Depends(get_async_session),
) -> UserByEmailRetriever:
	return UserByEmailRetriever(db)
