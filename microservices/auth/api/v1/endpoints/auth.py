from typing import Annotated

from fastapi import APIRouter, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm

import schemas
from core.exceptions import ExceptionDocFactory
from dependencies import get_base_token_service, get_pair_token_service, \
	get_token_blacklist_service, get_auth_service
from exceptions.custom_exceptions import CredentialsException, InactiveUserException, NotAuthenticatedException, \
	RefreshTokenMissingException
from api.v1.services import JWTBaseService, JWTPairService, TokenBlacklistService, AuthService

auth_router = APIRouter(prefix='/api/v1/auth', tags=['auth'])


@auth_router.post(
	"/login",
	response_model=schemas.TokenRead,
	responses={
		401: ExceptionDocFactory.from_exception(CredentialsException),
		403: ExceptionDocFactory.from_exception(InactiveUserException),
	},
	status_code=200
)
async def login(
		response: Response,
		form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
		auth_service: AuthService = Depends(get_auth_service),
		base_token_service: JWTBaseService = Depends(get_base_token_service),
) -> schemas.TokenRead:
	""" Logs in user. """

	auth_data = await auth_service.authenticate(form_data.username, form_data.password)
	error = auth_data.get('error')
	if error:
		if 'No permission' in error:
			raise InactiveUserException()
		else:
			raise CredentialsException()

	user_id = auth_data.get('user_id')

	# Create tokens
	access_token, refresh_token = base_token_service.obtain_token_pair(sub=user_id)

	# Set 'refresh_token' to cookie
	base_token_service.set_refresh_token_cookie(response, refresh_token)

	# Return 'access_token' in response body
	return schemas.TokenRead(access_token=access_token, token_type="bearer")


@auth_router.post(
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
		pair_token_service: JWTPairService = Depends(get_pair_token_service),
		token_blacklist_service: TokenBlacklistService = Depends(get_token_blacklist_service),
):
	""" Logouts user, blacklists tokens. """

	if not pair_token_service.refresh_token:
		raise RefreshTokenMissingException()

	try:
		# 'validate_jti=True' will check if the 'jti' is in TokenBlacklist,
		# which is redundant because the .add() method already handles the IntegrityError
		# when attempting to insert a duplicate 'jti' into the database.
		payload = await pair_token_service.decode_and_validate_token(
			'refresh_token', validate_jti=False
		)
		await token_blacklist_service.add(payload.get('jti'))
	except ValueError:
		pass

	response.delete_cookie(key="refresh_token")
	return {"message": "Logged out successfully."}


@auth_router.post(
	"/refresh",
	response_model=schemas.TokenRead,
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
		pair_token_service: JWTPairService = Depends(get_pair_token_service),
		token_blacklist_service: TokenBlacklistService = Depends(get_token_blacklist_service),
) -> schemas.TokenRead:
	""" Refreshes a pair of tokens. """

	if not pair_token_service.refresh_token:
		raise RefreshTokenMissingException()

	try:
		# Decode and validate payload of 'refresh_token'
		payload = await pair_token_service.decode_and_validate_token('refresh_token')
		# Blacklist old 'refresh_token'
		await token_blacklist_service.add(payload.get('jti'))
	except ValueError:
		raise CredentialsException()


	# Create new tokens
	access_token, refresh_token = pair_token_service.obtain_token_pair(sub=payload["sub"])

	# Renew 'refresh_token' in cookie
	response.delete_cookie(key="refresh_token")
	pair_token_service.set_refresh_token_cookie(response, refresh_token)

	# Return new 'access_token' in response body
	return schemas.TokenRead(access_token=access_token, token_type="bearer")
