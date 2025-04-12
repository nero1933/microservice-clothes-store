from datetime import timedelta
from typing import Annotated, Optional
from jwt import PyJWTError

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from db import async_get_db
from schemas import UserCreateSchema, UserReadSchema, TokenReadSchema
from utils.auth import authenticate_user, get_current_active_user, create_token, oauth2_scheme
from utils.create_user import create_user

router = APIRouter(prefix="/auth", tags=["users"])


@router.post('/register', response_model=UserReadSchema, status_code=201)
async def register_user(
        user_data: UserCreateSchema,
        db: Annotated[AsyncSession, Depends(async_get_db)]
):
    try:
        user = await create_user(db=db, user_data=user_data, is_active=True, is_admin=False)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenReadSchema, status_code=200)
async def login(
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[AsyncSession, Depends(async_get_db)],
) -> TokenReadSchema:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create 'access_token'
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={"sub": user.email, "type": "access"}, expires_delta=access_token_expires
    )
    # Create 'refresh_token'
    max_age = 60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS
    refresh_token_expires = timedelta(seconds=max_age)
    refresh_token = create_token(
        data={"sub": user.email, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        # secure=True,
        samesite="strict",
        path="/refresh",
        max_age=max_age,
    )

    return TokenReadSchema(access_token=access_token, token_type="bearer")

@router.post("/logout", status_code=200)
async def logout(
        response: Response,
        db: Annotated[AsyncSession, Depends(async_get_db)],
        access_token: Annotated[str, Depends(oauth2_scheme)],
        refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
):
    try:
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token not found")

        # Block tokens
        # ---> Implement <---

        response.delete_cookie(key="refresh_token")

        return {"message": "Logged out successfully"}

    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/me", response_model=UserReadSchema, status_code=200)
async def read_users_me(
    current_user: Annotated[UserReadSchema, Depends(get_current_active_user)]
):
    return current_user
