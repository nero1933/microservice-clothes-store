from typing import Annotated

from fastapi import APIRouter, Response, Depends
import schemas
from core.exceptions.exception_factory import ExceptionDocFactory
from dependencies.tokens import get_base_token_manager, get_pair_token_manager, get_token_blacklist_manager
from exceptions.custom_exceptions import CredentialsException, InactiveUserException, NotAuthenticatedException, \
	RefreshTokenMissingException
from services.tokens import JWTBaseManager, JWTPairManager, TokenBlacklistManager

auth_router = APIRouter(prefix='/api/v1/auth', tags=['auth'])


# @router.post(
# 	"/login",
# 	response_model=schemas.TokenRead,
# 	responses={
# 		401: ExceptionDocFactory.from_exception(CredentialsException),
# 		403: ExceptionDocFactory.from_exception(InactiveUserException),
# 	},
# 	status_code=200
# )
# async def login(
# 		response: Response,
# 		form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
# 		login_service: LoginService = Depends(get_login_service),
# 		base_token_manager: JWTBaseManager = Depends(get_base_token_manager),
# ) -> schemas.TokenRead:
# 	""" Logs in user. """
#
# 	user = await login_service.authenticate(form_data.username, form_data.password)
# 	if not user:
# 		raise CredentialsException()
#
# 	if not user.is_active:
# 		raise InactiveUserException()
#
# 	# Create tokens
# 	access_token, refresh_token = base_token_manager.obtain_token_pair(sub=str(user.id))
#
# 	# Set 'refresh_token' to cookie
# 	base_token_manager.set_refresh_token_cookie(response, refresh_token)
#
# 	# Return 'access_token' in response body
# 	return schemas.TokenRead(access_token=access_token, token_type="bearer")


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
		pair_token_manager: JWTPairManager = Depends(get_pair_token_manager),
		token_blacklist_manager: TokenBlacklistManager = Depends(get_token_blacklist_manager),
):
	""" Logouts user, blacklists tokens. """

	if not pair_token_manager.refresh_token:
		raise RefreshTokenMissingException()

	try:
		# 'validate_jti=True' will check if the 'jti' is in TokenBlacklist,
		# which is redundant because the .add() method already handles the IntegrityError
		# when attempting to insert a duplicate 'jti' into the database.
		payload = await pair_token_manager.decode_and_validate_token(
			'refresh_token', validate_jti=False
		)
		await token_blacklist_manager.add(payload.get('jti'))
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
		pair_token_manager: JWTPairManager = Depends(get_pair_token_manager),
		token_blacklist_manager: TokenBlacklistManager = Depends(get_token_blacklist_manager),
) -> schemas.TokenRead:
	""" Refreshes a pair of tokens. """

	if not pair_token_manager.refresh_token:
		raise RefreshTokenMissingException()

	try:
		# Decode and validate payload of 'refresh_token'
		payload = await pair_token_manager.decode_and_validate_token('refresh_token')
		# Blacklist old 'refresh_token'
		await token_blacklist_manager.add(payload.get('jti'))
	except ValueError:
		raise CredentialsException()


	# Create new tokens
	access_token, refresh_token = pair_token_manager.obtain_token_pair(sub=payload["sub"])

	# Renew 'refresh_token' in cookie
	response.delete_cookie(key="refresh_token")
	pair_token_manager.set_refresh_token_cookie(response, refresh_token)

	# Return new 'access_token' in response body
	return schemas.TokenRead(access_token=access_token, token_type="bearer")
