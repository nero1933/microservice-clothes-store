from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from db import async_get_db
from exceptions.exception_factory import ExceptionDocFactory
from schemas import UserCreateSchema, UserReadSchema, TokenReadSchema, UserFullSchema
from utils.auth import authenticate_user, oauth2_scheme, get_current_active_user, \
	blacklist_jwt_token, obtain_token_pair, decode_and_validate_token, set_refresh_token_cookie
from utils.create_user import create_user
from exceptions.custom_exceptions import CredentialsException, InactiveUserException, \
	RefreshTokenMissingException, NotAuthenticatedException, EmailExistsException

router = APIRouter()


@router.post(
	'/register',
	response_model=UserReadSchema,
	responses={
		400: ExceptionDocFactory.from_exception(EmailExistsException, description='Email Error'),
	},
	status_code=201
)
async def register(
		user_data: UserCreateSchema,
		db: Annotated[AsyncSession, Depends(async_get_db)]
):
	try:
		user = await create_user(db=db, user_data=user_data, is_active=True, is_admin=False)
		return user
	except ValueError:
		raise EmailExistsException()


@router.post(
	"/login",
	response_model=TokenReadSchema,
	responses={
		401: ExceptionDocFactory.from_exception(CredentialsException),
		403: ExceptionDocFactory.from_exception(InactiveUserException),
	},
	status_code=200
)
async def login(
		response: Response,
		form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
		db: Annotated[AsyncSession, Depends(async_get_db)],
) -> TokenReadSchema:
	""" Logs in user. """

	user = await authenticate_user(form_data.username, form_data.password, db)
	if not user:
		raise CredentialsException()

	if not user.is_active:
		raise InactiveUserException()

	# Create tokens
	access_token, refresh_token = obtain_token_pair(sub=str(user.id))

	# Set 'refresh_token' to cookie
	set_refresh_token_cookie(response, refresh_token)

	# Return 'access_token' in response body
	return TokenReadSchema(access_token=access_token, token_type="bearer")


@router.post(
	"/logout",
	responses={
		401: ExceptionDocFactory.from_multiple_exceptions(
			(NotAuthenticatedException, RefreshTokenMissingException),
			description='Authentication Errors'
		),
	},
	status_code=200
)
async def logout(
		response: Response,
		db: Annotated[AsyncSession, Depends(async_get_db)],
		access_token: Annotated[str, Depends(oauth2_scheme)],
		refresh_token: Optional[str] = Cookie(default=None),
):
	""" Logouts user, blacklists tokens. """

	if not refresh_token:
		raise RefreshTokenMissingException()

	await blacklist_jwt_token(
		db=db,
		access_token=access_token,
		refresh_token=refresh_token
	)
	response.delete_cookie(key="refresh_token")
	return {"message": "Logged out successfully."}


@router.post(
	"/refresh",
	response_model=TokenReadSchema,
	responses={
		401: ExceptionDocFactory.from_multiple_exceptions(
			(CredentialsException, RefreshTokenMissingException),
			description='Authentication Errors'
		),
	},
	status_code=200
)
async def refresh(
		response: Response,
		db: Annotated[AsyncSession, Depends(async_get_db)],
		refresh_token: Optional[str] = Cookie(default=None),
) -> TokenReadSchema:
	""" Refreshes a pair of tokens. """

	if not refresh_token:
		raise RefreshTokenMissingException()

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


@router.get(
	"/me",
	response_model=UserReadSchema,
	responses={
		401: ExceptionDocFactory.from_multiple_exceptions(
			(NotAuthenticatedException, CredentialsException),
			description='Authentication Errors'
		),
		403: ExceptionDocFactory.from_exception(InactiveUserException)
	},
	status_code=200
)
async def read_user_me(
		current_user: Annotated[UserFullSchema, Depends(get_current_active_user)]
):
	""" Returns current user information """

	return UserReadSchema.model_validate(current_user)
