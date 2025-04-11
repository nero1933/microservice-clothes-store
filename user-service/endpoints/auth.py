from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from db import get_db
from schemas import UserCreateSchema, UserReadSchema, TokenReadSchema
from utils.auth import authenticate_user, create_access_token, get_current_active_user
from utils.create_user import create_user

router = APIRouter(prefix="/auth", tags=["users"])


@router.post('/register', response_model=UserReadSchema, status_code=201)
async def register_user(user_data: UserCreateSchema, db: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(db=db, user_data=user_data, is_active=True, is_admin=False)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenReadSchema, status_code=200)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: AsyncSession = Depends(get_db)
) -> TokenReadSchema:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return TokenReadSchema(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserReadSchema, status_code=200)
async def read_users_me(
    current_user: Annotated[UserReadSchema, Depends(get_current_active_user)]
):
    return current_user
