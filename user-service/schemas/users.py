from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, EmailStr


class UserBaseSchema(BaseModel):
	email: EmailStr
	first_name: str
	last_name: str

	model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(UserBaseSchema):
	""" Validates input from api to create user """

	password: str

	@field_validator('password')
	def password_validator(cls, value):
		if len(value) < 8:
			raise ValueError('Password must be at least 8 characters')

		return value


class UserReadSchema(UserBaseSchema):
	is_active: bool
	created_at: datetime


class UserInDBSchema(UserBaseSchema):
	""" Validates data before creating a user instance """
	hashed_password: str
	is_active: bool
	is_admin: bool


class UserFullSchema(UserInDBSchema):
	id: UUID
	created_at: datetime
