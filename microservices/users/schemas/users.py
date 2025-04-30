import re
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, EmailStr, HttpUrl

from models import RoleEnum

class UserBase(BaseModel):
	username: str
	email: EmailStr

	model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
	""" Validates input from api to create user """

	password: str

	@field_validator('username')
	def username_validator(cls, value):
		if len(value) < 4:
			raise ValueError('Username must be at least 4 characters')

		if not re.match(r'^[a-zA-Z0-9-_]+$', value):
			raise ValueError('Username can only contain letters, '
							 'numbers, hyphens, and underscores.')

		if not value[0].isalpha():
			raise ValueError('Username must start with a letter.')

		return value

	@field_validator('password')
	def password_validator(cls, value):
		if len(value) < 8:
			raise ValueError('Password must be at least 8 characters')

		return value


class UserRead(BaseModel):
	id: UUID
	username: str
	email: EmailStr
	avatar: Optional[HttpUrl]
	role: RoleEnum
	is_active: bool
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
	""" Validates data before creating a user instance """
	hashed_password: str
	role: RoleEnum
	is_active: bool


class UserFull(UserInDB):
	id: UUID
	created_at: datetime
