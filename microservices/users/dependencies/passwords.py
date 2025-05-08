from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_async_session
from services.passwords import ForgotPasswordService

from services.passwords import Temp


def get_forgot_password_service(
		db: AsyncSession = Depends(get_async_session),
) -> ForgotPasswordService:
	return ForgotPasswordService(db)


def get_temp(
) -> Temp:
	return Temp()