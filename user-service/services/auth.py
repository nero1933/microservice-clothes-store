# import uuid
# from functools import wraps
#
# import jwt
# from datetime import datetime, timezone, timedelta
# from typing import Annotated, Optional
#
# from fastapi import Depends, status, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer
# from jwt.exceptions import PyJWTError
# from sqlalchemy.dialects.postgresql import insert
#
# from sqlalchemy.future import select
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from core import settings
# from dependencies.db import get_async_session
# from models.tokens import TokenBlacklist
# from schemas import UserFullSchema
# from models.users import User
# from utils import password as p
# from exceptions.custom_exceptions import CredentialsException, InactiveUserException
#
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
#
#
# async def get_user(user_data: dict[str: str], db: AsyncSession) -> Optional[UserFullSchema]:
# 	"""
# 	Retrieves a user from the database.
#
# 	:param user_data: dict with only one k, v pair, example -> {id: some_uuid}
# 	:param db: AsyncSession
# 	:return: UserFullSchema or None
# 	"""
#
# 	if not isinstance(user_data, dict) or len(user_data) != 1:
# 		raise ValueError("'user_data' must be a dict with only one field.")
#
# 	field_name = next(iter(user_data))
# 	field_value = user_data[field_name]
#
# 	stmt = select(User).where(getattr(User, field_name) == field_value)
# 	result = await db.execute(stmt)
# 	user = result.scalar_one_or_none()
# 	return UserFullSchema.model_validate(user) if user else None
#
#
# async def authenticate_user(
# 		email: str,
# 		password: str,
# 		db: AsyncSession
# ) -> Optional[UserFullSchema]:
# 	""" Authenticate user """
#
# 	user = await get_user({'email': email}, db)
# 	if not user:
# 		return None
#
# 	if not p.verify_password(password, user.hashed_password):
# 		return None
#
# 	return user
#
#
# def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
# 	""" Creates JWT token """
#
# 	to_encode = data.copy()
#
# 	if expires_delta:
# 		expire = datetime.now(timezone.utc) + expires_delta
# 	elif not expires_delta and data.get('type') == 'refresh':
# 		expire = datetime.now(timezone.utc) + timedelta(minutes=60 * 24 * 7)  # default 7 days
# 	else:
# 		expire = datetime.now(timezone.utc) + timedelta(minutes=15)  # default 15 min
#
# 	to_encode.update({"exp": expire})
# 	to_encode["jti"] = str(uuid.uuid4())
# 	encoded_jwt = jwt.encode(
# 		to_encode,
# 		settings.JWT_TOKEN_SECRET_KEY,
# 		algorithm=settings.JWT_TOKEN_ALGORITHM
# 	)
# 	return encoded_jwt
#
#
# def obtain_token_pair(sub: str) -> tuple[str, str]:
# 	""" Creates and returns access and refresh JWT tokens. """
#
# 	# Create 'access_token'
# 	access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
# 	access_token = create_jwt_token(
# 		data={"sub": sub, "type": "access"}, expires_delta=access_token_expires
# 	)
# 	# Create 'refresh_token'
# 	refresh_token_expires_minutes = 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS
# 	refresh_token_expires = timedelta(minutes=refresh_token_expires_minutes)
# 	refresh_token = create_jwt_token(
# 		data={"sub": sub, "type": "refresh"}, expires_delta=refresh_token_expires
# 	)
#
# 	return access_token, refresh_token
#
#
# async def decode_and_validate_token(
# 		token: str,
# 		token_type: str,
# 		db: AsyncSession,
# ) -> dict:
# 	"""
# 	Decodes and validates token's payload.
#
# 	:return: payload
# 	"""
#
# 	# Decode token
# 	try:
# 		payload = jwt.decode(
# 			token,
# 			settings.JWT_TOKEN_SECRET_KEY,
# 			algorithms=[settings.JWT_TOKEN_ALGORITHM]
# 		)
# 	except PyJWTError:
# 		raise CredentialsException()
#
# 	jti_str = payload.get("jti")
# 	if not jti_str:
# 		raise CredentialsException()
#
# 	try:
# 		jti = uuid.UUID(jti_str)
# 	except ValueError:
# 		raise CredentialsException()
#
# 	stmt = select(BlacklistedToken).where(BlacklistedToken.jti == jti)
# 	result = await db.execute(stmt)
# 	jti_in_db = result.scalar_one_or_none()
#
# 	if jti_in_db:
# 		raise CredentialsException()
#
# 	try:
# 		user_id = uuid.UUID(payload.get("sub"))
# 		if not user_id:
# 			raise CredentialsException()
# 	except (ValueError, TypeError):
# 		raise CredentialsException()
#
# 	# Validate token type
# 	if payload.get("type") != token_type:
# 		raise CredentialsException()
#
# 	return payload
#
#
# async def get_user_from_token(token: str, token_type: str, db: AsyncSession) -> UserFullSchema:
# 	""" Extracts user from token and returns UserFullSchema """
#
# 	payload = await decode_and_validate_token(token, token_type, db)
# 	user_id = payload['sub']
# 	user = await get_user({'id': user_id}, db)
# 	if not user:
# 		raise CredentialsException()
#
# 	return user
#
#
# async def blacklist_jwt_token(
# 		db: Annotated[AsyncSession, Depends(get_async_session)],
# 		access_token: Optional[str],
# 		refresh_token: Optional[str],
# ) -> None:
# 	""" Blacklists JWT Tokens. """
#
# 	blacklisted_tokens = []
#
# 	for token in (access_token, refresh_token):
# 		if not token:
# 			continue
#
# 		try:
# 			payload = jwt.decode(
# 				token,
# 				settings.JWT_TOKEN_SECRET_KEY,
# 				algorithms=[settings.JWT_TOKEN_ALGORITHM]
# 			)
# 			jti_str = payload.get("jti")
# 			if not jti_str:
# 				continue
#
# 			jti = uuid.UUID(jti_str)
#
# 		except (PyJWTError, ValueError, TypeError):
# 			continue
#
# 		blacklisted_tokens.append({'jti': jti})
#
# 	if blacklisted_tokens:
# 		stmt = insert(BlacklistedToken).values(blacklisted_tokens)
# 		stmt = stmt.on_conflict_do_nothing(index_elements=["jti"])
# 		await db.execute(stmt)
# 		await db.commit()
#
#
# def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
# 	""" Sets 'refresh_token' in cookies. """
#
# 	max_age = 60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS
# 	response.set_cookie(
# 		key="refresh_token",
# 		value=refresh_token,
# 		httponly=True,
# 		# secure=True,
# 		samesite="strict",
# 		path="/",
# 		max_age=max_age,
# 	)
#
#
# async def get_current_user(
# 		access_token: Annotated[str, Depends(oauth2_scheme)],
# 		db: Annotated[AsyncSession, Depends(get_async_session)]
# ) -> UserFullSchema:
# 	""" Retrieves current user. """
#
# 	return await get_user_from_token(access_token, token_type='access', db=db)
#
#
# async def get_current_active_user(
# 		current_user: Annotated[UserFullSchema, Depends(get_current_user)],
# ) -> UserFullSchema:
# 	""" Retrieves current user if user is active. """
#
# 	if not current_user.is_active:
# 		raise InactiveUserException()
#
# 	return current_user
#
#
# def require_user_field(field_name: str):
# 	""" Use to check if 'is_admin', 'is_active'... is True. """
#
# 	def decorator(func):
# 		@wraps(func)
# 		async def wrapper(current_user: UserFullSchema, *args, **kwargs):
# 			if not getattr(current_user, field_name, True):
# 				raise HTTPException(
# 					status_code=status.HTTP_403_FORBIDDEN,
# 					detail=f"User is not {field_name}."
# 				)
#
# 			return await func(current_user, *args, **kwargs)
#
# 		return wrapper
#
# 	return decorator
