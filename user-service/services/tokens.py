import uuid
from abc import abstractmethod, ABC
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from core import settings


class BaseTokenEncoder(ABC):

	@abstractmethod
	def encode_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
		pass


class BaseTokenDecoder(ABC):

	@abstractmethod
	def decode_token(self, token: str) -> dict:
		pass


class JWTTokenMixin:
	ALLOWED_TOKEN_TYPES = ['access', 'refresh']
	JWT_TOKEN_SECRET_KEY = settings.JWT_TOKEN_SECRET_KEY
	JWT_TOKEN_ALGORITHM = settings.JWT_TOKEN_ALGORITHM


class JWTTokenEncoder(BaseTokenEncoder, JWTTokenMixin):
	ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
	REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

	def encode_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
		""" Creates JWT token """

		token_type = data.get('type')
		if token_type not in self.ALLOWED_TOKEN_TYPES:
			raise ValueError(
				f"Invalid token type: {token_type}. Allowed types are: {', '.join(self.ALLOWED_TOKEN_TYPES)}")

		to_encode = data.copy()

		if expires_delta:
			expire = datetime.now(timezone.utc) + expires_delta
		elif not expires_delta and token_type == 'refresh':
			expire = datetime.now(timezone.utc) + timedelta(minutes=60 * 24 * 7) # default 7 days
		else:
			expire = datetime.now(timezone.utc) + timedelta(minutes=15) # default 15 min

		to_encode.update({"exp": expire})

		if token_type == 'refresh':
			to_encode["jti"] = str(uuid.uuid4())

		encoded_jwt = jwt.encode(
			to_encode,
			self.JWT_TOKEN_SECRET_KEY,
			algorithm=self.JWT_TOKEN_ALGORITHM,
		)

		return encoded_jwt

	def obtain_token_pair(self, sub: str) -> tuple[str, str]:
		""" Creates and returns access and refresh JWT tokens. """

		# Create 'access_token'
		access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
		access_token = self.encode_token(
			data={"sub": sub, "type": "access"}, expires_delta=access_token_expires
		)
		# Create 'refresh_token'
		refresh_token_expires_minutes = 60 * 24 * self.REFRESH_TOKEN_EXPIRE_DAYS
		refresh_token_expires = timedelta(minutes=refresh_token_expires_minutes)
		refresh_token = self.encode_token(
			data={"sub": sub, "type": "refresh"}, expires_delta=refresh_token_expires
		)

		return access_token, refresh_token


class JWTTokenDecoder(JWTTokenMixin):

	def decode_token(self, token: str) -> dict:
		""" Decodes JWT token. If expired, raises exception """

		return jwt.decode( # decode exception raises if expired
			token,
			self.JWT_TOKEN_SECRET_KEY,
			algorithms=[self.JWT_TOKEN_ALGORITHM]
		)


class JWTTokenVerifier(JWTTokenDecoder):

	def verify_token(self, token: str) -> dict:
		payload = self.decode_token(token)



class JWTTokenBlacklist:
	pass