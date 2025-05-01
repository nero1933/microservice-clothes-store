from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy import select

import schemas
from core.db import get_async_session, AsyncSessionLocal
from core.exceptions import ExceptionDocFactory
from dependencies import get_register_service
from models import User
from services import RegisterService
from core.exceptions.custom_http_exception import EmailExistsException, BadRequestException

auth_scheme = HTTPBearer()
users_router = APIRouter(prefix='/api/v1/users', tags=['users'])


@users_router.post(
	'/register',
	response_model=schemas.UserRead,
	responses={
		400: ExceptionDocFactory.from_multiple_exceptions(
			(EmailExistsException, BadRequestException),
			description='Email Error'
		),
	},
	status_code=201
)
async def register(
		user_data: schemas.UserCreate,
		register_service: RegisterService = Depends(get_register_service),
):
	user = await register_service.create_user(
		user_data=user_data,
		is_active=False,
		role='user'
	)
	return schemas.UserRead.model_validate(user)


@users_router.get('/me', dependencies=[Depends(auth_scheme)])
async def me(request: Request, db: AsyncSessionLocal = Depends(get_async_session)):
	user_id = request.headers.get('X-User-Id')
	stmt = select(User).where(User.id == user_id)
	result = await db.execute(stmt)
	r = result.scalar_one_or_none()
	if not r:
		return {'message': 'User not found'}

	return schemas.UserRead.model_validate(r)


# @router.post(
# 	"/login",
# 	response_model=TokenReadSchema,
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
# ) -> TokenReadSchema:
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
# 	return TokenReadSchema(access_token=access_token, token_type="bearer")
#
#
# @router.post(
# 	"/logout",
# 	responses={
# 		401: ExceptionDocFactory.from_multiple_exceptions(
# 			(NotAuthenticatedException, RefreshTokenMissingException),
# 			description='Authentication Errors'
# 		),
# 	},
# 	status_code=200
# )
# async def logout(
# 		response: Response,
# 		pair_token_manager: JWTPairManager = Depends(get_pair_token_manager),
# 		token_blacklist_manager: TokenBlacklistManager = Depends(get_token_blacklist_manager),
# ):
# 	""" Logouts user, blacklists tokens. """
#
# 	if not pair_token_manager.refresh_token:
# 		raise RefreshTokenMissingException()
#
# 	try:
# 		# 'validate_jti=True' will check if the 'jti' is in TokenBlacklist,
# 		# which is redundant because the .add() method already handles the IntegrityError
# 		# when attempting to insert a duplicate 'jti' into the database.
# 		payload = await pair_token_manager.decode_and_validate_token(
# 			'refresh_token', validate_jti=False
# 		)
# 		await token_blacklist_manager.add(payload.get('jti'))
# 	except ValueError:
# 		pass
#
# 	response.delete_cookie(key="refresh_token")
# 	return {"message": "Logged out successfully."}
#
#
# @router.post(
# 	"/refresh",
# 	response_model=TokenReadSchema,
# 	responses={
# 		401: ExceptionDocFactory.from_multiple_exceptions(
# 			(CredentialsException, RefreshTokenMissingException),
# 			description='Authentication Errors'
# 		),
# 	},
# 	status_code=200
# )
# async def refresh(
# 		response: Response,
# 		pair_token_manager: JWTPairManager = Depends(get_pair_token_manager),
# 		token_blacklist_manager: TokenBlacklistManager = Depends(get_token_blacklist_manager),
# ) -> TokenReadSchema:
# 	""" Refreshes a pair of tokens. """
#
# 	if not pair_token_manager.refresh_token:
# 		raise RefreshTokenMissingException()
#
# 	try:
# 		# Decode and validate payload of 'refresh_token'
# 		payload = await pair_token_manager.decode_and_validate_token('refresh_token')
# 		# Blacklist old 'refresh_token'
# 		await token_blacklist_manager.add(payload.get('jti'))
# 	except ValueError:
# 		raise CredentialsException()
#
#
# 	# Create new tokens
# 	access_token, refresh_token = pair_token_manager.obtain_token_pair(sub=payload["sub"])
#
# 	# Renew 'refresh_token' in cookie
# 	response.delete_cookie(key="refresh_token")
# 	pair_token_manager.set_refresh_token_cookie(response, refresh_token)
#
# 	# Return new 'access_token' in response body
# 	return TokenReadSchema(access_token=access_token, token_type="bearer")


# @user_router.get(
# 	"/me",
# 	# response_model=UserReadSchema,
# 	responses={
# 		401: ExceptionDocFactory.from_multiple_exceptions(
# 			(NotAuthenticatedException, CredentialsException),
# 			description='Authentication Errors'
# 		),
# 		403: ExceptionDocFactory.from_exception(InactiveUserException)
# 	},
# 	status_code=200
# )
# async def read_user_me(
# 		access_token_manager: JWTAccessManager = Depends(get_access_token_manager),
# 		db: AsyncSession = Depends(get_async_session),
# ):
# 	""" Returns current user information """
#
# 	try:
# 		user_id = await access_token_manager.get_user_id('access_token')
# 	except ExpiredSignatureError:
# 		pass
# 	except ValueError:
# 		raise NotAuthenticatedException()
#
# 	stmt = (
# 		select(
# 			User.email,
# 			User.first_name,
# 			User.last_name,
# 			User.is_active,
# 			User.created_at,
# 		)
# 		.where(User.id == user_id)
# 	)
# 	result = await db.execute(stmt)
# 	current_user = result.first()
# 	return UserReadSchema.model_validate(current_user)
