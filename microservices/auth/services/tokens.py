import uuid
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt import PyJWTError, ExpiredSignatureError
from fastapi import Response
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from config import settings
from exceptions.exceptions import JWTTokenValidationException, DuplicateJTIException
from core.loggers import log
from models import TokenBlacklist

TokenPair = namedtuple("TokenPair", ["access_token", "refresh_token"])


class JWTTokenService:
	ALLOWED_TOKEN_TYPES = ['access_token', 'refresh_token']
	JWT_TOKEN_SECRET_KEY = settings.JWT_TOKEN_SECRET_KEY
	JWT_TOKEN_ALGORITHM = settings.JWT_TOKEN_ALGORITHM
	ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
	REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

	def __init__(
			self,
			db: AsyncSession,
			access_token: str | None = None,
			refresh_token: str | None = None,
	):
		self.db = db
		self._access_token = access_token
		self._refresh_token = refresh_token

	@property
	def access_token(self) -> str | None:
		return self._access_token

	@access_token.setter
	def access_token(self, access_token: str) -> None:
		if self._access_token is None:
			self._access_token = access_token

	@property
	def refresh_token(self) -> str | None:
		return self._access_token

	@refresh_token.setter
	def refresh_token(self, refresh_token: str) -> None:
		if self._refresh_token is None:
			self._refresh_token = refresh_token

	def encode_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
		""" Creates JWT token """

		token_type = data.get('type')
		if token_type not in self.ALLOWED_TOKEN_TYPES:
			raise ValueError(
				f"Invalid token type: {token_type}. Allowed types are: "
				f"{', '.join(self.ALLOWED_TOKEN_TYPES)}"
			)

		to_encode = data.copy()

		expire = datetime.now(timezone.utc) + expires_delta
		if not expires_delta:
			if token_type == 'refresh_token':
				expire = datetime.now(timezone.utc) + timedelta(minutes=60 * 24 * 7)  # default 7 days
			else:
				expire = datetime.now(timezone.utc) + timedelta(minutes=15)  # default 15 min

		to_encode.update({"exp": expire})

		if token_type == 'refresh_token':
			to_encode["jti"] = str(uuid.uuid4())

		encoded_jwt = jwt.encode(
			to_encode,
			self.JWT_TOKEN_SECRET_KEY,
			algorithm=self.JWT_TOKEN_ALGORITHM,
		)

		return encoded_jwt

	def decode_token(self, token_type: str) -> dict:
		""" Decodes JWT token. If expired, raises exception """

		if not token_type in self.ALLOWED_TOKEN_TYPES:
			log.warning(f'{token_type} is not a valid token')
			raise ValueError("Token is invalid")

		token = getattr(self, '_' + token_type)

		if not token:
			log.warning(f'No token provided for type {token_type}')
			raise ValueError("Token is invalid")

		try:
			return jwt.decode(  # decode exception raises if expired
				token,
				self.JWT_TOKEN_SECRET_KEY,
				algorithms=[self.JWT_TOKEN_ALGORITHM]
			)
		except ExpiredSignatureError:
			log.warning(f'Token has expired')
			raise ExpiredSignatureError("Token has expired")
		except PyJWTError as e:
			log.warning(f"Token can't be decoded, PyJWTError: {e}")
			raise JWTTokenValidationException("Token is invalid")

	def obtain_token_pair(self, sub: str) -> TokenPair:
		""" Creates and returns access and refresh JWT tokens. """

		# Create 'access_token'
		access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
		access_token = self.encode_token(
			data={"sub": sub, "type": "access_token"}, expires_delta=access_token_expires
		)
		# Create 'refresh_token'
		refresh_token_expires_minutes = 60 * 24 * self.REFRESH_TOKEN_EXPIRE_DAYS
		refresh_token_expires = timedelta(minutes=refresh_token_expires_minutes)
		refresh_token = self.encode_token(
			data={"sub": sub, "type": "refresh_token"}, expires_delta=refresh_token_expires
		)
		return TokenPair(access_token=access_token, refresh_token=refresh_token)

	async def decode_and_validate_token(
			self,
			token_type: str,
			validate_jti: bool = True
	) -> dict:
		"""
		Decodes and validates token's payload.

		:return: payload
		"""

		# 1: Decode
		#    Tokens are instance attrs, chooses which one to validate
		payload = self.decode_token(token_type)

		# 2: Validate token type
		token_type = payload.get("type")
		if not token_type or token_type not in self.ALLOWED_TOKEN_TYPES:
			log.warning(f'{token_type} is not a valid token')
			raise JWTTokenValidationException("Token is invalid")

		# 3: Additional check for refresh token only
		if token_type == 'refresh' and validate_jti:

			# 3.1: Validate 'jti'
			jti_str = payload.get("jti")
			if not jti_str:
				log.warning('"jti" is missing')
				raise JWTTokenValidationException("Token is invalid")

			# 3.2 Check if token is blacklisted 'jti'
			try:
				jti = uuid.UUID(jti_str)
			except ValueError:
				log.warning('"jti" is invalid')
				raise JWTTokenValidationException("Token is invalid")

			# stmt = select(TokenBlacklist).where(TokenBlacklist.jti == jti)
			# result = await self.db.execute(stmt)
			# jti_in_db = result.scalar_one_or_none()
			# if jti_in_db:
			# 	log.warning('Token is blacklisted')
			# 	raise DuplicateJTIException("Token is invalid")

		# 4: Validate 'sub'
		user_id_str = payload.get("sub")
		if not user_id_str:
			log.warning('"sub" is missing')
			raise JWTTokenValidationException("Token is invalid")

		try:
			user_id = uuid.UUID(user_id_str)
		except ValueError:
			log.warning('"user_id" is invalid')
			raise JWTTokenValidationException("Token is invalid")

		return payload

	async def get_user_id(
			self,
			token_type: str
	) -> uuid.UUID:
		""" Extracts user from token and returns UserFullSchema """

		payload = await self.decode_and_validate_token(token_type)
		user_id = payload.get('sub')

		if token_type != payload.get('type'):
			log.warning(f'Token type is invalid: {token_type}')
			raise ValueError("Token is invalid")

		return user_id

	@staticmethod
	def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
		""" Sets 'refresh_token' in cookies. """

		max_age = 60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS
		response.set_cookie(
			key="refresh_token",
			value=refresh_token,
			httponly=True,
			# secure=True,
			samesite="strict",
			path="/",
			max_age=max_age,
		)


class TokenBlacklistService:
	def __init__(self, db: AsyncSession):
		self.db = db

	async def add(self, jti: uuid.UUID) -> None:
		"""Adds the token JTI to the blacklist."""
		try:
			stmt = insert(TokenBlacklist).values(jti=jti, created_at=datetime.now(timezone.utc))
			await self.db.execute(stmt)
			await self.db.commit()
		except IntegrityError:
			await self.db.rollback()
			log.warning("Can't add jti because it already exists")
			raise DuplicateJTIException("Can't add jti because it already exists")

	async def is_blacklisted(self, jti: uuid.UUID) -> bool:
		"""Checks if the token JTI is blacklisted."""
		stmt = select(TokenBlacklist).where(TokenBlacklist.jti == jti)
		result = await self.db.execute(stmt)
		return result.scalar_one_or_none() is not None

	async def clear_expired(self, before: datetime) -> None:
		"""
		Optional: Clears tokens added before a certain date.
		Can be used as a cleanup operation if needed.
		"""
		stmt = delete(TokenBlacklist).where(TokenBlacklist.created_at < before)
		await self.db.execute(stmt)
		await self.db.commit()
