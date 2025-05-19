from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, EmailStr

from models import RoleEnum

class UserBase(BaseModel):
	email: EmailStr

	model_config = ConfigDict(from_attributes=True)


class UserPassword(BaseModel):
	""" Validates input from api to create user """

	password: str

	@field_validator('password')
	def password_validator(cls, value):
		if len(value) < 8:
			raise ValueError('Password must be at least 8 characters')

		if value != value.strip():
			raise ValueError('Password must not start or end with spaces')

		return value


class UserCreate(UserBase, UserPassword):
	""" Validates input from api to create user """
	pass


class UserRead(BaseModel):
	id: UUID
	email: EmailStr
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


# class UserResetPassword(BaseModel):
# 	hashed_password: str
