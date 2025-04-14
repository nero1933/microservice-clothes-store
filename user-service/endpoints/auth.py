from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from db import async_get_db
from schemas import UserCreateSchema, UserReadSchema, TokenReadSchema, UserFullSchema
from schemas.error_responses import ErrorResponse
from utils.auth import authenticate_user, oauth2_scheme, \
    get_current_active_user, blacklist_jwt_token, obtain_token_pair, decode_and_validate_token, \
    set_refresh_token_cookie, raise_credentials_exception
from utils.create_user import create_user

router = APIRouter()


@router.post('/register', response_model=UserReadSchema, status_code=201)
async def register(
        user_data: UserCreateSchema,
        db: Annotated[AsyncSession, Depends(async_get_db)]
):
    try:
        user = await create_user(db=db, user_data=user_data, is_active=True, is_admin=False)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/login",
    response_model=TokenReadSchema,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Invalid credentials",
        },
        403: {
            "model": ErrorResponse,
            "description": "Inactive user",
        },
    },
    status_code=200
)
async def login(
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[AsyncSession, Depends(async_get_db)],
) -> TokenReadSchema:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise_credentials_exception()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token, refresh_token = obtain_token_pair(sub=str(user.id))

    # Set 'refresh_token' to cookie
    set_refresh_token_cookie(response, refresh_token)

    # Return 'access_token' in response body
    return TokenReadSchema(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=200)
async def logout(
        response: Response,
        db: Annotated[AsyncSession, Depends(async_get_db)],
        access_token: Annotated[str, Depends(oauth2_scheme)],
        refresh_token: Optional[str] = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found."
        )

    await blacklist_jwt_token(
        db=db,
        access_token=access_token,
        refresh_token=refresh_token
    )
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully."}


@router.post("/refresh", response_model=TokenReadSchema, status_code=200)
async def refresh(
        response: Response,
        db: Annotated[AsyncSession, Depends(async_get_db)],
        refresh_token: Optional[str] = Cookie(default=None),
) -> TokenReadSchema:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token not found."
        )

    # Decode and validate payload
    payload = await decode_and_validate_token(refresh_token, token_type="refresh", db=db)

    # Blacklist old 'refresh_token'
    await blacklist_jwt_token(
        db=db,
        access_token=None,
        refresh_token=refresh_token
    )

    # Create new tokens
    access_token, refresh_token = obtain_token_pair(sub=payload["sub"])

    # Renew 'refresh_token' in cookies
    response.delete_cookie(key="refresh_token")
    set_refresh_token_cookie(response, refresh_token)

    # Return new 'access_token' in response body
    return TokenReadSchema(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserReadSchema, status_code=200)
async def read_user_me(
    current_user: Annotated[UserFullSchema, Depends(get_current_active_user)]
):
    """ Returns current user information """
    return UserReadSchema.model_validate(current_user)
