from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer

import schemas
from core.exceptions import ExceptionDocFactory
from core.loggers import log
from core.exceptions.http import NotFoundHTTPException, BadRequestHTTPException, \
	CredentialsHTTPException, TooManyRequestsHTTPException
from dependencies import get_register_service, get_forgot_password_service, get_user_me_service, \
	get_password_confirmation_cache_service
from exceptions import DuplicateEmailException
from exceptions.exceptions import TooManyRequestsException
from exceptions.http import EmailExistsHTTPException

from dependencies.passwords import get_temp
from services.passwords import Temp
from services import RegisterService, ForgotPasswordService, UserMeService, PasswordConfirmationCacheService

auth_scheme = HTTPBearer()
users_router = APIRouter(prefix='/api/v1/users', tags=['users'])


@users_router.post(
	'/register',
	response_model=schemas.UserRead,
	responses={400: ExceptionDocFactory.from_exception(EmailExistsHTTPException)},
	status_code=201
)
async def register(
		request: Request,
		# user_data: schemas.UserCreate,
		# register_service: RegisterService = Depends(get_register_service),
):
	identifier = request.client.host
	log.info(f" *** identifier: {identifier}")
	# try:
	# 	user = await register_service.create_user(
	# 		user_data=user_data,
	# 		is_active=True,
	# 		role='user'
	# 	)
	# 	return schemas.UserRead.model_validate(user)
	# except DuplicateEmailException:
	# 	raise EmailExistsHTTPException()


@users_router.get(
	'/me',
	response_model=schemas.UserRead,
	responses={
		400: ExceptionDocFactory.from_exception(BadRequestHTTPException),
		401: ExceptionDocFactory.from_exception(CredentialsHTTPException),
		404: ExceptionDocFactory.from_exception(NotFoundHTTPException),
	},
	dependencies=[Depends(auth_scheme)]
)
async def me(
		request: Request,
		user_me_service: UserMeService = Depends(get_user_me_service)
):
	user_id = request.headers.get('X-User-Id', None)
	if not user_id:
		log.warning("/me * Missing 'X-User-Id' header")
		raise BadRequestHTTPException()

	user = await user_me_service.retrieve(user_id)
	if not user:
		log.warning('/me * User not found')
		raise NotFoundHTTPException()

	return schemas.UserRead.model_validate(user)


@users_router.post('/forgot-password')
async def forgot_password(
		data: schemas.ForgotPassword,
		forgot_password_service: ForgotPasswordService = \
				Depends(get_forgot_password_service),
		pwd_conf_cache_service: PasswordConfirmationCacheService = \
				Depends(get_password_confirmation_cache_service),
		temp: Temp = Depends(get_temp),
):
	email = data.email
	user = await forgot_password_service.retrieve(email)
	try:
		await pwd_conf_cache_service.handle_cache_confirmation(str(user.id))
		reset_id = await pwd_conf_cache_service.get_confirmation_token()
	except TooManyRequestsException:
		log.info(f"User: {str(user.id)} exceeded limit of password reset")
		raise TooManyRequestsHTTPException()

	await temp.create_task(d={'reset_id': reset_id})


@users_router.post('/reset-password/{reset_id}')
async def reset_password(
		data: schemas.ResetPassword,
):
	# extract 'user_id' from cache using 'reset_id'
	# get new password
	# update user with new password
	pass
