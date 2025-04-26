from typing import Annotated, Optional
from fastapi import Depends, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from api.v1.services import TokenBlacklistService, JWTAccessService, JWTBaseService, \
	JWTPairService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_base_token_service(
		db: AsyncSession = Depends(get_async_session),
) -> JWTBaseService:
	return JWTBaseService(db)


def get_access_token_service(
		access_token: Annotated[str, Depends(oauth2_scheme)],
		db: AsyncSession = Depends(get_async_session),
) -> JWTAccessService:
	return JWTAccessService(db, access_token)


def get_pair_token_service(
		access_token: Annotated[str, Depends(oauth2_scheme)],
		refresh_token: Optional[str] = Cookie(default=None),
		db: AsyncSession = Depends(get_async_session),
) -> JWTPairService:
	return JWTPairService(db, access_token, refresh_token)


def get_token_blacklist_service(
		db: AsyncSession = Depends(get_async_session),
) -> TokenBlacklistService:
	return TokenBlacklistService(db)
