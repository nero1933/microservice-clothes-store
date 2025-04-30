from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from services import TokenBlacklistService
from services.tokens import JWTTokenService


def get_jwt_token_service(
		db: AsyncSession = Depends(get_async_session),
) -> JWTTokenService:
	return JWTTokenService(db)


def get_token_blacklist_service(
		db: AsyncSession = Depends(get_async_session),
) -> TokenBlacklistService:
	return TokenBlacklistService(db)
