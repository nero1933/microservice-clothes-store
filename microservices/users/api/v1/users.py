import json

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPBearer

import schemas
from core.exceptions import ExceptionDocFactory
from core.loggers import log
from core.exceptions.http import NotFoundHTTPException, BadRequestHTTPException, \
	CredentialsHTTPException, TooManyRequestsHTTPException
from crud import UserByEmailRetriever, UserResetPasswordCRUD
from dependencies import get_register_service, get_user_me_service, get_reset_password_email_client, \
	get_user_by_email_crud, get_user_reset_password_crud, get_pwd_set_conf_cache_service, \
	get_pwd_get_conf_cache_service
from exceptions import DuplicateEmailException, TooManyRequestsException, \
	OperationCacheException, UserNotFoundException, PasswordUnchangedException, \
	ValidationConfirmationCacheException, CacheException, ExceedLimitConfirmationCacheException
from exceptions.http import EmailExistsHTTPException, ResetPasswordHTTPException
from messaging.clients import ResetPasswordEmailClient
from services import RegisterService, UserMeService, PasswordSetConfirmationCacheService, \
	PasswordGetConfirmationCacheService

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
		pwd_set_conf_cache_service: PasswordSetConfirmationCacheService = \
				Depends(get_pwd_set_conf_cache_service),
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
			await pwd_set_conf_cache_service.handle_cache_confirmation(str(user.id))
			reset_id = await pwd_set_conf_cache_service.get_confirmation_token()
		except ExceedLimitConfirmationCacheException:
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


@users_router.post('/reset-password/{reset_id}', status_code=204)
async def reset_password(
		reset_id: str,
		data: schemas.ResetPassword,
		user_reset_pwd_crud: UserResetPasswordCRUD = \
				Depends(get_user_reset_password_crud),
		pwd_get_conf_cache_service: PasswordGetConfirmationCacheService = \
				Depends(get_pwd_get_conf_cache_service),
):
	try:
		if not await pwd_get_conf_cache_service.validate_confirmation(reset_id):
			raise ValidationConfirmationCacheException()

		user_id = await pwd_get_conf_cache_service.get_user_id_from_cache(reset_id)
	except OperationCacheException as e:
		log.warning(
			f"/reset-password/{{reset_id}} * "
			f"Password reset error (OperationCacheException): {e}"
		)
		raise BadRequestHTTPException()
	except CacheException as e:
		log.info(f"/reset-password/{{reset_id}} * Password reset error: {e}")
		raise BadRequestHTTPException()

	try:
		await user_reset_pwd_crud.reset_password(
			user_id,
			data.password,
		)
	except UserNotFoundException as e:
		log.info(f"/reset-password/{{reset_id}} * User not found: {e}")
		raise NotFoundHTTPException()
	except PasswordUnchangedException as e:
		log.info(f"/reset-password/{{reset_id}} * New password matches old one: {e}")
		raise ResetPasswordHTTPException()

	return Response(status_code=204)
