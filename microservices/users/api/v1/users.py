import json

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPBearer

import schemas
from core.exceptions import ExceptionDocFactory
from core.loggers import log
from core.exceptions.http import NotFoundHTTPException, BadRequestHTTPException, \
	CredentialsHTTPException, TooManyRequestsHTTPException
from crud import UserByEmailRetriever
from dependencies import get_register_service, get_user_me_service
from dependencies.clients import get_reset_password_email_client
from dependencies.crud import get_user_by_email_crud
from dependencies.services import get_pwd_conf_cache_service
from exceptions import DuplicateEmailException
from exceptions.exceptions import TooManyRequestsException
from exceptions.http import EmailExistsHTTPException
from messaging.clients import ResetPasswordEmailClient
from services import RegisterService, UserMeService, PasswordConfirmationCacheService

auth_scheme = HTTPBearer()
users_router = APIRouter(prefix='/api/v1/users', tags=['users'])


@users_router.post(
	'/register',
	# response_model=schemas.UserRead,
	responses={400: ExceptionDocFactory.from_exception(EmailExistsHTTPException)},
	status_code=201
)
async def register(
		request: Request,
		user_data: schemas.UserCreate,
		register_service: RegisterService = Depends(get_register_service),
):
	ip = request.headers.get("X-Real-IP")
	log.info(f" *** identifier: {ip}")
	try:
		user = await register_service.create_user(
			user_data=user_data,
			is_active=True,
			role='user'
		)
		return schemas.UserRead.model_validate(user)
	except DuplicateEmailException:
		log.warning(f"/register * <{user_data.email}> already exists")
		raise EmailExistsHTTPException()


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
		pwd_conf_cache_service: PasswordConfirmationCacheService = \
				Depends(get_pwd_conf_cache_service),
		user_by_email_crud: UserByEmailRetriever = \
				Depends(get_user_by_email_crud),
		reset_password_email_client: ResetPasswordEmailClient = \
				Depends(get_reset_password_email_client),
):
	email = data.email
	user = await user_by_email_crud.retrieve(email)
	log.info(f'/forgot-password * {"User found" if user else "User not found"}')
	if user:
		try:
			# TEMP
			cache = await pwd_conf_cache_service.get_connection()
			await cache.flushdb()
			# TEMP

			await pwd_conf_cache_service.handle_cache_confirmation(str(user.id))
			reset_id = await pwd_conf_cache_service.get_confirmation_token()
		except TooManyRequestsException:
			log.info(f"User: {str(user.id)} exceeded limit of password reset")
			raise TooManyRequestsHTTPException()

		await reset_password_email_client.create_task(
			data={
				'email': email,
				'reset_id': reset_id
			},
		)

	return Response(
		content=json.dumps({"message": "Check your email for proceeding password reset"}),
		media_type="application/json",
		status_code=200
	)


@users_router.post('/reset-password/{reset_id}')
async def reset_password(
		reset_id: str,
		data: schemas.ResetPassword,
):

	return {'message': {reset_id}}
	# extract 'user_id' from cache using 'reset_id'
	# get new password
	# update user with new password
	pass
