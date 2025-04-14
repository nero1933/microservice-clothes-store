import uuid
from functools import wraps
from uuid import uuid4

import jwt
from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional

from fastapi import Depends, status, HTTPException, Cookie
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from db import async_get_db
from models.tokens import BlacklistedToken
from schemas import UserFullSchema
from models.users import User
from utils import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_user(email: str, db: AsyncSession) -> Optional[UserFullSchema]:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return UserFullSchema.model_validate(user) if user else None


async def authenticate_user(
        email: str,
        password: str,
        db: AsyncSession
) -> Optional[UserFullSchema]:
    """ Authenticate user """
    user = await get_user(email, db)
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif not expires_delta and data.get('type') == 'refresh':
        expire = datetime.now(timezone.utc) + timedelta(minutes=60 * 24 * 7) # default 7 days
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15) # default 15 min

    to_encode.update({"exp": expire})
    to_encode["jti"] = str(uuid4())
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_TOKEN_SECRET_KEY,
        algorithm=settings.JWT_TOKEN_ALGORITHM
    )
    return encoded_jwt


def obtain_token_pair(sub: str):
    # Create 'access_token'
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(
        data={"sub": sub, "type": "access"}, expires_delta=access_token_expires
    )
    # Create 'refresh_token'
    refresh_token_expires_minutes = 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS
    refresh_token_expires = timedelta(minutes=refresh_token_expires_minutes)
    refresh_token = create_jwt_token(
        data={"sub": sub, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    return access_token, refresh_token


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_TOKEN_SECRET_KEY,
            algorithms=[settings.JWT_TOKEN_ALGORITHM]
        )
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_jwt_payload(payload, token_type: str, db: AsyncSession) -> dict:
    """ Verify JWT token's payload. """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check jti
    jti_str = payload.get("jti")
    if not jti_str:
        raise credentials_exception

    try:
        jti = uuid.UUID(jti_str)
    except ValueError:
        raise credentials_exception

    stmt = select(BlacklistedToken).where(BlacklistedToken.jti == jti)
    result = await db.execute(stmt)
    jti_in_db = result.scalar_one_or_none()

    if jti_in_db:
        raise credentials_exception

    # Checks email
    if payload.get("sub") is None:
        raise credentials_exception

    # Checks type
    if payload.get("type") != token_type:
        raise credentials_exception

    return payload


async def blacklist_jwt_token(
        db: Annotated[AsyncSession, Depends(async_get_db)],
        access_token: Optional[str],
        refresh_token: Optional[str],
):
    for token in (access_token, refresh_token):
        if not token:
            continue

        try:
            payload = jwt.decode(
                token,
                settings.JWT_TOKEN_SECRET_KEY,
                algorithms=[settings.JWT_TOKEN_ALGORITHM]
            )
            jti_str = payload.get("jti")
            if not jti_str:
                continue

            jti = uuid.UUID(jti_str)

        except (PyJWTError, ValueError, TypeError):
            continue

        stmt = select(BlacklistedToken).where(BlacklistedToken.jti == jti)
        result = await db.execute(stmt)
        jti_in_db = result.scalar_one_or_none()
        if not jti_in_db:
            db.add(BlacklistedToken(jti=jti))

    await db.commit()


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Annotated[AsyncSession, Depends(async_get_db)]
) -> UserFullSchema:

    payload = decode_jwt_token(token)
    payload = await verify_jwt_payload(payload, token_type='access', db=db)
    email = payload.get("sub")
    current_user = await get_user(email, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
    )
    return current_user

    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials.",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    # try:
    #     payload = jwt.decode(
    #         token,
    #         settings.JWT_TOKEN_SECRET_KEY,
    #         algorithms=[settings.JWT_TOKEN_ALGORITHM]
    #     )
    #     if payload.get("type") != "access":
    #         raise credentials_exception
    #
    #     email = payload.get("sub")
    #     if email is None:
    #         raise credentials_exception
    #
    #     token_data = TokenDataSchema(email=email)
    # except InvalidTokenError:
    #     raise credentials_exception
    #
    # user = await get_user(email=token_data.email, db=db)
    # if user is None:
    #     raise credentials_exception
    #
    # return user


async def get_current_active_user(
    current_user: Annotated[UserFullSchema, Depends(get_current_user)],
) -> UserFullSchema:

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user."
        )

    return current_user


def require_user_field(field_name: str):
    """ Use to check for 'is_admin' is True. """
    def decorator(func):
        @wraps(func)
        async def wrapper(current_user: UserFullSchema, *args, **kwargs):
            if not getattr(current_user, field_name, True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User is not {field_name}."
                )

            return await func(current_user, *args, **kwargs)

        return wrapper

    return decorator
