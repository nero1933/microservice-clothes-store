from typing import Annotated

import jwt
from fastapi import APIRouter, Response, Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, \
	HTTPAuthorizationCredentials

import schemas
from core.exceptions import ExceptionDocFactory
from exceptions.exceptions import JWTTokenValidationException
from loggers import default_logger
from services import TokenBlacklistService, AuthService
from services.tokens import JWTTokenService
from dependencies import  get_token_blacklist_service, get_auth_service, \
	get_jwt_token_service
from exceptions.http import CredentialsHTTPException, ExpiredSignatureHTTPException, \
	RefreshTokenMissingHTTPException, NotAuthenticatedHTTPException

auth_scheme = HTTPBearer(auto_error=False)
auth_router = APIRouter(prefix='/api/v1/auth', tags=['auth'])


@auth_router.post(
	"/login",
	response_model=schemas.TokenRead,
	responses={401: ExceptionDocFactory.from_exception(CredentialsHTTPException)},
	status_code=200
)
async def login(
		response: Response,
		form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
		auth_service: AuthService = Depends(get_auth_service),
		jwt_token_service: JWTTokenService = Depends(get_jwt_token_service),
) -> schemas.TokenRead:
	""" Logs in user. """

	auth_data = await auth_service.authenticate(form_data.username, form_data.password)
	default_logger.info(f'/login * User logs in: {form_data.username}')
	if not auth_data: # If RPC returns {} raise 401
		default_logger.warning(f'/login * User failed to log in: {form_data.username}')
		raise CredentialsHTTPException()

	user_id = auth_data.get('user_id')

	# Create tokens
	access_token, refresh_token = jwt_token_service.obtain_token_pair(sub=user_id)

	# Set 'refresh_token' to cookie
	jwt_token_service.set_refresh_token_cookie(response, refresh_token)

	# Return 'access_token' in response body
	return schemas.TokenRead(access_token=access_token, token_type="bearer")


@auth_router.post(
	"/logout",
	responses={
		401: ExceptionDocFactory.from_multiple_exceptions(
			(NotAuthenticatedHTTPException, RefreshTokenMissingHTTPException),
			description='Authentication Errors'
		),
	},
	status_code=200,
	dependencies=[Depends(auth_scheme)]
)
async def logout(
		response: Response,
		credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
		jwt_token_service: JWTTokenService = Depends(get_jwt_token_service),
		token_blacklist_service: TokenBlacklistService = Depends(get_token_blacklist_service),
		refresh_token: str = Cookie(None)
):
	""" Logouts user, blacklists tokens. """

	if not refresh_token:
		raise RefreshTokenMissingHTTPException()

	jwt_token_service.refresh_token = refresh_token

	try:
		# 'validate_jti=True' will check if the 'jti' is in TokenBlacklist,
		# which is redundant because the .add() method already handles the IntegrityError
		# when attempting to insert a duplicate 'jti' into the database.
		payload = await jwt_token_service.decode_and_validate_token(
			'refresh_token', validate_jti=False
		)
		await token_blacklist_service.add(payload.get('jti'))
	except ValueError:
		default_logger.info(f"/logout * ValueError when validating refresh token")

	response.delete_cookie(key="refresh_token")
	return {"message": "Logged out successfully."}


@auth_router.post(
	"/refresh",
	response_model=schemas.TokenRead,
	responses={
		401: ExceptionDocFactory.from_multiple_exceptions(
			(CredentialsHTTPException, RefreshTokenMissingHTTPException),
			description='Authentication Errors'
		),
	},
	status_code=200,
	dependencies=[Depends(auth_scheme)]
)
async def refresh(
		response: Response,
		jwt_token_service: JWTTokenService = Depends(get_jwt_token_service),
		token_blacklist_service: TokenBlacklistService = Depends(get_token_blacklist_service),
) -> schemas.TokenRead:
	""" Refreshes a pair of tokens. """

	#
	# GET COOKIE, CHECK, SET TO jwt_token_service
	#

	if not jwt_token_service.refresh_token:
		raise RefreshTokenMissingHTTPException()

	try:
		# Decode and validate payload of 'refresh_token'
		payload = await jwt_token_service.decode_and_validate_token('refresh_token')
		# Blacklist old 'refresh_token'
		await token_blacklist_service.add(payload.get('jti'))
	except ValueError:
		raise CredentialsHTTPException()


	# Create new tokens
	access_token, refresh_token = jwt_token_service.obtain_token_pair(sub=payload["sub"])

	# Renew 'refresh_token' in cookie
	response.delete_cookie(key="refresh_token")
	jwt_token_service.set_refresh_token_cookie(response, refresh_token)

	# Return new 'access_token' in response body
	return schemas.TokenRead(access_token=access_token, token_type="bearer")


@auth_router.get('/authenticate')
async def authenticate(
		jwt_token_service: JWTTokenService = Depends(get_jwt_token_service),
		credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):

	access_token = credentials.credentials if credentials else None
	if not access_token:
		default_logger.warning('/authenticate * Missing access token')
		raise CredentialsHTTPException()

	jwt_token_service.access_token = access_token

	try:
		payload = await jwt_token_service.decode_and_validate_token('access_token')
	except JWTTokenValidationException:
		default_logger.warning(
			'/authenticate * Invalid access token'
		)
		raise CredentialsHTTPException()
	except jwt.ExpiredSignatureError:
		default_logger.warning(
			'/authenticate * Expired access token'
		)
		raise ExpiredSignatureHTTPException()

	response = Response(status_code=200)
	user_id = payload['sub']
	response.headers['X-User-Id'] = user_id
	default_logger.info(
		f'/authenticate * Authenticated user_id: {user_id}'
	)
	return response
