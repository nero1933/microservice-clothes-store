from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer

import schemas
from core.exceptions import ExceptionDocFactory
from core.loggers import log
from core.exceptions.http import NotFoundHTTPException, BadRequestHTTPException, \
	CredentialsHTTPException
from dependencies import get_register_service
from dependencies.users import get_user_me_service
from exceptions.http import EmailExistsHTTPException
from exceptions.exceptions import DuplicateEmailException
from services import RegisterService
from services.users import UserMeService

auth_scheme = HTTPBearer()
users_router = APIRouter(prefix='/api/v1/users', tags=['users'])


@users_router.post(
	'/register',
	response_model=schemas.UserRead,
	responses={400: ExceptionDocFactory.from_exception(EmailExistsHTTPException)},
	status_code=201
)
async def register(
		user_data: schemas.UserCreate,
		register_service: RegisterService = Depends(get_register_service),
):
	try:
		user = await register_service.create_user(
			user_data=user_data,
			is_active=True,
			role='user'
		)
		return schemas.UserRead.model_validate(user)
	except DuplicateEmailException:
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
		log.warning("/me Missing 'X-User-Id' header")
		raise BadRequestHTTPException()

	user = await user_me_service.retrieve(user_id)
	if not user:
		log.warning('/me User not found')
		raise NotFoundHTTPException()

	return schemas.UserRead.model_validate(user)


@users_router.post('/forgot-password')
async def forgot_password():
	pass


@users_router.post('/reset-password/{reset_id}')
async def reset_password():
	pass
