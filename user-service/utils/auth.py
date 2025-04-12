from datetime import datetime, timezone, timedelta

import jwt
from typing import Annotated, Optional

from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from db import async_get_db
from schemas import TokenDataSchema, UserReadSchema
from models.users import User
from schemas import UserInDBSchema
from utils import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_user(email: str, db: AsyncSession) -> Optional[UserInDBSchema]:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return UserInDBSchema.model_validate(user) if user else None


async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[User]:
    user = await get_user(email, db)
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_TOKEN_SECRET_KEY,
        algorithm=settings.JWT_TOKEN_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Annotated[AsyncSession, Depends(async_get_db)]
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_TOKEN_SECRET_KEY,
            algorithms=[settings.JWT_TOKEN_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception

        token_data = TokenDataSchema(email=email)
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user(email=token_data.email, db=db)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[UserReadSchema, Depends(get_current_user)],
):

    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user
