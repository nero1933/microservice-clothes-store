from typing import Annotated, Optional
from fastapi import Depends, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.db_dependency import get_async_session
from services.tokens import TokenBlacklistManager, JWTAccessManager, JWTBaseManager, \
	JWTPairManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_base_token_manager(
		db: AsyncSession = Depends(get_async_session),
) -> JWTBaseManager:
	return JWTBaseManager(db)


def get_access_token_manager(
		access_token: Annotated[str, Depends(oauth2_scheme)],
		db: AsyncSession = Depends(get_async_session),
) -> JWTAccessManager:
	return JWTAccessManager(db, access_token)


def get_pair_token_manager(
		access_token: Annotated[str, Depends(oauth2_scheme)],
		refresh_token: Optional[str] = Cookie(default=None),
		db: AsyncSession = Depends(get_async_session),
) -> JWTPairManager:
	return JWTPairManager(db, access_token, refresh_token)


def get_token_blacklist_manager(
		db: AsyncSession = Depends(get_async_session),
) -> TokenBlacklistManager:
	return TokenBlacklistManager(db)
