from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_async_session
from dependencies.services import get_register_service, get_login_service
from exceptions.exception_factory import ExceptionDocFactory
from schemas import UserCreateSchema, UserReadSchema, TokenReadSchema, UserFullSchema, UserBaseSchema
from services.auth import oauth2_scheme, get_current_active_user, \
	blacklist_jwt_token, obtain_token_pair, decode_and_validate_token, set_refresh_token_cookie
from services.users import RegisterService, LoginService
from exceptions.custom_exceptions import CredentialsException, InactiveUserException, \
	RefreshTokenMissingException, NotAuthenticatedException, EmailExistsException, BadRequestException

router = APIRouter(prefix='/api/v1/auth', tags=['auth'])


@router.post(
	'/register',
	response_model=UserReadSchema,
	responses={
		400: ExceptionDocFactory.from_multiple_exceptions(
			(EmailExistsException, BadRequestException),
			description='Email Error'
		),
	},
	status_code=201
)
async def register(
		user_data: UserCreateSchema,
		register_service: RegisterService = Depends(get_register_service),
):
	user = await register_service.create_user(
		user_data=user_data,
		is_active=True,
		is_admin=False
	)
	return UserReadSchema.model_validate(user)


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
		login_service: LoginService = Depends(get_login_service),
) -> TokenReadSchema:
	""" Logs in user. """

	user = await login_service.authenticate(form_data.username, form_data.password)
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
		db: Annotated[AsyncSession, Depends(get_async_session)],
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
		db: Annotated[AsyncSession, Depends(get_async_session)],
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
