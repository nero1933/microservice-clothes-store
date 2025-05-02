from typing import Annotated

import jwt
from fastapi import APIRouter, Response, Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, \
	HTTPAuthorizationCredentials

import schemas
from core.exceptions import ExceptionDocFactory
from core.loggers import log
from core.exceptions.http import CredentialsHTTPException
from exceptions.exceptions import JWTTokenValidationException, DuplicateJTIException
from services import TokenBlacklistService, AuthRPCService
from services.tokens import JWTTokenService
from dependencies import  get_token_blacklist_service, get_auth_rpc_service, \
	get_jwt_token_service
from exceptions.http import ExpiredSignatureHTTPException, \
	RefreshTokenMissingHTTPException

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
		auth_rpc_service: AuthRPCService = Depends(get_auth_rpc_service),
		jwt_token_service: JWTTokenService = Depends(get_jwt_token_service),
) -> schemas.TokenRead:
	"""
	   Authenticates a user with their `username` and `password`, issues a new JWT token pair.
	\n User can authenticate with `username` or `email`
	\n On successful authentication:
	\n - Returns an `access_token` in the response body.
	\n - Sets the `refresh_token` as an HttpOnly cookie.
	"""

	auth_data = await auth_rpc_service.authenticate(form_data.username, form_data.password)
	log.info(f'/login * User logs in: <{form_data.username}>')
	if not auth_data: # If RPC returns {} raise 401
		log.warning(f'/login * User failed to log in: <{form_data.username}>')
		raise CredentialsHTTPException()

	user_id = auth_data.get('user_id')

	# Create tokens with 'sub'='user_id'
	access_token, refresh_token = jwt_token_service.obtain_token_pair(sub=user_id)

	# Set 'refresh_token' to cookie
	jwt_token_service.set_refresh_token_cookie(response, refresh_token)

	# Return 'access_token' in response body
	return schemas.TokenRead(access_token=access_token, token_type="bearer")


@auth_router.post(
	"/logout",
	responses={
		401: ExceptionDocFactory.from_multiple_exceptions(
			(CredentialsHTTPException, RefreshTokenMissingHTTPException),
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
	"""
	   Logs out the user by blacklisting the refresh token and deleting it from cookies.
	\n This endpoint requires an access token to be called, but the access token itself is not validated.
	\n Instead, the refresh token (stored in the cookie) is decoded and its `jti` is blacklisted to prevent reuse.
	\n On successful logout:
	\n - Deletes the `refresh_token` cookie.
	\n - Returns a success message.
	"""

	# To access endpoint 'access_token' is required but token wouldn't be validated
	access_token = credentials.credentials if credentials else None
	if not access_token:
		log.warning("/logout * Missing 'access_token'")
		raise CredentialsHTTPException()

	if not refresh_token:
		raise RefreshTokenMissingHTTPException()

	jwt_token_service.refresh_token = refresh_token

	try:
		payload = await jwt_token_service.decode_and_validate_token('refresh_token')
		await token_blacklist_service.add(payload.get('jti'))
	except (JWTTokenValidationException, DuplicateJTIException) as e:
		log.info(f"/logout * Error when validating 'refresh_token': {e}")

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
		refresh_token: str = Cookie(None)
) -> schemas.TokenRead:
	"""
	   Refreshes the JWT token pair using a valid `refresh_token`.
	\n On successful refresh:
	\n - Requires a valid `refresh_token` provided via HttpOnly cookie.
	\n - Verifies the token and ensures its `jti` is not blacklisted.
	\n - Blacklists the old `refresh_token` to prevent reuse.
	\n - Issues a new `access_token` in the response body.
	\n - Sets a new `refresh_token` in the HttpOnly cookie.
	"""

	if not refresh_token:
		log.warning("/refresh * Missing 'refresh_token'")
		raise RefreshTokenMissingHTTPException()

	jwt_token_service.refresh_token = refresh_token

	try:
		payload = await jwt_token_service.decode_and_validate_token('refresh_token')
		await token_blacklist_service.add(payload.get('jti'))
	except (JWTTokenValidationException, DuplicateJTIException):
		raise CredentialsHTTPException()

	# Create new tokens
	access_token, refresh_token = jwt_token_service.obtain_token_pair(sub=payload["sub"])

	# Renew 'refresh_token' in cookie
	response.delete_cookie(key="refresh_token")
	jwt_token_service.set_refresh_token_cookie(response, refresh_token)

	# Return new 'access_token' in response body
	return schemas.TokenRead(access_token=access_token, token_type="bearer")


@auth_router.get(
	'/authenticate',
	responses={
		401: ExceptionDocFactory.from_multiple_exceptions(
			(CredentialsHTTPException, ExpiredSignatureHTTPException),
			description='Authentication Errors'
		),
	},
	status_code=200,
)
async def authenticate(
		jwt_token_service: JWTTokenService = Depends(get_jwt_token_service),
		credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
	"""
	   Validates the provided `access_token` to authenticate the user.

    \n This endpoint is primarily used internally by the API Gateway (e.g., `AuthForward`)
    \n to verify a user's identity and forward their `user_id` to downstream services
    \n via the `X-User-Id` header.

    \n On successful validation:
    \n - Returns a 200 OK response.
    \n - Injects the `user_id` into the response header as `X-User-Id`.
	"""

	access_token = credentials.credentials if credentials else None
	if not access_token:
		log.warning("/authenticate * Missing 'access_token'")
		raise CredentialsHTTPException()

	jwt_token_service.access_token = access_token

	try:
		payload = await jwt_token_service.decode_and_validate_token('access_token')
	except JWTTokenValidationException:
		log.warning("/authenticate * Invalid 'access_token'")
		raise CredentialsHTTPException()
	except jwt.ExpiredSignatureError:
		log.warning("/authenticate * Expired 'access_token'")
		raise ExpiredSignatureHTTPException()

	response = Response(status_code=200)
	user_id = str(payload['sub'])
	response.headers['X-User-Id'] = user_id
	log.info(f'/authenticate * Authenticated user_id: <{user_id}>')
	return response
