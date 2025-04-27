from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, EmailStr


class UserBase(BaseModel):
	email: EmailStr
	first_name: str
	last_name: str

	model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
	""" Validates input from api to create user """

	password: str

	@field_validator('password')
	def password_validator(cls, value):
		if len(value) < 8:
			raise ValueError('Password must be at least 8 characters')

		return value


class UserRead(UserBase):
	role: str
	is_active: bool
	created_at: datetime


class UserInDB(UserBase):
	""" Validates data before creating a user instance """
	hashed_password: str
	is_active: bool
	role: str


class UserFull(UserInDB):
	id: UUID
	created_at: datetime
